#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod address;
mod recent;
mod server;
mod settings;

use address::OpenRequest;
use recent::RecentProjects;
use settings::Settings;
use std::{
    collections::HashMap,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicU64, AtomicUsize, Ordering},
        mpsc, Mutex,
    },
    time::Duration,
};
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder, SubmenuBuilder},
    webview::PageLoadEvent,
    window::Color,
    AppHandle, Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder,
};
use tauri_plugin_deep_link::DeepLinkExt;
use tauri_plugin_dialog::{DialogExt, MessageDialogButtons, MessageDialogKind};

// The Workbench background, --bl-chrome in brand.css.
const WINDOW_BACKGROUND: Color = Color(15, 27, 54, 255);

struct FolderWindow {
    folder: PathBuf,
    pending: OpenRequest,
    loaded: bool,
    request_serial: u64,
    server: Option<server::Server>,
}
struct Desktop {
    windows: Mutex<HashMap<String, FolderWindow>>,
    requests: mpsc::Sender<OpenRequest>,
    settings: Mutex<Settings>,
    settings_path: PathBuf,
    recent: Mutex<RecentProjects>,
    welcome_folders: Mutex<Vec<PathBuf>>,
    recent_path: PathBuf,
    logs: PathBuf,
    next: AtomicU64,
    active_starts: AtomicUsize,
    closing: Mutex<Vec<String>>,
    quitting: AtomicBool,
    exit_approved: AtomicBool,
}

// Count queued requests and launches until dispatch and process ownership are settled.
struct Starting(AppHandle);
impl Drop for Starting {
    fn drop(&mut self) {
        self.0
            .state::<Desktop>()
            .active_starts
            .fetch_sub(1, Ordering::SeqCst);
    }
}

fn welcome_status(app: &AppHandle, message: &str, busy: bool) {
    if let Some(window) = app.get_webview_window("welcome") {
        let message = serde_json::to_string(message).expect("serializable status");
        let _ = window.eval(format!(
            "window.bellmanWelcome?.setOpenStatus({message}, {busy});"
        ));
    }
}

fn finish_opening(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("welcome") {
        let _ = window.destroy();
    }
}

fn welcome_navigation_path(url: &url::Url) -> Option<&str> {
    // Tauri serves the bundled page with these platform-specific origins.
    let (scheme, host) = if cfg!(windows) {
        ("http", "tauri.localhost")
    } else {
        ("tauri", "localhost")
    };
    if url.scheme() != scheme
        || url.host_str() != Some(host)
        || url.port().is_some()
        || !url.username().is_empty()
        || url.password().is_some()
        || url.query().is_some_and(|query| !query.is_empty())
        || url.fragment().is_some()
    {
        return None;
    }
    match url.path() {
        "" | "/" | "/index.html" | "/open-project" | "/open-file" => Some(url.path()),
        path if recent_index(path).is_some() => Some(path),
        _ => None,
    }
}

fn recent_index(path: &str) -> Option<usize> {
    let index = path.strip_prefix("/recent/")?;
    if index.is_empty() || !index.bytes().all(|byte| byte.is_ascii_digit()) {
        return None;
    }
    index.parse().ok()
}

fn recent_request(folders: &[PathBuf], index: usize) -> Result<OpenRequest, String> {
    let folder = folders
        .get(index)
        .ok_or("The recent project is not in this list.")?;
    let request = OpenRequest::from_path(folder)?;
    if request.file.is_some() {
        return Err(format!(
            "The recent project is no longer a folder: {}",
            folder.display()
        ));
    }
    Ok(request)
}

fn show_error(app: &AppHandle, error: String) {
    welcome_status(app, &error, false);
    eprintln!("Bellman Workbench: {error}");
    app.dialog()
        .message(error)
        .title("Bellman Workbench")
        .kind(MessageDialogKind::Error)
        .show(|_| {});
}

