import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from .errors import sanitize


def inspect_mesh_file(path: Path) -> dict[str, Any]:
    mesh = trimesh.load_mesh(path, process=False)
    if isinstance(mesh, trimesh.Scene):
        mesh = mesh.to_mesh()
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError("Export did not contain a triangle mesh.")
    return analyze_mesh(mesh)


def analyze_mesh(mesh: trimesh.Trimesh) -> dict[str, Any]:
    result: dict[str, Any] = {"empty": bool(mesh.is_empty), "unavailable_reasons": {}}
    names = [
        "bounds_min",
        "bounds_max",
        "dimensions",
        "volume",
        "surface_area",
        "vertices",
        "faces",
        "components",
        "watertight",
        "winding_consistent",
        "euler_number",
        "degenerate_faces",
        "duplicate_faces",
        "non_manifold_edges",
        "boundary_edges",
        "center_of_mass",
    ]
    if mesh.is_empty:
        result.update(dict.fromkeys(names))
        result.update(vertices=0, faces=0, components=0)
        result["unavailable_reasons"] = {n: "Mesh is empty." for n in names if result[n] is None}
        return result
    mesh = mesh.copy()
    mesh.merge_vertices()
    calculations = {
        "bounds_min": lambda: mesh.bounds[0].tolist(),
        "bounds_max": lambda: mesh.bounds[1].tolist(),
        "dimensions": lambda: mesh.extents.tolist(),
        "surface_area": lambda: float(mesh.area),
        "vertices": lambda: int(len(mesh.vertices)),
        "faces": lambda: int(len(mesh.faces)),
        "components": lambda: int(len(mesh.split(only_watertight=False))),
        "watertight": lambda: bool(mesh.is_watertight),
        "winding_consistent": lambda: bool(mesh.is_winding_consistent),
        "euler_number": lambda: int(mesh.euler_number),
        "degenerate_faces": lambda: bool(not mesh.nondegenerate_faces().all()),
        "duplicate_faces": lambda: bool(not mesh.unique_faces().all()),
        "non_manifold_edges": lambda: bool((np.bincount(mesh.edges_unique_inverse) > 2).any()),
        "boundary_edges": lambda: int((np.bincount(mesh.edges_unique_inverse) == 1).sum()),
        "volume": lambda: (
            float(mesh.volume) if mesh.is_watertight and mesh.is_winding_consistent else None
        ),
        "center_of_mass": lambda: mesh.center_mass.tolist() if mesh.is_volume else None,
    }
    for name, calculate in calculations.items():
        try:
            value = calculate()
            flat = value if isinstance(value, list) else [value]
            if value is None or any(isinstance(v, float) and not math.isfinite(v) for v in flat):
                result[name] = None
                result["unavailable_reasons"][name] = (
                    "Metric undefined or mesh is not a closed oriented volume."
                )
            else:
                result[name] = value
        except Exception as exc:
            result[name] = None
            result["unavailable_reasons"][name] = sanitize(str(exc)) or type(exc).__name__
    return result


def main() -> None:
    try:
        result = inspect_mesh_file(Path(sys.argv[1]))
        Path(sys.argv[2]).write_text(json.dumps(result, allow_nan=False), encoding="utf-8")
    except Exception as exc:
        sys.stderr.write("ERROR: " + sanitize(str(exc)))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
