import pytest
import trimesh

from openscad_design_mcp.config import Settings
from openscad_design_mcp.service import DesignService
from openscad_design_mcp.workspace import Workspace


@pytest.fixture
def settings(tmp_path):
    return Settings(workspace=tmp_path / "không gian làm việc")


@pytest.fixture
def workspace(settings):
    return Workspace(settings)


@pytest.fixture
def project(workspace):
    return workspace.create("Cube", "Description", "20 x 20 x 10", "cube([20,20,10]);", "mm")


@pytest.fixture
def mesh_data():
    from openscad_design_mcp.mesh_inspector import analyze_mesh

    return analyze_mesh(trimesh.creation.box(extents=[20, 20, 10]))


@pytest.fixture
def service(settings, monkeypatch, mesh_data):
    service = DesignService(settings)

    def execute(source, output, timeout, options=None, max_bytes=None):
        if output.suffix == ".png":
            from PIL import Image

            size = next(x.split("=")[1] for x in options if x.startswith("--imgsize"))
            Image.new("RGB", tuple(map(int, size.split(","))), "white").save(output)
        else:
            trimesh.creation.box(extents=[20, 20, 10]).export(output, file_type="stl")
        return dict(
            success=True,
            errors=[],
            warnings=[],
            exit_code=0,
            stdout="",
            stderr="Total rendering time: 0",
            duration_ms=1,
            output_created=True,
        )

    monkeypatch.setattr(service.runner, "execute", execute)
    monkeypatch.setattr(
        service.runner,
        "capabilities",
        lambda cwd: {
            "path": "mock",
            "version": "mock",
            "formats": ["stl", "png", "3mf"],
            "flags": [
                "--imgsize",
                "--camera",
                "--viewall",
                "--autocenter",
                "--projection",
                "--colorscheme",
                "--render",
            ],
        },
    )
    monkeypatch.setattr(service, "_inspect", lambda path: mesh_data.copy())
    return service