fn deliver(window: &WebviewWindow, request: &OpenRequest) -> tauri::Result<()> {
    if request.file.is_none() {
        return Ok(());
    }
    let mut data = serde_json::to_value(request).expect("serializable location");
    data["folder"] = serde_json::to_value(&request.folder).expect("serializable folder");
    let data = data.to_string();
    window.eval(format!("(()=>{{const request={data};if(window.__bellmanOpenReady){{window.dispatchEvent(new CustomEvent('bellman-open',{{detail:request}}));}}else{{(window.__bellmanOpenQueue ||= []).push(request);}}}})()"))
}

fn open_request(app: &AppHandle, request: OpenRequest) {
    let state = app.state::<Desktop>();
    let mut windows = state.windows.lock().unwrap();
    if state.exit_approved.load(Ordering::SeqCst) {
        return;
    }
    if let Some(label) = matching_window(&windows, &request.folder) {
        windows.get_mut(&label).unwrap().request_serial += 1;
    }
    state.active_starts.fetch_add(1, Ordering::SeqCst);
    if state.requests.send(request).is_err() {
        state.active_starts.fetch_sub(1, Ordering::SeqCst);
    }
}

fn matching_window(windows: &HashMap<String, FolderWindow>, folder: &Path) -> Option<String> {
    windows
        .iter()
        .filter(|(_, entry)| entry.folder == folder)
        .map(|(label, _)| label)
        .min()
        .cloned()
}

fn record_folder(entry: &mut FolderWindow, folder: PathBuf) -> bool {
    if entry.folder == folder {
        return false;
    }
    entry.folder = folder.clone();
    entry.pending = OpenRequest {
        folder,
        file: None,
        line: 1,
        r#box: None,
    };
    entry.request_serial += 1;
    true
}

fn refresh_window_folders(app: &AppHandle) -> Result<(), String> {
    let labels: Vec<String> = app
        .state::<Desktop>()
        .windows
        .lock()
        .unwrap()
        .iter()
        .filter(|(_, entry)| entry.loaded)
        .map(|(label, _)| label.clone())
        .collect();
    for label in labels {
        let Some(window) = app.get_webview_window(&label) else {
            continue;
        };
        let (send, receive) = mpsc::sync_channel(1);
        window
            .eval_with_callback("window.__bellmanFolder || null", move |result| {
                let _ = send.send(result);
            })
            .map_err(|error| format!("Cannot read the open model folder: {error}"))?;
        let value = receive
            .recv_timeout(Duration::from_secs(2))
            .map_err(|_| "The open model window did not answer. Try opening the link again.")?;
        let folder: Option<PathBuf> = serde_json::from_str(&value)
            .map_err(|_| "The open model window returned an invalid folder.")?;
        let Some(folder) = folder else { continue };
        let folder = folder
            .canonicalize()
            .map_err(|error| format!("Cannot read the open model folder: {error}"))?;
        let title = format!(
            "{} · Bellman Workbench",
            folder.file_name().unwrap_or_default().to_string_lossy()
        );
        let changed = app
            .state::<Desktop>()
            .windows
            .lock()
            .unwrap()
            .get_mut(&label)
            .is_some_and(|entry| record_folder(entry, folder.clone()));
        if changed {
            let _ = window.set_title(&title);
            record_recent(app, &folder);
        }
    }
    Ok(())
}

fn record_recent(app: &AppHandle, folder: &Path) {
    let state = app.state::<Desktop>();
    let mut recent = state.recent.lock().unwrap();
    if let Err(error) = recent
        .record(folder)
        .and_then(|_| recent.save(&state.recent_path))
    {
        eprintln!("Cannot save recent projects: {error}");
    }
}

