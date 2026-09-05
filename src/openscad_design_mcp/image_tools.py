import math
from pathlib import Path
from typing import Any

from PIL import Image

from .config import Settings
from .errors import DesignError
from .schemas import ColorScheme, Projection, View

CAMERAS = {
    "isometric": (55, 0, 45),
    "front": (90, 0, 0),
    "back": (90, 0, 180),
    "left": (90, 0, 90),
    "right": (90, 0, 270),
    "top": (0, 0, 0),
    "bottom": (180, 0, 0),
}
DEFAULT_VIEWS: list[View] = ["isometric", "front", "right", "back", "left", "top"]


def preview_options(
    settings: Settings,
    flags: list[str],
    width: int,
    height: int,
    view: View,
    camera: list[float] | None,
    projection: Projection,
    colorscheme: ColorScheme,
) -> tuple[list[str], list[str]]:
    if (
        not 16 <= width <= settings.max_preview_dimension
        or not 16 <= height <= settings.max_preview_dimension
    ):
        raise DesignError("Preview dimensions must be between 16 and configured maximum.")
    if camera is not None and view != "custom":
        raise DesignError("camera requires view='custom'.")
    if view == "custom":
        if (
            camera is None
            or len(camera) not in (6, 7)
            or not all(math.isfinite(v) and abs(v) <= 1e9 for v in camera)
        ):
            raise DesignError("Custom camera requires 6 or 7 finite numeric values.")
        if len(camera) == 7 and camera[-1] <= 0:
            raise DesignError("Camera distance must be positive.")
        values = camera
    else:
        values = [0, 0, 0, *CAMERAS[view], 100]
    required = ("--imgsize", "--camera", "--projection")
    if any(flag not in flags for flag in required):
        raise DesignError("OpenSCAD lacks required preview flags: " + ", ".join(required))
    options = [
        f"--imgsize={width},{height}",
        "--camera=" + ",".join(map(str, values)),
        "--projection=" + ("o" if projection == "orthographic" else "p"),
    ]
    warnings = []
    for flag in ("--viewall", "--autocenter") if view != "custom" else ():
        if flag in flags:
            options.append(flag)
        else:
            warnings.append(f"{flag} unavailable; model may not fit the frame.")
    if "--colorscheme" in flags:
        options.append(f"--colorscheme={colorscheme}")
    else:
        warnings.append("--colorscheme unavailable; using OpenSCAD default colors.")
    if "--render" in flags:
        options.append("--render")
    else:
        warnings.append("Full geometry PNG rendering unavailable; using preview renderer.")
    return options, warnings


def inspect_png(path: Path, width: int, height: int, max_bytes: int) -> dict[str, Any]:
    if not path.is_file() or not 0 < path.stat().st_size <= max_bytes:
        raise DesignError("PNG missing, empty or oversized.")
    with Image.open(path) as img:
        if img.format != "PNG" or img.size != (width, height):
            raise DesignError("Invalid PNG format or unexpected dimensions.")
        img.verify()
    with Image.open(path) as img:
        img.load()
    return {"width": width, "height": height, "format": "PNG", "bytes": path.stat().st_size}
