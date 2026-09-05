import math
from typing import Any

from .errors import DesignError
from .schemas import BuildVolume, Dimensions


def compare(
    actual: list[float] | None,
    expected: Dimensions,
    tolerance: float,
    percent_tolerance: float | None = None,
) -> dict[str, Any]:
    if not math.isfinite(tolerance) or tolerance < 0:
        raise DesignError("Tolerance must be finite and nonnegative.")
    if percent_tolerance is not None and (
        not math.isfinite(percent_tolerance) or percent_tolerance < 0
    ):
        raise DesignError("Percentage tolerance must be finite and nonnegative.")
    axes: dict[str, Any] = {}
    for i, axis in enumerate(("x", "y", "z")):
        target = getattr(expected, axis)
        measured = actual[i] if actual else None
        allowed = max(tolerance, target * (percent_tolerance or 0) / 100) if target else None
        delta = measured - target if measured is not None and target is not None else None
        axes[axis] = {
            "target": target,
            "actual": measured,
            "deviation": delta,
            "allowed_deviation": allowed,
            "skipped": target is None,
            "passed": None if target is None else delta is not None and abs(delta) <= allowed,
        }
    return {
        "passed": all(v["passed"] is True for v in axes.values() if not v["skipped"]),
        "axes": axes,
        "tolerance_rule": "max(absolute, target * percent / 100)",
    }


def printability(
    mesh: dict[str, Any],
    build: BuildVolume | None,
    require_watertight: bool = True,
    units: str = "mm",
) -> dict[str, Any]:
    scale = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4}[units]
    dimensions = mesh.get("dimensions")
    mm = [v * scale for v in dimensions] if dimensions else None
    checks: dict[str, bool] = {
        "nonempty": mesh.get("empty") is False,
        "valid_dimensions": bool(mm and all(math.isfinite(v) and v > 0 for v in mm)),
        "single_component": mesh.get("components") == 1,
        "no_degenerate_faces": mesh.get("degenerate_faces") is False,
        "no_duplicate_faces": mesh.get("duplicate_faces") is False,
        "no_non_manifold_edges": mesh.get("non_manifold_edges") is False,
        "consistent_winding": mesh.get("winding_consistent") is True,
    }
    if require_watertight:
        checks["watertight"] = mesh.get("watertight") is True
        checks["positive_volume"] = mesh.get("volume") is not None and mesh["volume"] > 0
    elif mesh.get("volume") is not None:
        checks["positive_volume"] = mesh["volume"] > 0
    if build:
        checks["fits_build_volume"] = bool(
            dimensions
            and all(
                value <= getattr(build, axis)
                for value, axis in zip(dimensions, ("x", "y", "z"), strict=True)
            )
        )
    warnings = []
    if mm and min(mm) < 0.1:
        warnings.append("Heuristic: an overall dimension is smaller than 0.1 mm.")
    if mm and max(mm) > 10000:
        warnings.append("Heuristic: bounding box exceeds 10 metres; verify units.")
    if not require_watertight and mesh.get("watertight") is not True:
        warnings.append(
            "Open mesh accepted by policy; enclosed volume and printability are uncertain."
        )
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "warnings": warnings,
        "dimensions": dimensions,
        "dimensions_mm": mm,
        "unknown": {
            key: "Not evaluated; requires a dedicated algorithm or manual review."
            for key in (
                "wall_thickness",
                "supports",
                "overhangs",
                "assembly_clearance",
                "self_intersections",
            )
        },
        "build_volume_policy": "Axis-aligned extents after translation; no rotation search.",
    }