// The receiver processes links in order, away from Tauri's main thread.
fn route_request(app: &AppHandle, request: OpenRequest) {
    let state = app.state::<Desktop>();
    if state.exit_approved.load(Ordering::SeqCst) {
        return;
    }
    if let Err(error) = refresh_window_folders(app) {
        show_error(app, error);
        return;
    }
    let mut folders = state.windows.lock().unwrap();
    if state.exit_approved.load(Ordering::SeqCst) {
        return;
    }
    if let Some(label) = matching_window(&folders, &request.folder) {
        let existing = folders.get_mut(&label).unwrap();
        existing.request_serial += 1;
        existing.pending = request;
        if let Some(window) = app.get_webview_window(&label) {
            let delivered = if existing.loaded {
                deliver(&window, &existing.pending)
            } else {
                Ok(())
            };
            match delivered {
                Ok(()) => {
                    record_recent(app, &existing.folder);
                    finish_opening(app);
                }
                Err(error) => show_error(app, error.to_string()),
            }
            let _ = window.unminimize();
            let _ = window.set_focus();
        }
        return;
    }
    let label = format!("model-{}", state.next.fetch_add(1, Ordering::SeqCst));
    folders.insert(
        label.clone(),
        FolderWindow {
            folder: request.folder.clone(),
            pending: request.clone(),
            loaded: false,
            request_serial: 0,
            server: None,
        },
    );
    state.active_starts.fetch_add(1, Ordering::SeqCst);
    drop(folders);
    let settings = state.settings.lock().unwrap().clone();
    let log = state.logs.join(format!("{label}.log"));
    let app = app.clone();
    std::thread::spawn(move || {
        let _start = Starting(app.clone());
        let started = server::start(
            &settings.workbench_command,
            &request.folder,
            &settings.editor_command,
            &log,
            &app.state::<Desktop>().exit_approved,
        );
        let server = match started {
            Ok(server) => server,
            Err(error) => {
                app.state::<Desktop>()
                    .windows
                    .lock()
                    .unwrap()
                    .remove(&label);
                if !app.state::<Desktop>().exit_approved.load(Ordering::SeqCst) {
                    show_error(&app, error);
                }
                return;
            }
        };
        if app.state::<Desktop>().exit_approved.load(Ordering::SeqCst) {
            return;
        }
        let port = server.port;
        {
            let state = app.state::<Desktop>();
            let mut folders = state.windows.lock().unwrap();
            if let Some(entry) = folders.get_mut(&label) {
                entry.server = Some(server);
            } else {
                return;
            }
        }
        let app_for_window = app.clone();
        let location = request.folder.clone();
        let window_label = label.clone();
        let scheduled = app.run_on_main_thread(move || {
            let app = app_for_window;
            let label = window_label;
            let state = app.state::<Desktop>();
            let current = match state.windows.lock().unwrap().get(&label) {
                Some(entry) => entry.pending.clone(),
                None => return,
            };
            let page_url = current.page_url(port);
            let origin = page_url.origin();
            let load_app = app.clone();
            let window = WebviewWindowBuilder::new(&app, &label, WebviewUrl::External(page_url))
                .background_color(WINDOW_BACKGROUND)
                .theme(Some(tauri::Theme::Dark))
                .title(format!(
                    "{} · Bellman Workbench",
                    location.file_name().unwrap_or_default().to_string_lossy()
                ))
                .inner_size(1440.0, 940.0)
                .min_inner_size(720.0, 560.0)
                .initialization_script(format!(
                    "window.__bellmanFolder = {};",
                    serde_json::to_string(&location).unwrap()
                ))
                .on_navigation(move |url| url.origin() == origin)
                .on_page_load(move |window, payload| {
                    if matches!(payload.event(), PageLoadEvent::Finished) {
                        let state = load_app.state::<Desktop>();
                        let mut folders = state.windows.lock().unwrap();
                        if let Some(entry) = folders.get_mut(window.label()) {
                            entry.loaded = true;
                            if let Err(error) = deliver(&window, &entry.pending) {
                                show_error(&load_app, error.to_string());
                            }
                        }
                    }
                });
            #[cfg(target_os = "macos")]
            let window = window.title_bar_style(tauri::TitleBarStyle::Transparent);
            let window = window.build();
            match window {
                Ok(window) => {
                    record_recent(&app, &location);
                    let event_app = app.clone();
                    let event_window = window.clone();
                    window.on_window_event(move |event| match event {
                        tauri::WindowEvent::CloseRequested { api, .. } => {
                            api.prevent_close();
                            close_window(&event_app, &event_window);
                        }
                        tauri::WindowEvent::Destroyed => {
                            let removed = event_app
                                .state::<Desktop>()
                                .windows
                                .lock()
                                .unwrap()
                                .remove(event_window.label());
                            drop(removed);
                        }
                        _ => {}
                    });
                    finish_opening(&app);
                }
                Err(error) => {
                    state.windows.lock().unwrap().remove(&label);
                    show_error(&app, format!("Cannot open the model window: {error}"));
                }
            }
        });
        if let Err(error) = scheduled {
            app.state::<Desktop>()
                .windows
                .lock()
                .unwrap()
                .remove(&label);
            show_error(&app, format!("Cannot create the model window: {error}"));
        }
    });
}

