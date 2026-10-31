// The license notices for a package-lock.json and its installed packages.
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const LICENSE_FILES = ["license", "license.md", "license.txt", "licence", "licence.md"];
const RULE = "-".repeat(78);

// The license file of the package folder `folder`, or null.
function licenseFileOf(folder) {
  if (!existsSync(folder)) return null;
  const names = readdirSync(folder);
  const found = names.find((name) => LICENSE_FILES.includes(name.toLowerCase()));
  return found ? join(folder, found) : null;
}

// Returns the notices from directory, preceded by the caller's preamble.
export function licenseNotices(directory, preamble) {
  const lock = JSON.parse(readFileSync(join(directory, "package-lock.json"), "utf8"));
  const notices = [];
  for (const [key, record] of Object.entries(lock.packages)) {
    if (!key.startsWith("node_modules/")) continue;
    const name = key.slice("node_modules/".length);
    const folder = join(directory, key);
    const head = `${name} ${record.version}\nlicense: ${record.license ?? "not stated in the lockfile"}`;
    const file = licenseFileOf(folder);
    let body;
    if (file) {
      body = readFileSync(file, "utf8").trimEnd();
    } else if (record.optional && !existsSync(folder)) {
      body = "An optional package of another platform; npm did not install it in this build.";
    } else {
      body = "The package carries no license file; its license is the field above.";
    }
    notices.push(`${head}\n\n${body}`);
  }
  return `${preamble}\n\n${RULE}\n${notices.join(`\n\n${RULE}\n`)}\n`;
}
