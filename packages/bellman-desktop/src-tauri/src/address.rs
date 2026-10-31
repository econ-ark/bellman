//! Addresses contain model locations, never commands.
use serde::Serialize;
use std::{
    collections::HashMap,
    path::{Component, Path, PathBuf},
};
use url::Url;

#[derive(Clone, Debug, Serialize, PartialEq)]
pub struct OpenRequest {
    #[serde(skip)]
    pub folder: PathBuf,
    pub file: Option<String>,
    pub line: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub r#box: Option<String>,
}

impl OpenRequest {
    pub fn from_url(value: &str) -> Result<Self, String> {
        let url = Url::parse(value).map_err(|_| "The Workbench link is not a URL.")?;
        if url.scheme() != "bellman"
            || url.host_str() != Some("open")
            || !matches!(url.path(), "" | "/")
            || url.port().is_some()
            || !url.username().is_empty()
            || url.password().is_some()
            || url.fragment().is_some()
        {
            return Err("Expected bellman://open?folder=…&file=…&line=….".into());
        }
        let mut fields = HashMap::new();
        for (key, value) in url.query_pairs() {
            if !["folder", "file", "line", "box"].contains(&key.as_ref())
                || fields.insert(key.to_string(), value.to_string()).is_some()
            {
                return Err("The Workbench link has an unknown or repeated parameter.".into());
            }
        }
        let folder = fields
            .get("folder")
            .ok_or("The Workbench link needs a folder.")?;
        let file = fields
            .get("file")
            .ok_or("The Workbench link needs a file.")?;
        let line = fields
            .get("line")
            .ok_or("The Workbench link needs a line.")?;
        if line.is_empty() || !line.bytes().all(|c| c.is_ascii_digit()) {
            return Err("The line must be a positive integer.".into());
        }
        let line = line.parse::<u32>().map_err(|_| "The line is too large.")?;
        if line == 0 || line > 2_147_483_647 {
            return Err("The line must be a positive integer.".into());
        }
        Self::checked(
            Path::new(folder),
            Some(file),
            line,
            fields.get("box").cloned(),
        )
    }

    pub fn from_path(path: &Path) -> Result<Self, String> {
        let path = path
            .canonicalize()
            .map_err(|e| format!("Cannot open {}: {e}", path.display()))?;
        if path.is_dir() {
            return Self::checked(&path, None, 1, None);
        }
        let name = path
            .file_name()
            .and_then(|s| s.to_str())
            .ok_or("The file name is not valid UTF-8.")?;
        if path.extension().and_then(|s| s.to_str()) != Some("bl")
            && !(name == "spec.yml" || name.starts_with("spec.") && name.ends_with(".yml"))
        {
            return Err("Choose a .bl stage file or a spec.yml recipe.".into());
        }
        Self::checked(
            path.parent().ok_or("The file has no folder.")?,
            Some(name),
            1,
            None,
        )
    }

    fn checked(
        folder: &Path,
        file: Option<&str>,
        line: u32,
        node: Option<String>,
    ) -> Result<Self, String> {
        if !folder.is_absolute() {
            return Err("The model folder must be an absolute path.".into());
        }
        let folder = folder
            .canonicalize()
            .map_err(|e| format!("Cannot open the model folder: {e}"))?;
        if !folder.is_dir() {
            return Err("The model folder is not a directory.".into());
        }
        if let Some(file) = file {
            let relative = Path::new(file);
            if file.is_empty()
                || file.contains('\\')
                || relative.is_absolute()
                || relative.components().any(|c| {
                    matches!(
                        c,
                        Component::ParentDir | Component::RootDir | Component::Prefix(_)
                    )
                })
            {
                return Err(
                    "The linked file must be a relative path inside the model folder.".into(),
                );
            }
            let target = folder
                .join(relative)
                .canonicalize()
                .map_err(|e| format!("Cannot open the linked file: {e}"))?;
            if !target.starts_with(&folder) || !target.is_file() {
                return Err("The linked file must be a file inside the model folder.".into());
            }
        }
        if node
            .as_ref()
            .is_some_and(|s| s.is_empty() || s.len() > 4096)
        {
            return Err("The box name is empty or too long.".into());
        }
        Ok(Self {
            folder,
            file: file.map(str::to_owned),
            line,
            r#box: node,
        })
    }

