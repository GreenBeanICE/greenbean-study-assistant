const { spawnSync } = require("node:child_process");

const args = ["-m", "pytest", ...process.argv.slice(2)];
const candidates = process.env.PYTHON
  ? [process.env.PYTHON]
  : process.platform === "win32"
    ? ["py", "python"]
    : ["python", "python3"];

let lastResult;

for (const command of candidates) {
  const result = spawnSync(command, args, { stdio: "inherit" });
  lastResult = result;

  if (!result.error || result.error.code !== "ENOENT") {
    process.exit(result.status ?? 1);
  }
}

console.error(
  `Unable to find a Python executable. Tried: ${candidates.join(", ")}`
);
process.exit(lastResult?.status ?? 1);
