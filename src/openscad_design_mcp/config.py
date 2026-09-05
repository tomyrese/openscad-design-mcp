import os
import shutil
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from .errors import DesignError


class Settings(BaseModel):
    model_config = ConfigDict(frozen=True)
    workspace: Path = Field(default_factory=lambda: Path.cwd() / "workspace")
    validate_timeout: float = Field(default=30, gt=0, le=3600)
    preview_timeout: float = Field(default=60, gt=0, le=3600)
    export_timeout: float = Field(default=180, gt=0, le=3600)
    inspect_timeout: float = Field(default=60, gt=0, le=3600)
    lock_timeout: float = Field(default=10, gt=0, le=60)
    max_code_bytes: int = Field(default=2 * 1024 * 1024, gt=0)
    max_preview_dimension: int = Field(default=4096, ge=16, le=4096)
    max_previews: int = Field(default=12, ge=1, le=12)
    max_export_bytes: int = Field(default=500 * 1024 * 1024, gt=0)
    max_image_bytes: int = Field(default=64 * 1024 * 1024, gt=0)
    max_log_bytes: int = Field(default=1024 * 1024, gt=0)

    @classmethod
    def from_env(cls) -> "Settings":
        values = {
            name: os.environ[f"OPENSCAD_MCP_{name.upper()}"]
            for name in cls.model_fields
            if f"OPENSCAD_MCP_{name.upper()}" in os.environ
        }
        return cls.model_validate(values)


def discover_openscad() -> Path:
    candidates = [
        os.environ.get("OPENSCAD_PATH"),
        shutil.which("openscad"),
        shutil.which("openscad.exe"),
        r"C:\Program Files\OpenSCAD\openscad.exe",
        r"C:\Program Files (x86)\OpenSCAD\openscad.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    raise DesignError(
        "OpenSCAD not found. Install OpenSCAD and set OPENSCAD_PATH to the full executable "
        "path, for example C:\\Program Files\\OpenSCAD\\openscad.exe.",
        "openscad_not_found",
    )
