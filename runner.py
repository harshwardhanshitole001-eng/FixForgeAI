"""Runs generated tests against code for real, using pytest in a temporary folder.

Safety: this executes code on your machine. It uses a fresh temp folder and a
timeout, which is fine for a local demo but is NOT a security sandbox.
For a public deployment, run each job in a container with no network access.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT_SECONDS = 15


def run_pytest(solution_code: str, tests_code: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="fixforge_") as folder:
        workdir = Path(folder)
        (workdir / "solution.py").write_text(solution_code, encoding="utf-8")
        (workdir / "test_solution.py").write_text(tests_code, encoding="utf-8")

        try:
            proc = subprocess.run(
                [
                    sys.executable, "-m", "pytest", "-q", "--tb=short",
                    "-p", "no:cacheprovider", "test_solution.py",
                ],
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return {
                "passed": 0, "failed": 0, "ok": False,
                "output": f"Tests stopped after {TIMEOUT_SECONDS} seconds. Check for infinite loops.",
            }

    output = (proc.stdout + proc.stderr).strip()
    passed = _count(output, "passed")
    failed = _count(output, "failed") + _count(output, "error")
    ok = proc.returncode == 0 and passed > 0 and failed == 0
    return {"passed": passed, "failed": failed, "ok": ok, "output": output}


def _count(text: str, word: str) -> int:
    match = re.search(rf"(\d+) {word}", text)
    return int(match.group(1)) if match else 0
