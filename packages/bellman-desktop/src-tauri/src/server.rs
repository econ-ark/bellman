//! Start one installed Workbench server and retain ownership of its processes.

use std::ffi::OsString;
use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::net::{Ipv4Addr, SocketAddr, TcpListener, TcpStream};
use std::path::Path;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;
use std::time::{Duration, Instant};

const START_TIMEOUT: Duration = Duration::from_secs(90);
const POLL_INTERVAL: Duration = Duration::from_millis(75);
const LOG_LIMIT: u64 = 65_536;

/// The server belonging to one desktop window. Dropping it stops its processes.
pub struct Server {
    pub port: u16,
    process: platform::OwnedProcess,
}

impl Server {
    pub fn is_running(&mut self) -> bool {
        self.process.is_running()
    }
}

impl Drop for Server {
    fn drop(&mut self) {
        self.process.stop();
    }
}

/// Launch the installed command without a command interpreter or Python bundle.
pub fn start(
    command: &[String],
    folder: &Path,
    editor: &[String],
    log_path: &Path,
    cancel: &AtomicBool,
) -> Result<Server, String> {
    start_with_timeout(command, folder, editor, log_path, START_TIMEOUT, cancel)
}

fn start_with_timeout(
    command: &[String],
    folder: &Path,
    editor: &[String],
    log_path: &Path,
    timeout: Duration,
    cancel: &AtomicBool,
) -> Result<Server, String> {
    if cancel.load(Ordering::Acquire) {
        return Err("Workbench startup was cancelled.".into());
    }
    if command.first().is_none_or(|name| name.trim().is_empty()) {
        return Err("Choose the installed bellman-workbench command in Settings.".into());
    }
    if !folder.is_dir() {
        return Err(format!(
            "The model folder does not exist: {}",
            folder.display()
        ));
    }
    let mut options = OpenOptions::new();
    options.create(true).truncate(true).write(true);
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        options.mode(0o600);
    }
    let mut log = options.open(log_path).map_err(|error| {
        format!(
            "Cannot write the Workbench log {}: {error}",
            log_path.display()
        )
    })?;
    let environment = [
        ("BELLMAN_WORKBENCH_DESKTOP", "1".to_owned()),
        (
            "BELLMAN_WORKBENCH_EDITOR",
            if editor.is_empty() {
                String::new()
            } else {
                serde_json::to_string(editor).unwrap()
            },
        ),
        ("PYTHONUNBUFFERED", "1".to_owned()),
        ("NO_COLOR", "1".to_owned()),
    ];

    for attempt in 1..=3 {
        if cancel.load(Ordering::Acquire) {
            return Err("Workbench startup was cancelled.".into());
        }
        let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0))
            .map_err(|error| format!("Cannot choose a local server port: {error}"))?;
        let port = listener
            .local_addr()
            .map_err(|error| error.to_string())?
            .port();
        writeln!(log, "Workbench start {attempt}, loopback port {port}.")
            .map_err(|error| format!("Cannot write the Workbench log: {error}"))?;
        let offset = log.metadata().map_err(|error| error.to_string())?.len();
        let mut arguments: Vec<OsString> = command.iter().map(OsString::from).collect();
        arguments.extend([
            folder.as_os_str().to_owned(),
            "--host".into(),
            "127.0.0.1".into(),
            "--port".into(),
            port.to_string().into(),
            "--no-open".into(),
        ]);
        // The launcher's bind can lose this port. Its own success message is
        // required below, so an unrelated listener cannot satisfy readiness.
        drop(listener);
        let process =
            platform::OwnedProcess::spawn(&arguments, &environment, &log).map_err(|error| {
                format!(
                    "Cannot start {}: {error}. Install bellman-workbench in a Python environment, \
                     then choose its command in Settings. Log: {}",
                    command[0],
                    log_path.display()
                )
            })?;
        let mut server = Server { port, process };
        let deadline = Instant::now() + timeout;
        let marker = format!("Uvicorn running on http://127.0.0.1:{port} ");
        let mut bound = false;
        let failure = loop {
            if cancel.load(Ordering::Acquire) {
                return Err("Workbench startup was cancelled.".into());
            }
            let text = read_log(log_path, offset);
            bound |= text.contains(&marker);
            if !server.is_running() {
                break format!(
                    "Workbench stopped during startup ({})",
                    server.process.status()
                );
            }
            if bound && page_responds(port) && server.is_running() {
                if cancel.load(Ordering::Acquire) {
                    return Err("Workbench startup was cancelled.".into());
                }
                return Ok(server);
            }
            if Instant::now() >= deadline {
                break "Workbench did not finish starting within the allowed time".to_owned();
            }
            thread::sleep(POLL_INTERVAL.min(deadline.saturating_duration_since(Instant::now())));
        };
        drop(server);
        let text = read_log(log_path, offset);
        let lower = text.to_ascii_lowercase();
        if attempt < 3
            && (lower.contains("address already in use")
                || lower.contains("only one usage of each socket address"))
        {
            continue;
        }
        let tail: String = text
            .chars()
            .rev()
            .take(2_000)
            .collect::<String>()
            .chars()
            .rev()
            .collect();
        return Err(format!(
            "{failure}. Log: {}\n{}",
            log_path.display(),
            tail.trim()
        ));
    }
    unreachable!("the final startup attempt returns its result")
}

