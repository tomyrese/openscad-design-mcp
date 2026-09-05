from pathlib import Path
from unittest.mock import Mock

import pytest

from openscad_design_mcp.errors import DesignError


def create(service):
    return service.create_project("Cache", "", "", "cube(10);").project_id


def test_validation_populates_cache_and_reuses_geometry(service, monkeypatch):
    pid = create(service)
    execute = Mock(side_effect=AssertionError("Unexpected OpenSCAD execution"))
    inspect = Mock(side_effect=AssertionError("Unexpected inspection"))
    monkeypatch.setattr(service.runner, "execute", execute)
    monkeypatch.setattr(service, "_inspect", inspect)
    assert service.validate_scad(pid).data["cache_hit"]
    assert service.export_model(pid).data["cache_hit"]
    assert service.inspect_mesh(pid).data["cache_hit"]
    assert not execute.called and not inspect.called


def test_cache_cannot_hide_source_corruption(service):
    pid = create(service)
    source = service.workspace.source(pid)
    source.write_text("cube(99);", encoding="utf-8")
    for action in (service.validate_scad, service.inspect_mesh, service.export_model):
        with pytest.raises(DesignError, match="checksum"):
            action(pid)


def test_failed_validation_is_retried(service, monkeypatch):
    pid = create(service)
    service.update_model(pid, "cube(11);", "edit", 1)
    original = service.runner.execute
    execute = Mock(
        return_value=dict(
            success=False,
            errors=["Process timeout exceeded."],
            warnings=[],
            exit_code=-1,
        )
    )
    monkeypatch.setattr(service.runner, "execute", execute)
    assert not service.validate_scad(pid).success
    monkeypatch.setattr(service.runner, "execute", original)
    retried = service.validate_scad(pid)
    assert retried.success and not retried.data["cache_hit"]


def test_update_and_restore_invalidate_geometry(service):
    pid = create(service)
    service.update_model(pid, "cube(12);", "edit", 1)
    meta = service.workspace.metadata(pid)
    assert meta["last_inspection"] is None and meta["validation_export"] is None
    assert not service.validate_scad(pid).data["cache_hit"]
    service.restore_version(pid, 1, 2)
    assert not service.validate_scad(pid).data["cache_hit"]


@pytest.mark.parametrize("damage", ["missing", "changed"])
def test_damaged_artifact_invalidates_cached_validation(service, monkeypatch, damage):
    pid = create(service)
    path = Path(service.workspace.metadata(pid)["validation_export"]["path"])
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"corrupted")
    execute = Mock(wraps=service.runner.execute)
    monkeypatch.setattr(service.runner, "execute", execute)
    assert service.validate_scad(pid).success
    assert execute.call_count == 1


def test_inspection_cache_matches_actual_export(service, monkeypatch):
    pid = create(service)
    result = service.export_model(pid, "3mf")
    path = Path(result.data["path"])
    path.write_bytes(path.read_bytes() + b"different-export")
    meta = service.workspace.metadata(pid)
    meta["last_export"]["sha256"] = service._artifact(path, 1, "export")["sha256"]
    service.workspace.save_metadata(meta)
    inspect = Mock(wraps=service._inspect)
    monkeypatch.setattr(service, "_inspect", inspect)
    assert not service.inspect_mesh(pid).data["cache_hit"]
    assert inspect.call_count == 1
    assert service.inspect_mesh(pid).data["cache_hit"]


def test_legacy_cache_without_provenance_is_rebuilt(service, monkeypatch):
    pid = create(service)
    meta = service.workspace.metadata(pid)
    meta["last_validation"].pop("source_key")
    service.workspace.save_metadata(meta)
    execute = Mock(wraps=service.runner.execute)
    monkeypatch.setattr(service.runner, "execute", execute)
    assert not service.validate_scad(pid).data["cache_hit"]
    assert execute.call_count == 1


def test_cache_hit_preserves_warnings(service):
    pid = create(service)
    meta = service.workspace.metadata(pid)
    meta["last_validation"]["warnings"] = ["WARNING: test"]
    service.workspace.save_metadata(meta)
    assert service.validate_scad(pid).warnings == ["WARNING: test"]


def test_compiler_identity_change_invalidates_cache(service, monkeypatch):
    pid = create(service)
    original = service.runner.capabilities
    monkeypatch.setattr(
        service.runner,
        "capabilities",
        lambda cwd: {
            **original(cwd),
            "version": "new compiler",
        },
    )
    assert not service.validate_scad(pid).data["cache_hit"]