fn open_argument(app: &AppHandle, value: &str, cwd: &Path) {
    let request = if value.starts_with("bellman:") {
        OpenRequest::from_url(value)
    } else {
        OpenRequest::from_path(&cwd.join(value))
    };
    match request {
        Ok(request) => open_request(app, request),
        Err(error) => show_error(app, error),
    }
}

fn dirty(window: &WebviewWindow) -> bool {
    let (send, receive) = mpsc::sync_channel(1);
    if window
        .eval_with_callback("window.__bellmanDirty !== false", move |result| {
            let _ = send.send(result);
        })
        .is_err()
    {
        return true;
    }
    receive
        .recv_timeout(Duration::from_secs(2))
        .map_or(true, |result| result != "false")
}

fn close_window(app: &AppHandle, window: &WebviewWindow) {
    let state = app.state::<Desktop>();
    let label = window.label().to_string();
    let mut closing = state.closing.lock().unwrap();
    if closing.contains(&label) {
        return;
    }
    closing.push(label.clone());
    drop(closing);
    let serial = state
        .windows
        .lock()
        .unwrap()
        .get(&label)
        .map(|entry| entry.request_serial);
    let app = app.clone();
    let window = window.clone();
    std::thread::spawn(move || {
        let close = !dirty(&window)
            || app
                .dialog()
                .message("This window has unsaved changes. Close it and discard them?")
                .title("Close Workbench")
                .buttons(MessageDialogButtons::OkCancelCustom(
                    "Discard and close".into(),
                    "Keep open".into(),
                ))
                .blocking_show();
        let latest = app
            .state::<Desktop>()
            .windows
            .lock()
            .unwrap()
            .get(&label)
            .map(|entry| entry.request_serial);
        if close && latest == serial {
            let _ = window.destroy();
        }
        app.state::<Desktop>()
            .closing
            .lock()
            .unwrap()
            .retain(|item| item != &label);
    });
}

fn choose_path(app: &AppHandle, folder: bool) {
    welcome_status(
        app,
        if folder {
            "Choose a project folder."
        } else {
            "Choose a Bellman file."
        },
        true,
    );
    let dialog = app
        .dialog()
        .file()
        .set_title(if folder { "Open Project" } else { "Open File" });
    let app = app.clone();
    let callback = move |file: Option<tauri_plugin_dialog::FilePath>| {
        let Some(file) = file else {
            welcome_status(&app, "Opening cancelled.", false);
            return;
        };
        let path = match file.into_path() {
            Ok(path) => path,
            Err(error) => {
                show_error(&app, format!("Cannot open the selected path: {error}"));
                return;
            }
        };
        match OpenRequest::from_path(&path) {
            Ok(request) => {
                welcome_status(&app, "Opening project…", true);
                open_request(&app, request);
            }
            Err(error) => show_error(&app, error),
        }
    };
    if folder {
        dialog.pick_folder(callback);
    } else {
        dialog
            .add_filter("Bellman files", &["bl", "yml"])
            .pick_file(callback);
    }
}

