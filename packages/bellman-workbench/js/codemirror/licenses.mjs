// Writes this bundle's license notices to standard output.
import { fileURLToPath } from "node:url";
import { licenseNotices } from "../license-notices.mjs";

const preamble =
  "The license notices of the packages bundled into bellman-workbench.js or used\n" +
  "to build it, written by js/codemirror/licenses.mjs from package-lock.json\n" +
  "and the license files under node_modules. Each notice names the package,\n" +
  "its version and its license, then gives the license file's text.";

process.stdout.write(licenseNotices(fileURLToPath(new URL(".", import.meta.url)), preamble));
