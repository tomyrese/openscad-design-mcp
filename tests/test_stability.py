import sys
import threading
import time

import psutil

from openscad_design_mcp.openscad_runner import OpenSCADRunner, ProcessRunner


def test_parallel_preview_bound_and_order(service, monkeypatch):
    pid = service.create_project("Parallel", "", "", "cube(1);").project_id
    service.settings = service.settings.model_copy(update={"preview_workers": 2})
    original = service.render_preview
    active = peak = 0
    lock = threading.Lock()

    def render(*args, **kwargs):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        try:
            time.sleep(0.02 if kwargs["view"] == "front" else 0.01)
            return original(*args, **kwargs)
        finally:
            with lock:
                active -= 1

    monkeypatch.setattr(service, "render_preview", render)
    views = ["front", "top", "right", "front", "left", "back"]
    result = service.render_preview_set(pid, views)
    assert result.success and peak == 2
    assert [r["data"]["view"] for r in result.data["previews"]] == views
    assert len({a["path"] for a in result.artifacts}) == len(views)


def test_many_revisions_have_no_stale_cache(service):
    pid = service.create_project("Repeat", "", "", "cube(1);").project_id
    for version in range(1, 21):
        if version > 1:
            service.update_model(pid, f"cube({version});", "iteration", version - 1)
        result = service.finalize_model(pid, render_views=["top"])
        assert result.success and result.data["version"] == version
        for step in ("validation", "mesh", "export"):
            assert result.data["steps"][step]["data"]["version"] == version
    assert len(service.list_versions(pid).data["versions"]) == 20
    assert not list(service.workspace.root.rglob(".write-*"))
    assert not list((service.workspace.root / ".tmp").iterdir())


def test_capability_cache_reprobes_changed_executable(settings, tmp_path, monkeypatch):
    executable = tmp_path / "openscad.exe"
    executable.write_bytes(b"first")
    monkeypatch.setenv("OPENSCAD_PATH", str(executable))
    runner = OpenSCADRunner(settings)
    calls = []

    def run(args, cwd, timeout):
        calls.append(args)
        return {"success": True, "stdout": "--imgsize --camera stl png", "stderr": ""}

    monkeypatch.setattr(runner, "run", run)
    runner.capabilities(tmp_path)
    runner.capabilities(tmp_path)
    assert len(calls) == 2
    executable.write_bytes(b"replacement compiler")
    runner.capabilities(tmp_path)
    assert len(calls) == 4


def test_timeout_stops_child_process(settings, tmp_path):
    pid_file = tmp_path / "child.pid"
    script = (
        "import subprocess,sys,time,pathlib; "
        "p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']); "
        "pathlib.Path('child.pid').write_text(str(p.pid)); time.sleep(30)"
    )
    result = ProcessRunner(settings).run([sys.executable, "-c", script], tmp_path, 1)
    assert result["timed_out"]
    assert pid_file.exists()
    child_pid = int(pid_file.read_text())
    deadline = time.monotonic() + 3
    while psutil.pid_exists(child_pid) and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not psutil.pid_exists(child_pid)
