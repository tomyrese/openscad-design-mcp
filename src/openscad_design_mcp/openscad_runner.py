import contextlib
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import psutil

from .config import Settings, discover_openscad
from .errors import DesignError, sanitize


def parse_diagnostics(stdout: str, stderr: str) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for line in (stdout + "\n" + stderr).splitlines():
        if re.match(r"(?i)\s*WARNING:", line):
            warnings.append(sanitize(line))
        elif re.match(r"(?i)\s*(?:ERROR:|Parser error:|Can't open\b|Cannot open\b)", line):
            errors.append(sanitize(line))
    return errors, warnings


class ProcessRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def stop(self, process: subprocess.Popen[bytes]) -> None:
        with contextlib.suppress(psutil.Error):
            children = psutil.Process(process.pid).children(recursive=True)
            for child in reversed(children):
                with contextlib.suppress(psutil.Error):
                    child.kill()
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)

    def run(
        self,
        args: list[str],
        cwd: Path,
        timeout: float,
        output: Path | None = None,
        max_bytes: int | None = None,
    ) -> dict[str, Any]:
        started = time.monotonic()
        reason: str | None = None
        limit = max_bytes or self.settings.max_export_bytes
        with tempfile.TemporaryFile(dir=cwd) as out, tempfile.TemporaryFile(dir=cwd) as err:
            process = subprocess.Popen(
                args,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=err,
                shell=False,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            try:
                while process.poll() is None:
                    if time.monotonic() - started >= timeout:
                        reason = "Process timeout exceeded."
                    elif output and output.exists() and output.stat().st_size > limit:
                        reason = "Output file size limit exceeded."
                    elif (
                        max(os.fstat(out.fileno()).st_size, os.fstat(err.fileno()).st_size)
                        > self.settings.max_log_bytes
                    ):
                        reason = "Process log size limit exceeded."
                    if reason:
                        self.stop(process)
                        break
                    time.sleep(0.025)
            finally:
                if process.poll() is None:
                    self.stop(process)
            if output and output.exists() and output.stat().st_size > limit:
                reason = "Output file size limit exceeded."
            if (
                max(os.fstat(out.fileno()).st_size, os.fstat(err.fileno()).st_size)
                > self.settings.max_log_bytes
            ):
                reason = "Process log size limit exceeded."
            out.seek(0)
            err.seek(0)
            stdout = out.read(self.settings.max_log_bytes).decode("utf-8", errors="replace")
            stderr = err.read(self.settings.max_log_bytes).decode("utf-8", errors="replace")
        errors, warnings = parse_diagnostics(stdout, stderr)
        if reason:
            errors.append(reason)
        if process.returncode and not errors:
            errors.append(f"Process exited with code {process.returncode}.")
        if output and (not output.is_file() or output.stat().st_size == 0):
            errors.append("Output missing or empty; model may be empty.")
        result = {
            "success": not errors,
            "exit_code": process.returncode,
            "stdout": sanitize(stdout),
            "stderr": sanitize(stderr),
            "errors": errors,
            "warnings": warnings,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "timed_out": reason == "Process timeout exceeded.",
            "output_created": output.is_file() if output else None,
        }
        if errors and output:
            output.unlink(missing_ok=True)
        return result


class OpenSCADRunner(ProcessRunner):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._capabilities: dict[str, Any] | None = None

    def capabilities(self, cwd: Path) -> dict[str, Any]:
        if self._capabilities is None:
            path = discover_openscad()
            version = self.run([str(path), "--version"], cwd, 10)
            help_result = self.run([str(path), "--help"], cwd, 10)
            if not version["success"] or not help_result["success"]:
                raise DesignError("OpenSCAD capability probe failed.", "capability_probe_failed")
            help_text = help_result["stdout"] + help_result["stderr"]
            self._capabilities = {
                "path": str(path),
                "version": (version["stdout"] + version["stderr"]).strip(),
                "flags": sorted(set(re.findall(r"--[a-z][a-z-]+", help_text))),
                "formats": [
                    x
                    for x in ("stl", "3mf", "off", "amf", "dxf", "svg", "png")
                    if re.search(rf"\b{x}\b", help_text)
                ],
            }
        return self._capabilities

    def execute(
        self,
        source: Path,
        output: Path,
        timeout: float,
        options: list[str] | None = None,
        max_bytes: int | None = None,
    ) -> dict[str, Any]:
        caps = self.capabilities(source.parent)
        fmt = output.suffix.removeprefix(".")
        if fmt not in caps["formats"]:
            raise DesignError(
                f"Detected OpenSCAD does not advertise {fmt} export.", "unsupported_format"
            )
        return self.run(
            [
                caps["path"],
                "-o",
                os.path.relpath(output, source.parent),
                *(options or []),
                source.name,
            ],
            source.parent,
            timeout,
            output,
            max_bytes,
        )
