from pathlib import Path

import pytest

from openscad_design_mcp.config import discover_openscad
from openscad_design_mcp.errors import DesignError
from openscad_design_mcp.schemas import BuildVolume, Dimensions
from openscad_design_mcp.service import DesignService

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def require_openscad():
    try:
        discover_openscad()
    except DesignError:
        pytest.skip("OpenSCAD executable not installed")


def test_real_cube_workflow(settings):
    service = DesignService(settings)
    code = (Path(__file__).parent / "fixtures" / "cube.scad").read_text()
    created = service.create_project("Khối hộp Unicode", "", "20x20x10 mm", code)
    assert created.data["validation"]["success"], created.model_dump()
    result = service.finalize_model(
        created.project_id,
        expected_dimensions=Dimensions(x=20, y=20, z=10),
        build_volume=BuildVolume(x=220, y=220, z=250),
    )
    assert result.success, result.model_dump()
    assert result.data["steps"]["mesh"]["data"]["volume"] == pytest.approx(4000)
    assert len(result.artifacts) == 8
    assert all(Path(a["path"]).is_file() for a in result.artifacts)
    exported = service.export_model(created.project_id, "3mf")
    assert exported.success, exported.model_dump()
    mesh = service.inspect_mesh(created.project_id)
    assert mesh.success and mesh.data["watertight"], mesh.model_dump()


@pytest.mark.parametrize("code", ["cube([20,);", "difference(){cube(10);cube(10);}"])
def test_real_invalid_and_empty(settings, code):
    service = DesignService(settings)
    created = service.create_project("Invalid", "", "", code)
    assert created.success
    assert not created.data["validation"]["success"]


def test_real_status(settings):
    result = DesignService(settings).get_system_status()
    assert result.success, result.model_dump()
    assert result.data["render_available"]


@pytest.mark.parametrize(
    "fmt,code",
    [
        ("off", "cube(10);"),
        ("amf", "cube(10);"),
        ("dxf", "square([20,10]);"),
        ("svg", "square([20,10]);"),
    ],
)
def test_real_other_exports(settings, fmt, code):
    service = DesignService(settings)
    project = service.create_project("Export", "", "", code)
    result = service.export_model(project.project_id, fmt)
    assert result.success, result.model_dump()
    assert Path(result.data["path"]).stat().st_size > 0


def test_real_preview_fast_and_parallel(settings):
    service = DesignService(settings)
    code = (Path(__file__).parent / "fixtures" / "cube.scad").read_text()
    created = service.create_project("FastPreview", "", "", code)
    preview_set = service.render_preview_set(created.project_id)
    assert preview_set.success, preview_set.model_dump()
    assert len(preview_set.data["previews"]) == 6
    assert all(p["success"] for p in preview_set.data["previews"])


def test_real_mesh_inspection_cache(settings):
    service = DesignService(settings)
    code = (Path(__file__).parent / "fixtures" / "cube.scad").read_text()
    created = service.create_project("CacheTest", "", "", code)
    assert created.data["validation"]["success"]
    mesh1 = service.inspect_mesh(created.project_id)
    assert mesh1.success
    mesh2 = service.inspect_mesh(created.project_id)
    assert mesh2.success
    assert mesh2.data["volume"] == mesh1.data["volume"]


def test_real_repeated_finalize_and_revision_change(settings):
    service = DesignService(settings)
    created = service.create_project("Stability", "", "", "cube([20,20,10]);")
    pid = created.project_id
    for _ in range(3):
        result = service.finalize_model(pid, render_views=["front", "top"])
        assert result.success, result.model_dump()
        assert result.data["steps"]["mesh"]["data"]["dimensions"] == [20, 20, 10]
    service.update_model(pid, "cube([30,15,5]);", "Resize", 1)
    result = service.finalize_model(pid, render_views=["front", "top"])
    assert result.success, result.model_dump()
    assert result.data["steps"]["mesh"]["data"]["dimensions"] == [30, 15, 5]
    exported = service.export_model(pid, "3mf")
    assert exported.success
    assert not service.inspect_mesh(pid).data["cache_hit"]
