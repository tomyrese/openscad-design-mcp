from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

View = Literal["isometric", "front", "back", "left", "right", "top", "bottom", "custom"]
Format = Literal["stl", "3mf", "off", "amf", "dxf", "svg"]
Projection = Literal["orthographic", "perspective"]
ColorScheme = Literal[
    "Cornfield",
    "Metallic",
    "Sunset",
    "Starnight",
    "BeforeDawn",
    "Nature",
    "DeepOcean",
    "Solarized",
    "Tomorrow",
    "Tomorrow Night",
    "Monotone",
]


class Dimensions(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    x: float | None = Field(default=None, gt=0)
    y: float | None = Field(default=None, gt=0)
    z: float | None = Field(default=None, gt=0)


class BuildVolume(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    x: float = Field(gt=0)
    y: float = Field(gt=0)
    z: float = Field(gt=0)


class Response(BaseModel):
    success: bool = True
    tool: str
    project_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    duration_ms: int = 0
