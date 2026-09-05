import functools
import inspect
import logging
import time
from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP
from filelock import Timeout

from .config import Settings
from .errors import DesignError, sanitize
from .schemas import Response
from .service import DesignService

TOOL_NAMES = (
    "get_system_status",
    "create_project",
    "list_projects",
    "get_project",
    "read_model",
    "update_model",
    "validate_scad",
    "render_preview",
    "render_preview_set",
    "export_model",
    "inspect_mesh",
    "compare_dimensions",
    "check_printability",
    "finalize_model",
    "list_versions",
    "restore_version",
    "delete_project",
)


def guarded(service: DesignService, method: Callable[..., Response]) -> Callable[..., Response]:
    @functools.wraps(method)
    def call(*args: Any, **kwargs: Any) -> Response:
        started = time.monotonic()
        project_id = kwargs.get("project_id")
        try:
            bound = inspect.signature(method).bind(*args, **kwargs)
            project_id = bound.arguments.get("project_id")
            with service.workspace.lock:
                response = method(*args, **kwargs)
        except Exception as exc:
            code = (
                exc.code
                if isinstance(exc, DesignError)
                else ("workspace_busy" if isinstance(exc, Timeout) else "operation_failed")
            )
            message = (
                "Workspace busy; retry later." if isinstance(exc, Timeout) else sanitize(str(exc))
            )
            response = Response(
                success=False,
                tool=method.__name__,
                project_id=project_id,
                data={"error_code": code},
                errors=[message or type(exc).__name__],
            )
        response.duration_ms = round((time.monotonic() - started) * 1000)
        return response

    return call


def create_server(settings: Settings | None = None) -> FastMCP:
    service = DesignService(settings or Settings.from_env())
    server = FastMCP(
        "openscad-design-mcp",
        instructions=(
            "Manage trusted OpenSCAD source and versioned artifacts. "
            "Use expected_version for edits. Inspect the structured success flag and errors; "
            "only finalize_model can mark a revision finalized. "
            "No internal AI loop. All dimensional arguments use project units."
        ),
    )
    for name in TOOL_NAMES:
        method = getattr(service, name)
        server.tool(guarded(service, method), name=name, description=method.__doc__)
    return server


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    create_server().run(transport="stdio", show_banner=False)
