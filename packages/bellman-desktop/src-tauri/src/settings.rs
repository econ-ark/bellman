//! Saved command choices belong to the user, never to an incoming link.
use serde::{Deserialize, Serialize};
use std::{env, fs, path::Path};

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct Settings {
    #[serde(default)]
    pub workbench_command: Vec<String>,
    #[serde(default)]
    pub editor_command: Vec<String>,
}

impl Settings {
    pub fn load(path: &Path) -> Result<Self, String> {
        let mut settings: Self = match fs::read(path) {
            Ok(bytes) => serde_json::from_slice(&bytes)
                .map_err(|e| format!("Cannot read desktop settings: {e}"))?,
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => Self::default(),
            Err(e) => return Err(format!("Cannot read desktop settings: {e}")),
        };
        for (key, target) in [
            ("BELLMAN_DESKTOP_COMMAND", &mut settings.workbench_command),
            ("BELLMAN_WORKBENCH_EDITOR", &mut settings.editor_command),
        ] {
            if let Some(value) = env::var_os(key) {
                *target = serde_json::from_str(&value.to_string_lossy())
                    .map_err(|_| format!("{key} must be a JSON list of command arguments."))?;
                if target.is_empty() || target[0].is_empty() {
                    return Err(format!("{key} must name an executable."));
                }
            }
        }
        if settings.workbench_command.is_empty() {
            settings.workbench_command.push("bellman-workbench".into());
        }
        Ok(settings)
    }
    pub fn save(&self, path: &Path) -> Result<(), String> {
        let parent = path.parent().ok_or("The settings path has no directory.")?;
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
        let temporary = path.with_extension("json.tmp");
        fs::write(
            &temporary,
            serde_json::to_vec_pretty(self).map_err(|e| e.to_string())?,
        )
        .map_err(|e| e.to_string())?;
        // The final write also works where rename cannot replace a file (Windows).
        fs::copy(&temporary, path).map_err(|e| e.to_string())?;
        fs::remove_file(temporary).map_err(|e| e.to_string())?;
        Ok(())
    }
}