fn choose_command(app: &AppHandle, editor: bool) {
    let dialog = app.dialog().file().set_title(if editor {
        "Choose Code or Cursor executable"
    } else {
        "Choose bellman-workbench"
    });
    let app = app.clone();
    dialog.pick_file(move |selected| {
        if let Some(path) = selected.and_then(|file| file.into_path().ok()) {
            let state = app.state::<Desktop>();
            let mut settings = state.settings.lock().unwrap();
            if editor {
                settings.editor_command = vec![path.to_string_lossy().into(), "--goto".into()];
            } else {
                settings.workbench_command = vec![path.to_string_lossy().into()];
            }
            if let Err(error) = settings.save(&state.settings_path) {
                show_error(&app, error);
            } else {
                app.dialog()
                    .message("Saved. The command applies to model windows opened next.")
                    .title("Bellman Workbench")
                    .show(|_| {});
            }
        }
    });
}

fn render_welcome(window: &WebviewWindow) -> tauri::Result<()> {
    let state = window.state::<Desktop>();
    let folders = state.recent.lock().unwrap().folders().to_vec();
    let data = serde_json::json!({
        "recentProjects": folders.iter().map(|folder| serde_json::json!({
            "name": folder.file_name().unwrap_or(folder.as_os_str()).to_string_lossy(),
            "path": folder.to_string_lossy(),
        })).collect::<Vec<_>>(),
        "shortcutModifier": if cfg!(target_os = "macos") { "⌘" } else { "Ctrl" },
    });
    window.eval(format!("window.bellmanWelcome?.setNativeState({data});"))?;
    *state.welcome_folders.lock().unwrap() = folders;
    Ok(())
}

fn show_welcome(app: &AppHandle) -> tauri::Result<()> {
    if let Some(window) = app.get_webview_window("welcome") {
        let state = app.state::<Desktop>();
        let recent = state.recent.lock().unwrap();
        if recent.folders() != state.welcome_folders.lock().unwrap().as_slice() {
            window.reload()?;
        }
        window.unminimize()?;
        window.show()?;
        return window.set_focus();
    }
    let welcome_app = app.clone();
    let welcome = WebviewWindowBuilder::new(app, "welcome", WebviewUrl::App("index.html".into()))
        .background_color(WINDOW_BACKGROUND)
        .theme(Some(tauri::Theme::Dark))
        .title("Bellman Workbench")
        .inner_size(800.0, 560.0)
        .min_inner_size(640.0, 480.0)
        .on_navigation(move |url| match welcome_navigation_path(url) {
            Some("/open-project") => {
                choose_path(&welcome_app, true);
                false
            }
            Some("/open-file") => {
                choose_path(&welcome_app, false);
                false
            }
            Some(path) if recent_index(path).is_some() => {
                let index = recent_index(path).expect("checked recent index");
                let state = welcome_app.state::<Desktop>();
                let request = recent_request(&state.welcome_folders.lock().unwrap(), index);
                match request {
                    Ok(request) => {
                        welcome_status(&welcome_app, "Opening project…", true);
                        open_request(&welcome_app, request);
                    }
                    Err(error) => show_error(&welcome_app, error),
                }
                false
            }
            Some(_) => true,
            None => false,
        })
        .on_new_window(|_, _| tauri::webview::NewWindowResponse::Deny)
        .on_page_load(|window, payload| {
            if matches!(payload.event(), PageLoadEvent::Finished) {
                if let Err(error) = render_welcome(&window) {
                    show_error(window.app_handle(), format!("Cannot list recent projects: {error}"));
                }
            }
        });
    #[cfg(target_os = "macos")]
    let welcome = welcome.title_bar_style(tauri::TitleBarStyle::Transparent);
    welcome.build().map(|_| ())
}