fn read_log(path: &Path, offset: u64) -> String {
    let Ok(mut file) = File::open(path) else {
        return String::new();
    };
    let length = file.metadata().map(|metadata| metadata.len()).unwrap_or(0);
    let _ = file.seek(SeekFrom::Start(
        offset.max(length.saturating_sub(LOG_LIMIT)),
    ));
    let mut bytes = Vec::new();
    let _ = file.take(LOG_LIMIT).read_to_end(&mut bytes);
    String::from_utf8_lossy(&bytes).into_owned()
}

fn page_responds(port: u16) -> bool {
    let address = SocketAddr::from((Ipv4Addr::LOCALHOST, port));
    let Ok(mut stream) = TcpStream::connect_timeout(&address, Duration::from_millis(200)) else {
        return false;
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(400)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(400)));
    if write!(
        stream,
        "GET / HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n\r\n"
    )
    .is_err()
    {
        return false;
    }
    let mut bytes = Vec::new();
    let mut chunk = [0; 4096];
    let deadline = Instant::now() + Duration::from_millis(750);
    while bytes.len() < 16_384 {
        let remaining = deadline.saturating_duration_since(Instant::now());
        if remaining.is_zero() {
            return false;
        }
        let _ = stream.set_read_timeout(Some(remaining.min(Duration::from_millis(400))));
        let Ok(length) = stream.read(&mut chunk) else {
            return false;
        };
        if length == 0 {
            return false;
        }
        bytes.extend_from_slice(&chunk[..length]);
        if let Some(end) = bytes.windows(4).position(|part| part == b"\r\n\r\n") {
            let headers = String::from_utf8_lossy(&bytes[..end]).to_ascii_lowercase();
            return (headers.starts_with("http/1.1 200 ") || headers.starts_with("http/1.0 200 "))
                && headers.contains("\r\ncontent-type: text/html");
        }
    }
    false
}

#[cfg(unix)]
mod platform {
    use super::*;
    use std::os::unix::process::CommandExt;
    use std::process::{Child, Command, Stdio};

    pub(super) struct OwnedProcess {
        child: Option<Child>,
        group: i32,
        status: String,
    }

    impl OwnedProcess {
        pub(super) fn spawn(
            arguments: &[OsString],
            environment: &[(&str, String)],
            log: &File,
        ) -> std::io::Result<Self> {
            let child = Command::new(&arguments[0])
                .args(&arguments[1..])
                .envs(environment.iter().map(|(key, value)| (*key, value)))
                .stdin(Stdio::null())
                .stdout(log.try_clone()?)
                .stderr(log.try_clone()?)
                .process_group(0)
                .spawn()?;
            let group = child.id() as i32;
            Ok(Self {
                child: Some(child),
                group,
                status: "running".into(),
            })
        }

        pub(super) fn is_running(&mut self) -> bool {
            let Some(child) = self.child.as_mut() else {
                return false;
            };
            match child.try_wait() {
                Ok(None) => true,
                Ok(Some(status)) => {
                    self.status = status.to_string();
                    false
                }
                Err(error) => {
                    self.status = error.to_string();
                    false
                }
            }
        }

        pub(super) fn status(&self) -> &str {
            &self.status
        }

