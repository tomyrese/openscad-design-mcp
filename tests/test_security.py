import os
import sys
from pathlib import Path

import pytest

from openscad_design_mcp.config import Settings, discover_openscad
from openscad_design_mcp.errors import DesignError, sanitize
from openscad_design_mcp.openscad_runner import ProcessRunner
from openscad_design_mcp.workspace import check_code


@pytest.mark.parametrize(
    "pid",
    [
        "../escape",
        "..\\escape",
        "/tmp/escape",
        "C:\\Windows",
        "C:relative",
        "\\\\server\\share",
        "a" * 31,
        "A" * 32,
        "a" * 32 + "/../x",
        "CON",
    ],
)
def test_reject_invalid_project_id(workspace, pid):
    with pytest.raises(DesignError):
        workspace.project(pid)


def test_code_limit():
    with pytest.raises(DesignError, match="exceeds"):
        check_code('echo("ế");', 10)


@pytest.mark.parametrize(
    "code",
    [
        "include <../../secret>; cube(1);",
        "use <lib.scad>",
        'import("C:/secret.stl");',
        'surface(file=str("/", "secret"));',
        'import /* gap */ ("x.stl");',
    ],
)
def test_external_file_reads_blocked(code):
    with pytest.raises(DesignError, match="External file"):
        check_code(code, 10000)


def test_strings_and_comments_do_not_trigger_filter():
    check_code('echo("import"); cube(1); // include\n/* use */', 1000)


def test_symlink_escape(workspace, project, tmp_path):
    target = tmp_path / "outside"
    target.mkdir()
    link = workspace.project(project["project_id"]) / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Windows symlink privilege unavailable; junction coverage is separate")
    with pytest.raises(DesignError, match="Symlinks"):
        workspace.safe(link / "secret.txt")


@pytest.mark.skipif(os.name != "nt", reason="Windows junction test")
def test_junction_escape(workspace, project, tmp_path):
    import subprocess

    target = tmp_path / "outside"
    target.mkdir()
    link = workspace.project(project["project_id"]) / "junction"
    script = "New-Item -ItemType Junction -Path $env:TEST_LINK -Target $env:TEST_TARGET | Out-Null"
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        check=True,
        env={**os.environ, "TEST_LINK": str(link), "TEST_TARGET": str(target)},
        timeout=15,
    )
    try:
        with pytest.raises(DesignError):
            workspace.safe(link / "secret.txt")
    finally:
        if link.exists():
            link.rmdir()


def test_timeout_kills_process(settings, tmp_path):
    result = ProcessRunner(settings).run(
        [sys.executable, "-c", "import time; time.sleep(30)"], tmp_path, 0.1
    )
    assert not result["success"]
    assert result["timed_out"]
    assert result["duration_ms"] < 5000


def test_output_limit(settings, tmp_path):
    output = tmp_path / "out.bin"
    script = "from pathlib import Path; Path('out.bin').write_bytes(b'x'*10000)"
    result = ProcessRunner(settings).run([sys.executable, "-c", script], tmp_path, 5, output, 100)
    assert not result["success"]
    assert not output.exists()


def test_log_limit(settings, tmp_path):
    runner = ProcessRunner(settings.model_copy(update={"max_log_bytes": 100}))
    result = runner.run([sys.executable, "-c", "print('x'*10000)"], tmp_path, 5)
    assert not result["success"]
    assert "log size" in " ".join(result["errors"])


def test_missing_openscad(monkeypatch):
    monkeypatch.delenv("OPENSCAD_PATH", raising=False)
    monkeypatch.setattr("openscad_design_mcp.config.shutil.which", lambda name: None)
    monkeypatch.setattr(Path, "is_file", lambda path: False)
    with pytest.raises(DesignError, match="OPENSCAD_PATH"):
        discover_openscad()


def test_openscad_env_precedence(monkeypatch, tmp_path):
    executable = tmp_path / "OpenSCAD Unicode ế.exe"
    executable.touch()
    monkeypatch.setenv("OPENSCAD_PATH", str(executable))
    assert discover_openscad() == executable.resolve()


def test_sanitizer():
    result = sanitize("\x1b[31mERROR\x00 C:\\Users\\private\\file.scad:12")
    assert "\x1b" not in result and "\x00" not in result
    assert "private" not in result
    assert ":12" in result


def test_settings_env(monkeypatch, tmp_path):
    monkeypatch.setenv("OPENSCAD_MCP_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("OPENSCAD_MCP_VALIDATE_TIMEOUT", "2")
    assert Settings.from_env().validate_timeout == 2
