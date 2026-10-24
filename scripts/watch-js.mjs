import { spawn } from "node:child_process";
import { watchFile, unwatchFile } from "node:fs";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("../", import.meta.url));
const source = fileURLToPath(new URL("../assets/js/_main.js", import.meta.url));
let building = false;
let pending = false;
let stopped = false;

function build() {
  if (stopped) return;
  if (building) {
    pending = true;
    return;
  }

  building = true;
  const child = spawn("npm", ["run", "build:js"], { cwd: root, stdio: "inherit" });
  child.on("error", (error) => console.error(`Cannot start JavaScript build: ${error.message}`));
  child.on("close", (code) => {
    building = false;
    if (code !== 0) console.error("JavaScript build failed; waiting for the next edit.");
    if (pending) {
      pending = false;
      build();
    }
  });
}

// Watch the only minifier input. Polling also handles editors that replace the
// file on save, and the generated main.min.js cannot trigger a rebuild loop.
watchFile(source, { interval: 250 }, build);
console.log("Watching assets/js/_main.js. Press Ctrl+C to stop.");

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    stopped = true;
    unwatchFile(source);
    // Let an active build finish before exiting so its output is not truncated.
  });
}