fn request_welcome(app: &AppHandle) {
    let app = app.clone();
    std::thread::spawn(move || {
        if let Err(error) = refresh_window_folders(&app) {
            eprintln!("Cannot refresh recent projects: {error}");
        }
        let welcome_app = app.clone();
        if let Err(error) = app.run_on_main_thread(move || {
            if let Err(error) = show_welcome(&welcome_app) {
                show_error(&welcome_app, format!("Cannot open Welcome: {error}"));
            }
        }) {
            show_error(&app, format!("Cannot open Welcome: {error}"));
        }
    });
}

fn main() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, args, cwd| {
            let mut locations = args
                .iter()
                .skip(1)
                .filter(|arg| !arg.starts_with('-'))
                .peekable();
            if locations.peek().is_none() {
                request_welcome(app);
            }
            for location in locations {
                open_argument(app, location, Path::new(&cwd));
            }
        }))
        .plugin(tauri_plugin_deep_link::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let settings_path = app.path().app_config_dir()?.join("commands.json");
            let settings = Settings::load(&settings_path);
            let recent_path = app.path().app_config_dir()?.join("recent-projects.json");
            let recent = RecentProjects::load(&recent_path);
            let logs = app.path().app_log_dir()?;
            std::fs::create_dir_all(&logs)?;
            let (requests, received) = mpsc::channel();
            app.manage(Desktop {
                windows: Mutex::new(HashMap::new()),
                requests,
                settings: Mutex::new(settings.clone().unwrap_or_default()),
                settings_path,
                recent: Mutex::new(recent),
                welcome_folders: Mutex::new(Vec::new()),
                recent_path,
                logs,
                next: AtomicU64::new(1),
                active_starts: AtomicUsize::new(0),
                closing: Mutex::new(Vec::new()),
                quitting: AtomicBool::new(false),
                exit_approved: AtomicBool::new(false),
            });
            let routing_app = app.handle().clone();
            std::thread::spawn(move || {
                while let Ok(request) = received.recv() {
                    let _request = Starting(routing_app.clone());
                    route_request(&routing_app, request);
                }
            });
            let open_project = MenuItemBuilder::with_id("open-folder", "Open Project…")
                .accelerator("CmdOrCtrl+O")
                .build(app)?;
            let open_file = MenuItemBuilder::with_id("open-file", "Open File…")
                .accelerator("CmdOrCtrl+Shift+O")
                .build(app)?;
            let file = SubmenuBuilder::new(app, "File")
                .items(&[&open_project, &open_file])
                .text("welcome", "Welcome")
                .separator()
                .close_window()
                .build()?;
            let edit = SubmenuBuilder::new(app, "Edit")
                .undo()
                .redo()
                .separator()
                .cut()
                .copy()
                .paste()
                .select_all()
                .build()?;
            let settings_menu = SubmenuBuilder::new(app, "Settings")
                .text("workbench-command", "Workbench command…")
                .text("editor-command", "Editor command…")
                .build()?;
            let application = SubmenuBuilder::new(app, "Bellman Workbench")
                .about(None)
                .separator()
                .quit()
                .build()?;
            app.set_menu(
                MenuBuilder::new(app)
                    .items(&[&application, &file, &edit, &settings_menu])
                    .build()?,
            )?;
            show_welcome(app.handle())?;
            if let Err(error) = settings {
                show_error(app.handle(), error);
            }
            let handle = app.handle().clone();
            app.deep_link().on_open_url(move |event| {
                for url in event.urls() {
                    open_argument(&handle, url.as_str(), Path::new("/"));
                }
            });
            let cwd = std::env::current_dir().unwrap_or_default();
            for argument in std::env::args().skip(1).filter(|arg| !arg.starts_with('-')) {
                open_argument(app.handle(), &argument, &cwd);
            }
            if let Some(urls) = app.deep_link().get_current()? {
                for url in urls {
                    open_argument(app.handle(), url.as_str(), &cwd);
                }
            }
            Ok(())
        })
        .on_menu_event(|app, event| match event.id().as_ref() {
            "open-folder" => choose_path(app, true),
            "open-file" => choose_path(app, false),
            "welcome" => request_welcome(app),
            "workbench-command" => choose_command(app, false),
            "editor-command" => choose_command(app, true),
            _ => {}
        })
        .build(tauri::generate_context!())
        .expect("Cannot initialise Bellman Workbench");
    app.run(|app, event| match event {
        #[cfg(target_os = "macos")]
        tauri::RunEvent::Opened { urls } => {
            for url in urls {
                if url.scheme() == "file" {
                    if let Ok(path) = url.to_file_path() {
                        open_argument(app, &path.to_string_lossy(), Path::new("/"));
                    }
                }
            }
        }
        tauri::RunEvent::ExitRequested { api, .. } => {
            let state = app.state::<Desktop>();
            if state.exit_approved.load(Ordering::SeqCst)
                || (state.windows.lock().unwrap().is_empty()
                    && state.active_starts.load(Ordering::SeqCst) == 0)
            {
                return;
            }
            api.prevent_exit();
            if state.quitting.swap(true, Ordering::SeqCst) {
                return;
            }
            let app = app.clone();
            std::thread::spawn(move || {
                let any_dirty = app
                    .webview_windows()
                    .iter()
                    .filter(|(label, _)| label.starts_with("model-"))
                    .any(|(_, window)| dirty(window));
                let quit = !any_dirty
                    || app
                        .dialog()
                        .message("A model has unsaved changes. Quit and discard them?")
                        .title("Quit Workbench")
                        .buttons(MessageDialogButtons::OkCancelCustom(
                            "Discard and quit".into(),
                            "Keep open".into(),
                        ))
                        .blocking_show();
                if quit {
                    let state = app.state::<Desktop>();
                    state.exit_approved.store(true, Ordering::SeqCst);
                    while state.active_starts.load(Ordering::SeqCst) != 0 {
                        std::thread::sleep(Duration::from_millis(25));
                    }
                    state.windows.lock().unwrap().clear();
                    app.exit(0);
                } else {
                    app.state::<Desktop>()
                        .quitting
                        .store(false, Ordering::SeqCst);
                }
            });
        }
        tauri::RunEvent::Exit => {
            app.state::<Desktop>().windows.lock().unwrap().clear();
        }
        _ => {}
    });
}