        pub(super) fn stop(&mut self) {
            let Some(mut child) = self.child.take() else {
                return;
            };
            // The group was created for this child before its executable ran.
            unsafe {
                libc::kill(-self.group, libc::SIGTERM);
            }
            let deadline = Instant::now() + Duration::from_secs(2);
            loop {
                let _ = child.try_wait();
                let present = unsafe { libc::kill(-self.group, 0) == 0 };
                if !present || Instant::now() >= deadline {
                    break;
                }
                thread::sleep(Duration::from_millis(25));
            }
            unsafe {
                libc::kill(-self.group, libc::SIGKILL);
            }
            let _ = child.kill();
            let _ = child.wait();
        }
    }

    impl Drop for OwnedProcess {
        fn drop(&mut self) {
            self.stop();
        }
    }
}

#[cfg(windows)]
mod platform {
    use super::*;
    use std::io;
    use std::mem::size_of;
    use std::os::windows::ffi::OsStrExt;
    use std::os::windows::io::{AsRawHandle, FromRawHandle, OwnedHandle};
    use std::ptr::null;
    use std::sync::Mutex;
    use windows_sys::Win32::Foundation::{
        SetHandleInformation, HANDLE, HANDLE_FLAG_INHERIT, STILL_ACTIVE,
    };
    use windows_sys::Win32::System::JobObjects::{
        AssignProcessToJobObject, CreateJobObjectW, JobObjectExtendedLimitInformation,
        SetInformationJobObject, JOBOBJECT_EXTENDED_LIMIT_INFORMATION,
        JOB_OBJECT_LIMIT_BREAKAWAY_OK, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    };
    use windows_sys::Win32::System::Threading::{
        CreateProcessW, GetExitCodeProcess, ResumeThread, TerminateProcess, WaitForSingleObject,
        CREATE_NO_WINDOW, CREATE_SUSPENDED, CREATE_UNICODE_ENVIRONMENT, PROCESS_INFORMATION,
        STARTF_USESTDHANDLES, STARTUPINFOW,
    };

    pub(super) struct OwnedProcess {
        child: OwnedHandle,
        job: Option<OwnedHandle>,
        status: String,
    }

    static SPAWN_HANDLES: Mutex<()> = Mutex::new(());

    fn handle(value: &impl AsRawHandle) -> HANDLE {
        value.as_raw_handle() as HANDLE
    }

    impl OwnedProcess {
        pub(super) fn spawn(
            arguments: &[OsString],
            environment: &[(&str, String)],
            log: &File,
        ) -> io::Result<Self> {
            let raw_job = unsafe { CreateJobObjectW(null(), null()) };
            if raw_job.is_null() {
                return Err(io::Error::last_os_error());
            }
            let job = unsafe { OwnedHandle::from_raw_handle(raw_job) };
            let mut limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION::default();
            // The editor explicitly requests breakaway; the Python server does not.
            limits.BasicLimitInformation.LimitFlags =
                JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | JOB_OBJECT_LIMIT_BREAKAWAY_OK;
            if unsafe {
                SetInformationJobObject(
                    handle(&job),
                    JobObjectExtendedLimitInformation,
                    &limits as *const _ as _,
                    size_of::<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>() as u32,
                )
            } == 0
            {
                return Err(io::Error::last_os_error());
            }

            let mut command_line = windows_command_line(arguments)?;
            let mut variables: Vec<_> = std::env::vars_os().collect();
            for (key, value) in environment {
                variables.retain(|(name, _)| !name.to_string_lossy().eq_ignore_ascii_case(key));
                variables.push(((*key).into(), value.into()));
            }
            variables.sort_by_key(|(key, _)| key.to_string_lossy().to_uppercase());
            let mut block: Vec<u16> = Vec::new();
            for (key, value) in variables {
                block.extend(key.encode_wide());
                block.push(b'=' as u16);
                block.extend(value.encode_wide());
                block.push(0);
            }
            block.push(0);
            let input = File::open("NUL")?;
            let output = log.try_clone()?;
            // Concurrent server starts must not inherit each other's log handles.
            let inheritance = SPAWN_HANDLES
                .lock()
                .unwrap_or_else(|error| error.into_inner());
            for raw in [handle(&input), handle(&output)] {
                if unsafe { SetHandleInformation(raw, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT) }
                    == 0
                {
                    return Err(io::Error::last_os_error());
                }
            }
            let startup = STARTUPINFOW {
                cb: size_of::<STARTUPINFOW>() as u32,
                dwFlags: STARTF_USESTDHANDLES,
                hStdInput: handle(&input),
                hStdOutput: handle(&output),
                hStdError: handle(&output),
                ..Default::default()
            };
            let mut info = PROCESS_INFORMATION::default();
            // A suspended process cannot start descendants before assignment.
            let created = unsafe {
                CreateProcessW(
                    null(),
                    command_line.as_mut_ptr(),
                    null(),
                    null(),
                    1,
                    CREATE_SUSPENDED | CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT,
                    block.as_ptr() as _,
                    null(),
                    &startup,
                    &mut info,
                )
            };
            let error = io::Error::last_os_error();
            for raw in [handle(&input), handle(&output)] {
                unsafe {
                    SetHandleInformation(raw, HANDLE_FLAG_INHERIT, 0);
                }
            }
            drop(inheritance);
            if created == 0 {
                return Err(error);
            }
            let child = unsafe { OwnedHandle::from_raw_handle(info.hProcess) };
            let thread_handle = unsafe { OwnedHandle::from_raw_handle(info.hThread) };
            let owned = Self {
                child,
                job: Some(job),
                status: "running".into(),
            };
            if unsafe {
                AssignProcessToJobObject(handle(owned.job.as_ref().unwrap()), handle(&owned.child))
            } == 0
            {
                return Err(io::Error::last_os_error());
            }
            if unsafe { ResumeThread(handle(&thread_handle)) } == u32::MAX {
                return Err(io::Error::last_os_error());
            }
            Ok(owned)
        }

