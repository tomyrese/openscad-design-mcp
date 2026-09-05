from pathlib import Path

import pytest
from PIL import Image

from openscad_design_mcp.errors import DesignError
from openscad_design_mcp.image_tools import inspect_png, preview_options
from openscad_design_mcp.openscad_runner import parse_diagnostics
from openscad_design_mcp.schemas import BuildVolume, Dimensions
from openscad_design_mcp.server import guarded
from openscad_design_mcp.validation import compare, printability


def test_diagnostics():
    errors, warnings = parse_diagnostics(
        "ECHO: hello", "Total rendering time: 0\nWARNING: issue\nERROR: syntax"
    )
    assert errors == ["ERROR: syntax"]
    assert warnings == ["WARNING: issue"]


def test_echo_is_not_a_diagnostic():
    errors, warnings = parse_diagnostics(
        'ECHO: "no error, no warning"',
        "WARNING: Can't open include file\nGeometries in cache: 1",
    )
    assert errors == []
    assert warnings == ["WARNING: Can't open include file"]


def test_compare_dimensions():
    result = compare([20.15, 19, 10], Dimensions(x=20, y=None, z=10), 0.1, 1)
    assert result["passed"]
    assert result["axes"]["y"]["skipped"]
    assert not compare([21, 20, 10], Dimensions(x=20), 0.1)["passed"]
    assert not compare(None, Dimensions(x=20), 0.1)["passed"]


@pytest.mark.parametrize("value", [-1, float("nan"), float("inf")])
def test_bad_tolerance(value):
    with pytest.raises(DesignError):
        compare([1, 1, 1], Dimensions(x=1), value)


def test_printability(mesh_data):
    result = printability(mesh_data, BuildVolume(x=220, y=220, z=250))
    assert result["passed"]
    assert "wall_thickness" in result["unknown"]
    assert not printability(mesh_data, BuildVolume(x=5, y=220, z=250))["passed"]
    assert not printability({**mesh_data, "volume": 0}, None)["passed"]
    assert not printability({**mesh_data, "components": 2}, None)["passed"]


def test_finalize_success_and_failure(service):
    pid = service.create_project("Cube", "", "", "cube([20,20,10]);").project_id
    good = service.finalize_model(pid, expected_dimensions=Dimensions(x=20, y=20, z=10))
    assert good.success and good.data["finalized"]
    assert len(good.data["steps"]["previews"]["data"]["previews"]) == 6
    assert service.workspace.metadata(pid)["status"] == "finalized"
    bad = service.finalize_model(pid, expected_dimensions=Dimensions(x=99), render_views=["front"])
    assert not bad.success and not bad.data["finalized"]
    assert bad.data["suggested_actions"]
    assert service.workspace.metadata(pid)["status"] == "needs_changes"
    assert any(a["kind"] == "report" and Path(a["path"]).exists() for a in bad.artifacts)


def test_finalize_failed_stage_still_records_report(service, monkeypatch):
    pid = service.create_project("Cube", "", "", "cube(1);").project_id

    def fail(project_id):
        raise DesignError("OpenSCAD unavailable")

    monkeypatch.setattr(service, "validate_scad", fail)
    result = service.finalize_model(pid, render_views=["front"])
    assert not result.success and result.data["steps"]["export"]["success"]
    assert "OpenSCAD unavailable" in " ".join(result.errors)


def test_preview_set_partial_failure(service, monkeypatch):
    pid = service.create_project("Cube", "", "", "cube(1);").project_id
    original = service.render_preview

    def render(*args, **kwargs):
        if kwargs.get("view") == "front":
            raise DesignError("front render failed")
        return original(*args, **kwargs)

    monkeypatch.setattr(service, "render_preview", render)
    result = service.render_preview_set(pid, ["front", "top"])
    assert not result.success and len(result.artifacts) == 1
    assert result.data["previews"][1]["success"]


def test_no_openscad_project_still_saved(settings, monkeypatch):
    from openscad_design_mcp.service import DesignService

    service = DesignService(settings)

    def fail(*args):
        raise DesignError("Configure OPENSCAD_PATH")

    monkeypatch.setattr(service.runner, "capabilities", fail)
    result = service.create_project("Cube", "", "", "cube(1);")
    assert result.success and not result.data["validation"]["success"]
    assert service.read_model(result.project_id).success
    status = service.get_system_status()
    assert not status.success and status.data["python"]


def test_envelope_on_error(service):
    result = guarded(service, service.read_model)("../../evil")
    assert not result.success and result.tool == "read_model"
    assert result.data["error_code"] == "invalid_project_id"
    assert "Traceback" not in str(result.model_dump())


def test_png_and_camera(settings, tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (32, 32)).save(path)
    assert inspect_png(path, 32, 32, 10000)["format"] == "PNG"
    with pytest.raises(DesignError):
        inspect_png(path, 100, 100, 10000)
    flags = ["--camera", "--imgsize", "--projection"]
    options, warnings = preview_options(
        settings, flags, 32, 32, "top", None, "orthographic", "Cornfield"
    )
    assert warnings and "--camera=0,0,0,0,0,0,100" in options
    with pytest.raises(DesignError):
        preview_options(settings, flags, 5000, 32, "front", None, "orthographic", "Cornfield")
    with pytest.raises(DesignError):
        preview_options(settings, [], 32, 32, "front", None, "orthographic", "Cornfield")
    with pytest.raises(DesignError):
        preview_options(settings, flags, 32, 32, "custom", [0, 1], "orthographic", "Cornfield")


def test_empty_preview_set_cannot_finalize(service):
    pid = service.create_project("Cube", "", "", "cube(1);").project_id
    with pytest.raises(DesignError):
        service.finalize_model(pid, render_views=[])


def test_export_format_rejected_before_cli(service):
    with pytest.raises(DesignError):
        service.export_model("bad-id", "stl --evil")