#[cfg(test)]
mod folder_tests {
    use super::*;

    fn entry(folder: &str, file: &str) -> FolderWindow {
        FolderWindow {
            folder: folder.into(),
            pending: OpenRequest {
                folder: folder.into(),
                file: Some(file.into()),
                line: 7,
                r#box: None,
            },
            loaded: true,
            request_serial: 0,
            server: None,
        }
    }

    #[test]
    fn changed_folder_clears_old_navigation_and_keeps_window_ownership() {
        let mut windows = HashMap::from([("model-1".into(), entry("original", "old.bl"))]);
        assert!(record_folder(
            windows.get_mut("model-1").unwrap(),
            "created".into()
        ));
        assert_eq!(matching_window(&windows, Path::new("original")), None);
        assert_eq!(
            matching_window(&windows, Path::new("created")).as_deref(),
            Some("model-1")
        );
        let changed = windows.get("model-1").unwrap();
        assert_eq!(changed.pending.file, None);
        assert_eq!(changed.request_serial, 1);
        assert!(!record_folder(
            windows.get_mut("model-1").unwrap(),
            "created".into()
        ));
        assert!(windows.remove("model-1").is_some());
        assert!(windows.is_empty());
    }

    #[test]
    fn duplicate_displayed_folders_keep_both_windows_and_choose_consistently() {
        let mut windows = HashMap::from([
            ("model-2".into(), entry("created", "second.bl")),
            ("model-1".into(), entry("original", "first.bl")),
        ]);
        record_folder(windows.get_mut("model-1").unwrap(), "created".into());
        assert_eq!(windows.len(), 2);
        assert_eq!(
            matching_window(&windows, Path::new("created")).as_deref(),
            Some("model-1")
        );
        windows.remove("model-1");
        assert_eq!(
            matching_window(&windows, Path::new("created")).as_deref(),
            Some("model-2")
        );
        assert_eq!(
            windows["model-2"].pending.file.as_deref(),
            Some("second.bl")
        );
    }
}