        pub(super) fn is_running(&mut self) -> bool {
            let mut code = 0;
            if unsafe { GetExitCodeProcess(handle(&self.child), &mut code) } == 0 {
                self.status = io::Error::last_os_error().to_string();
                return false;
            }
            self.status = format!("exit code {code}");
            code == STILL_ACTIVE as u32
        }

        pub(super) fn status(&self) -> &str {
            &self.status
        }

        pub(super) fn stop(&mut self) {
            if self.job.take().is_none() {
                return;
            }
            // TerminateProcess also covers an error before assignment to the job.
            unsafe {
                TerminateProcess(handle(&self.child), 1);
                WaitForSingleObject(handle(&self.child), 5_000);
            }
        }
    }

    impl Drop for OwnedProcess {
        fn drop(&mut self) {
            self.stop();
        }
    }

    fn windows_command_line(arguments: &[OsString]) -> io::Result<Vec<u16>> {
        let mut result = Vec::new();
        for (index, argument) in arguments.iter().enumerate() {
            if index != 0 {
                result.push(b' ' as u16);
            }
            result.push(b'"' as u16);
            let mut slashes = 0;
            for unit in argument.encode_wide() {
                if unit == 0 {
                    return Err(io::Error::new(
                        io::ErrorKind::InvalidInput,
                        "A command argument contains a null character",
                    ));
                }
                if unit == b'\\' as u16 {
                    slashes += 1;
                    continue;
                }
                let count = if unit == b'"' as u16 {
                    slashes * 2 + 1
                } else {
                    slashes
                };
                result.extend(std::iter::repeat_n(b'\\' as u16, count));
                slashes = 0;
                result.push(unit);
            }
            result.extend(std::iter::repeat_n(b'\\' as u16, slashes * 2));
            result.push(b'"' as u16);
        }
        result.push(0);
        Ok(result)
    }
}

#[cfg(all(test, unix))]
mod tests {
    use super::*;

    fn python(script: &str) -> Vec<String> {
        vec!["python3".into(), "-u".into(), "-c".into(), script.into()]
    }

    #[test]
    fn missing_command_names_the_executable_and_log() {
        let folder = tempfile::tempdir().unwrap();
        let log = folder.path().join("server.log");
        let result = start(
            &["/no/such/bellman-workbench".into()],
            folder.path(),
            &[],
            &log,
            &AtomicBool::new(false),
        );
        let error = result.err().unwrap();
        assert!(error.contains("/no/such/bellman-workbench"));
        assert!(error.contains(log.to_str().unwrap()));
    }

    #[test]
    fn readiness_requires_the_owned_servers_bind_message() {
        let folder = tempfile::tempdir().unwrap();
        let log = folder.path().join("server.log");
        let script = r#"
import http.server, sys
port = int(sys.argv[sys.argv.index('--port') + 1])
http.server.HTTPServer(('127.0.0.1', port), http.server.SimpleHTTPRequestHandler).serve_forever()
"#;
        let result = start_with_timeout(
            &python(script),
            folder.path(),
            &[],
            &log,
            Duration::from_millis(350),
            &AtomicBool::new(false),
        );
        assert!(result.err().unwrap().contains("did not finish starting"));
    }

