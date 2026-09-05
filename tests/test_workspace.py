import re
from concurrent.futures import ThreadPoolExecutor

import pytest

from openscad_design_mcp.errors import DesignError
from openscad_design_mcp.server import guarded
from openscad_design_mcp.workspace import checksum


def test_create(workspace, project):
    pid = project["project_id"]
    assert re.fullmatch(r"[0-9a-f]{32}", pid)
    assert project["current_version"] == 1
    assert workspace.source(pid).read_text() == "cube([20,20,10]);"
    assert workspace.versions(pid)[0]["checksum"] == checksum("cube([20,20,10]);")
    assert workspace.create("Cube", "", "", "cube(1);", "mm")["project_id"] != pid


def test_windows_line_endings_have_stable_checksum(workspace):
    meta = workspace.create("CRLF", "", "", "cube(1);\r\necho(2);\r\n", "mm")
    pid = meta["project_id"]
    assert workspace.source(pid).read_bytes() == b"cube(1);\necho(2);\n"
    workspace.update(pid, "cube(2);\r\n", "CRLF update", 1)
    assert workspace.source(pid).read_bytes() == b"cube(2);\n"
    assert workspace.versions(pid)[-1]["checksum"] == checksum("cube(2);\n")


def test_update_conflict_and_restore(service):
    created = service.create_project("Cube", "", "", "cube(1);")
    pid = created.project_id
    assert service.update_model(pid, "cube(2);", "Grow", 1).data["version"] == 2
    with pytest.raises(DesignError, match="Version conflict"):
        service.update_model(pid, "cube(3);", "Stale", 1)
    assert service.restore_version(pid, 1, 2).data["version"] == 3
    assert service.read_model(pid).data["scad_code"] == "cube(1);"
    assert len(service.list_versions(pid).data["versions"]) == 3


def test_atomic_failure_keeps_old_file(workspace, project, monkeypatch):
    import openscad_design_mcp.workspace as module

    path = workspace.project(project["project_id"]) / "current" / "model.scad"
    old = path.read_bytes()

    def fail(*args):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(module.os, "replace", fail)
    with pytest.raises(OSError):
        workspace.atomic(path, "new")
    assert path.read_bytes() == old
    assert list(path.parent.glob(".write-*")) == []


def test_update_rolls_back_on_metadata_failure(workspace, project, monkeypatch):
    pid = project["project_id"]

    def fail(*args):
        raise OSError("metadata commit failure")

    monkeypatch.setattr(workspace, "save_metadata", fail)
    with pytest.raises(OSError):
        workspace.update(pid, "cube(2);", "Grow", 1)
    assert workspace.metadata(pid)["current_version"] == 1
    assert not (workspace.project(pid) / "versions" / "2").exists()
    assert (workspace.project(pid) / "current" / "model.scad").read_text() == "cube([20,20,10]);"


def test_current_repair_and_checksum(workspace, project):
    pid = project["project_id"]
    current = workspace.project(pid) / "current" / "model.scad"
    current.write_text("corrupted", encoding="utf-8")
    source = workspace.source(pid)
    assert current.read_text() == source.read_text()
    source.write_text("cube(99);", encoding="utf-8")
    with pytest.raises(DesignError, match="checksum"):
        workspace.source(pid)


def test_delete_confirmation_and_trash(workspace, project):
    pid = project["project_id"]
    with pytest.raises(DesignError):
        workspace.delete(pid, "wrong")
    trash = workspace.delete(pid, pid)
    assert (trash / "project.json").is_file()
    assert not (workspace.root / "projects" / pid).exists()


def test_concurrent_updates_only_one_commits(service):
    pid = service.create_project("Cube", "", "", "cube(1);").project_id
    update = guarded(service, service.update_model)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda n: update(pid, f"cube({n});", "Edit", 1), [2, 3]))
    assert sum(result.success for result in results) == 1
    assert service.workspace.metadata(pid)["current_version"] == 2


def test_versions_are_immutable_and_status_reset(service):
    pid = service.create_project("Cube", "", "", "cube(1);").project_id
    assert service.finalize_model(pid, render_views=["front"]).success
    source = service.workspace.source(pid)
    original = source.read_bytes()
    service.update_model(pid, "cube(2);", "change", 1)
    assert source.read_bytes() == original
    meta = service.workspace.metadata(pid)
    assert meta["status"] == "draft"
    assert all(meta[key] is None for key in ("last_validation", "last_report", "last_export"))
