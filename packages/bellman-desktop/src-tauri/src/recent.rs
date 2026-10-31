//! Recently opened model folders, stored separately from executable commands.
use serde::{Deserialize, Serialize};
use std::{
    fs,
    path::{Path, PathBuf},
};

const MAX_PROJECTS: usize = 8;

#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(transparent)]
pub struct RecentProjects(Vec<PathBuf>);

impl RecentProjects {
    pub fn load(path: &Path) -> Self {
        let paths: Vec<PathBuf> = fs::read(path)
            .ok()
            .and_then(|bytes| serde_json::from_slice(&bytes).ok())
            .unwrap_or_default();
        let mut folders = Vec::new();
        for path in paths.into_iter().filter(|path| path.is_absolute()) {
            // Keep missing folders visible so opening them can explain the failure.
            let folder = path.canonicalize().unwrap_or(path);
            if !folders.contains(&folder) {
                folders.push(folder);
            }
            if folders.len() == MAX_PROJECTS {
                break;
            }
        }
        Self(folders)
    }

    pub fn folders(&self) -> &[PathBuf] {
        &self.0
    }

    pub fn record(&mut self, folder: &Path) -> Result<(), String> {
        let folder = folder.canonicalize().map_err(|error| error.to_string())?;
        if !folder.is_dir() {
            return Err("The recent project is not a directory.".into());
        }
        self.0.retain(|existing| existing != &folder);
        self.0.insert(0, folder);
        self.0.truncate(MAX_PROJECTS);
        Ok(())
    }

    pub fn save(&self, path: &Path) -> Result<(), String> {
        let parent = path
            .parent()
            .ok_or("The recent-project file has no directory.")?;
        fs::create_dir_all(parent).map_err(|error| error.to_string())?;
        fs::write(
            path,
            serde_json::to_vec_pretty(self).map_err(|error| error.to_string())?,
        )
        .map_err(|error| error.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn reopening_a_folder_moves_it_first_without_duplicates_and_keeps_eight() {
        let directory = tempfile::tempdir().unwrap();
        let mut recent = RecentProjects::default();
        for index in 0..10 {
            let folder = directory.path().join(format!("model-{index}"));
            fs::create_dir(&folder).unwrap();
            recent.record(&folder).unwrap();
        }
        let reopened = directory.path().join("model-4");
        recent.record(&reopened.join(".")).unwrap();
        let expected: Vec<_> = [4, 9, 8, 7, 6, 5, 3, 2]
            .iter()
            .map(|index| {
                directory
                    .path()
                    .join(format!("model-{index}"))
                    .canonicalize()
                    .unwrap()
            })
            .collect();
        assert_eq!(recent.folders(), expected);
        let history = directory.path().join("config/recent-projects.json");
        recent.save(&history).unwrap();
        assert_eq!(RecentProjects::load(&history).folders(), expected);
    }

    #[test]
    fn missing_or_malformed_history_does_not_prevent_recording_a_project() {
        let directory = tempfile::tempdir().unwrap();
        let history = directory.path().join("recent-projects.json");
        assert!(RecentProjects::load(&history).folders().is_empty());
        for contents in ["{broken", "{\"commands\":[]}", "[42]"] {
            fs::write(&history, contents).unwrap();
            let mut recent = RecentProjects::load(&history);
            assert!(recent.folders().is_empty());
            recent.record(directory.path()).unwrap();
            recent.save(&history).unwrap();
            assert_eq!(RecentProjects::load(&history).folders(), recent.folders());
        }
    }

    #[test]
    fn loading_limits_and_deduplicates_history_without_removing_missing_folders() {
        let directory = tempfile::tempdir().unwrap();
        let missing = directory
            .path()
            .canonicalize()
            .unwrap()
            .join("removed-model");
        let mut folders = vec![PathBuf::from("relative"), missing.clone(), missing.clone()];
        folders.extend((0..12).map(|index| directory.path().join(format!("missing-{index}"))));
        let history = directory.path().join("recent-projects.json");
        fs::write(&history, serde_json::to_vec(&folders).unwrap()).unwrap();
        let recent = RecentProjects::load(&history);
        assert_eq!(recent.folders().len(), 8);
        assert_eq!(recent.folders()[0], missing);
        assert_eq!(recent.folders()[1..], folders[3..10]);
    }
}