    #[test]
    fn drop_stops_the_server_and_its_child() {
        let folder = tempfile::tempdir().unwrap();
        let log = folder.path().join("server.log");
        let script = r#"
import http.server, pathlib, signal, socket, subprocess, sys, time
folder = pathlib.Path(sys.argv[1])
port = int(sys.argv[sys.argv.index('--port') + 1])
child = subprocess.Popen([sys.executable, '-u', '-c', '''
import pathlib, signal, sys, time
signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
p = pathlib.Path(sys.argv[1])
while True:
    p.write_text(str(time.monotonic_ns()))
    time.sleep(.02)
''', str(folder / 'heartbeat')])
def stop(*args):
    child.wait(timeout=1)
    sys.exit(0)
signal.signal(signal.SIGTERM, stop)
server = http.server.HTTPServer(('127.0.0.1', port), http.server.SimpleHTTPRequestHandler)
print(f'Uvicorn running on http://127.0.0.1:{port} (Press CTRL+C to quit)', flush=True)
server.serve_forever()
"#;
        let mut server = start_with_timeout(
            &python(script),
            folder.path(),
            &[],
            &log,
            Duration::from_secs(5),
            &AtomicBool::new(false),
        )
        .unwrap();
        let port = server.port;
        assert!(server.is_running());
        let heartbeat = folder.path().join("heartbeat");
        let deadline = Instant::now() + Duration::from_secs(2);
        while !heartbeat.exists() && Instant::now() < deadline {
            thread::sleep(POLL_INTERVAL);
        }
        assert!(heartbeat.exists());
        drop(server);
        let after = std::fs::read_to_string(&heartbeat).unwrap();
        thread::sleep(Duration::from_millis(150));
        assert_eq!(after, std::fs::read_to_string(&heartbeat).unwrap());
        assert!(TcpStream::connect((Ipv4Addr::LOCALHOST, port)).is_err());
    }

    #[test]
    fn startup_timeout_stops_descendants() {
        let folder = tempfile::tempdir().unwrap();
        let log = folder.path().join("server.log");
        let script = r#"
import pathlib, signal, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-u', '-c', '''
import pathlib, sys, time
p = pathlib.Path(sys.argv[1])
while True:
    p.write_text(str(time.monotonic_ns()))
    time.sleep(.02)
''', str(pathlib.Path(sys.argv[1]) / 'heartbeat')])
def stop(*args):
    child.wait(timeout=1)
    sys.exit(0)
signal.signal(signal.SIGTERM, stop)
time.sleep(60)
"#;
        let result = start_with_timeout(
            &python(script),
            folder.path(),
            &[],
            &log,
            Duration::from_millis(500),
            &AtomicBool::new(false),
        );
        assert!(result.err().unwrap().contains("did not finish starting"));
        let heartbeat = folder.path().join("heartbeat");
        let after = std::fs::read_to_string(&heartbeat).unwrap();
        thread::sleep(Duration::from_millis(150));
        assert_eq!(after, std::fs::read_to_string(&heartbeat).unwrap());
    }

    #[test]
    fn cancellation_stops_a_process_that_has_not_become_ready() {
        let folder = tempfile::tempdir().unwrap();
        let log = folder.path().join("server.log");
        let pid_path = folder.path().join("pid");
        let cancel = AtomicBool::new(false);
        let script = r#"
import os, pathlib, sys, time
pathlib.Path(sys.argv[1], 'pid').write_text(str(os.getpid()))
time.sleep(60)
"#;
        let before = Instant::now();
        thread::scope(|scope| {
            scope.spawn(|| {
                let deadline = Instant::now() + Duration::from_secs(3);
                while !pid_path.exists() && Instant::now() < deadline {
                    thread::sleep(Duration::from_millis(10));
                }
                cancel.store(true, Ordering::Release);
            });
            let result = start(&python(script), folder.path(), &[], &log, &cancel);
            assert!(result.err().unwrap().contains("cancelled"));
        });
        assert!(before.elapsed() < Duration::from_secs(5));
        let pid: i32 = std::fs::read_to_string(pid_path).unwrap().parse().unwrap();
        assert_ne!(unsafe { libc::kill(pid, 0) }, 0);
    }
}
