import numpy as np
import pytest
import trimesh

from openscad_design_mcp.mesh_inspector import analyze_mesh, inspect_mesh_file


def test_valid_cube(tmp_path):
    path = tmp_path / "khối hộp.stl"
    trimesh.creation.box(extents=[20, 20, 10]).export(path)
    result = inspect_mesh_file(path)
    assert result["dimensions"] == [20, 20, 10]
    assert result["volume"] == pytest.approx(4000)
    assert result["surface_area"] == pytest.approx(1600)
    assert result["watertight"] and result["winding_consistent"]
    assert result["components"] == 1 and result["euler_number"] == 2
    assert result["vertices"] == 8 and result["faces"] == 12
    assert not result["non_manifold_edges"] and not result["empty"]
    assert result["center_of_mass"] == [0, 0, 0]


def test_empty_mesh():
    result = analyze_mesh(trimesh.Trimesh())
    assert result["empty"]
    assert result["volume"] is None and result["dimensions"] is None
    assert "volume" in result["unavailable_reasons"]


def test_open_mesh_volume_unavailable():
    mesh = trimesh.creation.box()
    mesh.update_faces(np.arange(len(mesh.faces) - 1))
    result = analyze_mesh(mesh)
    assert not result["watertight"]
    assert result["volume"] is None
    assert result["boundary_edges"] > 0


def test_duplicate_degenerate_and_nonmanifold():
    box = trimesh.creation.box()
    mesh = trimesh.Trimesh(
        vertices=box.vertices, faces=np.vstack([box.faces, box.faces[0], [0, 0, 1]]), process=False
    )
    result = analyze_mesh(mesh)
    assert result["duplicate_faces"]
    assert result["degenerate_faces"]
    assert result["non_manifold_edges"]


def test_components():
    one = trimesh.creation.box()
    two = trimesh.creation.box()
    two.apply_translation([10, 0, 0])
    assert analyze_mesh(trimesh.util.concatenate([one, two]))["components"] == 2