#[cfg(test)]
mod welcome_tests {
    use super::*;

    #[test]
    fn bundled_page_and_open_actions_allow_no_arguments() {
        let origin = if cfg!(windows) {
            "http://tauri.localhost"
        } else {
            "tauri://localhost"
        };
        for path in [
            "/",
            "/index.html",
            "/open-project",
            "/open-file",
            "/recent/0",
            "/recent/7",
        ] {
            let url = url::Url::parse(&format!("{origin}{path}")).unwrap();
            assert_eq!(welcome_navigation_path(&url), Some(path));
        }
        let form = url::Url::parse(&format!("{origin}/open-project?")).unwrap();
        assert_eq!(welcome_navigation_path(&form), Some("/open-project"));
        for path in [
            "/other.html",
            "/open-project/",
            "/open-file?path=/tmp/model.bl",
            "/open-project#other",
            "/recent/",
            "/recent/-1",
            "/recent/1.5",
            "/recent/0/extra",
            "/recent/%30",
            "/recent/9999999999999999999999999999999999999",
            "/recent/0?path=/tmp/model",
            "/recent/0#other",
        ] {
            let url = url::Url::parse(&format!("{origin}{path}")).unwrap();
            assert_eq!(welcome_navigation_path(&url), None, "{url}");
        }
    }

    #[test]
    fn recent_actions_resolve_only_listed_folders_and_report_missing_folders() {
        let directory = tempfile::tempdir().unwrap();
        let folder = directory.path().join("model");
        std::fs::create_dir(&folder).unwrap();
        let folders = vec![folder.clone()];
        assert_eq!(
            recent_request(&folders, 0).unwrap().folder,
            folder.canonicalize().unwrap()
        );
        assert!(recent_request(&folders, 1).is_err());
        std::fs::remove_dir(&folder).unwrap();
        assert!(recent_request(&folders, 0)
            .unwrap_err()
            .contains("Cannot open"));
        assert_eq!(folders, vec![folder]);
        let file = directory.path().join("replaced.bl");
        std::fs::write(&file, "model").unwrap();
        assert!(recent_request(&[file], 0)
            .unwrap_err()
            .contains("no longer a folder"));
    }

    #[test]
    fn foreign_addresses_cannot_request_a_native_chooser() {
        for address in [
            "https://example.com/open-project",
            "http://127.0.0.1:8765/open-file",
            "http://localhost/open-project",
            "http://tauri.localhost.example.com/open-project",
            "https://tauri.localhost/open-project",
            "tauri://elsewhere/open-file",
            "tauri://localhost:8765/open-file",
            "http://tauri.localhost:8765/open-project",
            "tauri://user@localhost/open-project",
            "http://user@tauri.localhost/open-project",
            "file:///open-project",
            "bellman://open?folder=/tmp",
            "https://example.com/recent/0",
            "http://127.0.0.1:8765/recent/0",
            "tauri://user@localhost/recent/0",
            "http://tauri.localhost:8765/recent/0",
        ] {
            let url = url::Url::parse(address).unwrap();
            assert_eq!(welcome_navigation_path(&url), None, "{address}");
        }
        let other_platform = if cfg!(windows) {
            "tauri://localhost/open-project"
        } else {
            "http://tauri.localhost/open-project"
        };
        let url = url::Url::parse(other_platform).unwrap();
        assert_eq!(welcome_navigation_path(&url), None);
    }
}