    pub fn page_url(&self, port: u16) -> Url {
        let mut url = Url::parse(&format!("http://127.0.0.1:{port}/")).expect("loopback URL");
        if let Some(file) = &self.file {
            url.query_pairs_mut()
                .append_pair("file", file)
                .append_pair("line", &self.line.to_string());
            if let Some(node) = &self.r#box {
                url.query_pairs_mut().append_pair("box", node);
            }
        }
        url
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn link(folder: &Path, file: &str, line: &str) -> String {
        let mut url = Url::parse("bellman://open").unwrap();
        url.query_pairs_mut()
            .append_pair("folder", folder.to_str().unwrap())
            .append_pair("file", file)
            .append_pair("line", line);
        url.into()
    }
    #[test]
    fn encoded_paths_and_page_location_are_preserved() {
        let directory = tempfile::tempdir().unwrap();
        let file = "cons & ρ #1.bl";
        std::fs::write(directory.path().join(file), "model").unwrap();
        let request = OpenRequest::from_url(&link(directory.path(), file, "21")).unwrap();
        assert_eq!(request.file.as_deref(), Some(file));
        let page = request.page_url(9876);
        assert_eq!(
            page.query_pairs().find(|(k, _)| k == "file").unwrap().1,
            file
        );
        assert_eq!(request.line, 21);
    }
    #[test]
    fn malformed_and_repeated_fields_are_refused() {
        let directory = tempfile::tempdir().unwrap();
        std::fs::write(directory.path().join("cons.bl"), "model").unwrap();
        for line in ["0", "-1", "1.5", "NaN", "2147483648", "4294967296", "+1"] {
            assert!(OpenRequest::from_url(&link(directory.path(), "cons.bl", line)).is_err());
        }
        let good = link(directory.path(), "cons.bl", "1");
        for tail in ["&line=2", "&command=rm", "#fragment"] {
            assert!(OpenRequest::from_url(&(good.clone() + tail)).is_err());
        }
        assert!(OpenRequest::from_url(&good.replace("bellman://open", "https://open")).is_err());
    }
    #[test]
    fn parent_paths_and_symlink_escapes_are_refused() {
        let directory = tempfile::tempdir().unwrap();
        assert!(OpenRequest::from_url(&link(directory.path(), "../outside.bl", "1")).is_err());
        assert!(OpenRequest::from_url(&link(directory.path(), "/tmp/outside.bl", "1")).is_err());
        #[cfg(unix)]
        {
            let other = tempfile::NamedTempFile::new().unwrap();
            std::os::unix::fs::symlink(other.path(), directory.path().join("escape.bl")).unwrap();
            assert!(OpenRequest::from_url(&link(directory.path(), "escape.bl", "1")).is_err());
        }
    }
    #[test]
    fn folders_and_recipes_open_without_claiming_other_yaml() {
        let directory = tempfile::tempdir().unwrap();
        assert_eq!(OpenRequest::from_path(directory.path()).unwrap().file, None);
        for name in ["spec.yml", "spec.baseline.yml", "cons.bl"] {
            let path = directory.path().join(name);
            std::fs::write(&path, "model").unwrap();
            assert_eq!(
                OpenRequest::from_path(&path).unwrap().file.as_deref(),
                Some(name)
            );
        }
        let path = directory.path().join("unrelated.yml");
        std::fs::write(&path, "document").unwrap();
        assert!(OpenRequest::from_path(&path).is_err());
    }
}
