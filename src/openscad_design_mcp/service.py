import hashlib
import importlib.metadata
import json
import platform
import sys
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .config import Settings
from .errors import DesignError, sanitize
from .image_tools import DEFAULT_VIEWS, inspect_png, preview_options
from .openscad_runner import OpenSCADRunner, ProcessRunner
from .schemas import (
    BuildVolume,
    ColorScheme,
    Dimensions,
    Format,
    Projection,
    RenderMode,
    Response,
    View,
)
from .validation import compare, printability
from .workspace import Workspace, utc_now


class DesignService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.workspace = Workspace(settings)
        self.runner = OpenSCADRunner(settings)
        self.process = ProcessRunner(settings)

    def _result(
        self,
        tool: str,
        project_id: str | None = None,
        data: dict[str, Any] | None = None,
        success: bool = True,
        warnings: list[str] | None = None,
        errors: list[str] | None = None,
        artifacts: list[dict[str, Any]] | None = None,
    ) -> Response:
        return Response(
            tool=tool,
            project_id=project_id,
            data=data or {},
            success=success,
            warnings=warnings or [],
            errors=errors or [],
            artifacts=artifacts or [],
        )

    def _artifact(self, path: Path, version: int, kind: str) -> dict[str, Any]:
        path = self.workspace.safe(path)
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return {
            "path": str(path),
            "kind": kind,
            "version": version,
            "bytes": path.stat().st_size,
            "sha256": digest.hexdigest(),
        }

    def _inspect(self, path: Path) -> dict[str, Any]:
        self.workspace.safe(path)
        if path.stat().st_size > self.settings.max_export_bytes:
            raise DesignError("Mesh file exceeds configured size limit.")
        with tempfile.TemporaryDirectory(
            dir=self.workspace.safe(self.workspace.root / ".tmp")
        ) as temp:
            result_path = Path(temp) / "inspection.json"
            run = self.process.run(
                [
                    sys.executable,
                    "-m",
                    "openscad_design_mcp.mesh_inspector",
                    str(path),
                    str(result_path),
                ],
                Path(temp),
                self.settings.inspect_timeout,
                result_path,
                1024 * 1024,
            )
            if not run["success"]:
                raise DesignError("Mesh inspection failed: " + "; ".join(run["errors"]))
            result: dict[str, Any] = json.loads(result_path.read_text(encoding="utf-8"))
            return result

    def get_system_status(self) -> Response:
        """Detect OpenSCAD, probe real PNG rendering, and report dependency versions and limits."""
        libraries = {}
        for name in ("fastmcp", "trimesh", "manifold3d", "Pillow", "pydantic", "scipy"):
            try:
                libraries[name] = {"available": True, "version": importlib.metadata.version(name)}
            except importlib.metadata.PackageNotFoundError:
                libraries[name] = {"available": False, "version": None}
        data: dict[str, Any] = {
            "python": platform.python_version(),
            "workspace": str(self.workspace.root),
            "libraries": libraries,
            "limits": self.settings.model_dump(mode="json"),
            "openscad": None,
            "render_available": False,
        }
        try:
            caps = self.runner.capabilities(self.workspace.safe(self.workspace.root / ".tmp"))
            data["openscad"] = caps
            with tempfile.TemporaryDirectory(
                dir=self.workspace.safe(self.workspace.root / ".tmp")
            ) as temp:
                source, output = Path(temp) / "model.scad", Path(temp) / "probe.png"
                source.write_text("cube([20,20,10], center=true);", encoding="utf-8")
                options, warnings = preview_options(
                    self.settings,
                    caps["flags"],
                    128,
                    128,
                    "isometric",
                    None,
                    "orthographic",
                    "Cornfield",
                )
                run = self.runner.execute(
                    source,
                    output,
                    self.settings.preview_timeout,
                    options,
                    self.settings.max_image_bytes,
                )
                data["render_probe"] = run
                if run["success"]:
                    inspect_png(output, 128, 128, self.settings.max_image_bytes)
                    data["render_available"] = True
                return self._result(
                    "get_system_status",
                    data=data,
                    warnings=warnings + run["warnings"],
                    success=run["success"],
                    errors=run["errors"],
                )
        except Exception as exc:
            return self._result(
                "get_system_status", data=data, success=False, errors=[sanitize(str(exc))]
            )

    def create_project(
        self,
        name: str,
        description: str,
        requirements: str,
        initial_scad_code: str,
        units: str = "mm",
    ) -> Response:
        """Create and validate version 1; invalid geometry remains saved and editable."""
        meta = self.workspace.create(name, description, requirements, initial_scad_code, units)
        project_id = meta["project_id"]
        try:
            validated = self.validate_scad(project_id)
        except Exception as exc:
            validated = self._result(
                "validate_scad", project_id, success=False, errors=[sanitize(str(exc))]
            )
        return self._result(
            "create_project",
            project_id,
            {
                "metadata": self.workspace.metadata(project_id),
                "created": True,
                "validation": validated.model_dump(),
            },
            warnings=validated.warnings
            + (
                []
                if validated.success
                else ["Project saved; initial validation failed. Fix code or configure OpenSCAD."]
            ),
        )

    def list_projects(self) -> Response:
        """List projects with UTC timestamps and latest status."""
        projects, warnings = [], []
        for path in self.workspace.safe(self.workspace.root / "projects").iterdir():
            try:
                meta = self.workspace.metadata(path.name)
                projects.append(
                    {
                        key: meta[key]
                        for key in (
                            "project_id",
                            "name",
                            "created_at",
                            "updated_at",
                            "status",
                            "current_version",
                        )
                    }
                )
            except Exception as exc:
                warnings.append("Skipped unreadable project: " + sanitize(str(exc)))
        return self._result("list_projects", data={"projects": projects}, warnings=warnings)

    def get_project(self, project_id: str) -> Response:
        """Read metadata, current code, exports, and the latest finalization report."""
        meta = self.workspace.metadata(project_id)
        exports = [
            str(self.workspace.safe(p))
            for p in self.workspace.safe(self.workspace.project(project_id) / "exports").iterdir()
            if p.is_file()
        ]
        return self._result(
            "get_project",
            project_id,
            {
                "metadata": meta,
                "scad_code": self.workspace.source(project_id).read_text(encoding="utf-8"),
                "current_version": meta["current_version"],
                "exports": exports,
                "latest_report": meta["last_report"],
            },
        )

    def read_model(self, project_id: str) -> Response:
        """Read the checksum-verified current SCAD snapshot."""
        return self._result(
            "read_model",
            project_id,
            {
                "scad_code": self.workspace.source(project_id).read_text(encoding="utf-8"),
                "version": self.workspace.metadata(project_id)["current_version"],
            },
        )

    def update_model(
        self, project_id: str, scad_code: str, change_summary: str, expected_version: int
    ) -> Response:
        """Atomically update code if expected_version matches, invalidating previous results."""
        meta = self.workspace.update(project_id, scad_code, change_summary, expected_version)
        return self._result(
            "update_model", project_id, {"metadata": meta, "version": meta["current_version"]}
        )

    def validate_scad(self, project_id: str) -> Response:
        """Compile to a temporary STL and inspect for empty geometry, recording diagnostics."""
        meta = self.workspace.metadata(project_id)
        current_version = meta["current_version"]
        source = self.workspace.source(project_id)
        with tempfile.TemporaryDirectory(dir=self.workspace.project(project_id)) as temp:
            output = Path(temp) / "validation.stl"
            run = self.runner.execute(source, output, self.settings.validate_timeout)
            if run["success"]:
                try:
                    mesh = self._inspect(output)
                    run["empty"] = mesh["empty"]
                    if mesh["empty"]:
                        run["errors"].append("Model is empty.")
                        run["success"] = False
                    else:
                        meta["last_inspection"] = {
                            **mesh,
                            "version": current_version,
                            "units": meta["units"],
                        }
                except DesignError as exc:
                    run["success"] = False
                    run["errors"].append(str(exc))
        meta = self.workspace.metadata(project_id)
        run["version"] = current_version
        run["checked_at"] = utc_now()
        meta["last_validation"] = run
        meta["status"] = "validated" if run["success"] else "invalid"
        meta["last_report"] = None
        self.workspace.save_metadata(meta)
        return self._result(
            "validate_scad", project_id, run, run["success"], run["warnings"], run["errors"]
        )

    def render_preview(
        self,
        project_id: str,
        width: int = 800,
        height: int = 600,
        camera: list[float] | None = None,
        view: View = "isometric",
        projection: Projection = "orthographic",
        colorscheme: ColorScheme = "Cornfield",
        version: int | None = None,
        render_mode: RenderMode = "preview",
    ) -> Response:
        """Render a verified PNG for a named view or a numeric 6/7-value custom camera."""
        source = self.workspace.source(project_id, version)
        actual_version = (
            version
            if version is not None
            else self.workspace.metadata(project_id)["current_version"]
        )
        caps = self.runner.capabilities(source.parent)
        options, warnings = preview_options(
            self.settings,
            caps["flags"],
            width,
            height,
            view,
            camera,
            projection,
            colorscheme,
            render_mode,
        )
        folder = self.workspace.safe(self.workspace.project(project_id) / "previews")
        with tempfile.TemporaryDirectory(dir=folder) as temp:
            output = Path(temp) / "preview.png"
            run = self.runner.execute(
                source,
                output,
                self.settings.preview_timeout,
                options,
                self.settings.max_image_bytes,
            )
            if not run["success"]:
                return self._result(
                    "render_preview",
                    project_id,
                    {"view": view, "run": run},
                    False,
                    warnings + run["warnings"],
                    run["errors"],
                )
            info = inspect_png(output, width, height, self.settings.max_image_bytes)
            target = self.workspace.safe(
                folder / f"v{actual_version}-{view}-{uuid.uuid4().hex}.png"
            )
            output.replace(target)
        artifact = self._artifact(target, actual_version, "preview")
        return self._result(
            "render_preview",
            project_id,
            {
                **info,
                "path": str(target),
                "view": view,
                "version": actual_version,
                "rendered": True,
                "run": run,
            },
            warnings=warnings + run["warnings"],
            artifacts=[artifact],
        )

    def render_preview_set(
        self,
        project_id: str,
        views: list[View] | None = None,
        width: int = 800,
        height: int = 600,
        version: int | None = None,
        render_mode: RenderMode = "preview",
    ) -> Response:
        """Render six default views, or 1–12 requested named views, in parallel preserving order."""
        selected = DEFAULT_VIEWS if views is None else views
        if not 1 <= len(selected) <= self.settings.max_previews:
            raise DesignError("Preview set must contain 1 to configured maximum views.")

        def render_single(v: View) -> Response:
            try:
                return self.render_preview(
                    project_id,
                    width,
                    height,
                    view=v,
                    version=version,
                    render_mode=render_mode,
                )
            except Exception as exc:
                return self._result(
                    "render_preview",
                    project_id,
                    {"view": v},
                    False,
                    errors=[sanitize(str(exc))],
                )

        max_workers = min(len(selected), 8)
        rendered_map: dict[int, Response] = {}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_idx = {
                executor.submit(render_single, view): idx for idx, view in enumerate(selected)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                rendered_map[idx] = future.result()

        results, artifacts, warnings, errors = [], [], [], []
        for idx in range(len(selected)):
            result = rendered_map[idx]
            results.append(result.model_dump())
            artifacts.extend(result.artifacts)
            warnings.extend(result.warnings)
            errors.extend(result.errors)

        return self._result(
            "render_preview_set",
            project_id,
            {"previews": results},
            all(r["success"] for r in results),
            warnings,
            errors,
            artifacts,
        )

    def export_model(self, project_id: str, output_format: Format = "stl") -> Response:
        """Export STL, 3MF, OFF, AMF, DXF or SVG with fixed CLI arguments."""
        if output_format not in ("stl", "3mf", "off", "amf", "dxf", "svg"):
            raise DesignError("Unsupported export format.")
        source = self.workspace.source(project_id)
        meta = self.workspace.metadata(project_id)
        version = meta["current_version"]
        folder = self.workspace.safe(self.workspace.project(project_id) / "exports")
        with tempfile.TemporaryDirectory(dir=folder) as temp:
            output = Path(temp) / f"model.{output_format}"
            run = self.runner.execute(source, output, self.settings.export_timeout)
            if not run["success"]:
                return self._result(
                    "export_model", project_id, {"run": run}, False, run["warnings"], run["errors"]
                )
            target = self.workspace.safe(folder / f"v{version}-{uuid.uuid4().hex}.{output_format}")
            output.replace(target)
        artifact = self._artifact(target, version, "export")
        meta["last_export"] = {**artifact, "format": output_format}
        self.workspace.save_metadata(meta)
        return self._result(
            "export_model",
            project_id,
            {"path": str(target), "format": output_format, "version": version, "run": run},
            warnings=run["warnings"],
            artifacts=[artifact],
        )

    def inspect_mesh(self, project_id: str) -> Response:
        """Inspect a current verified STL/3MF export or create a temporary STL automatically."""
        meta = self.workspace.metadata(project_id)
        self.workspace.source(project_id)
        current_version = meta["current_version"]

        # 1. Reuse cached inspection if available for the current version
        cached_insp = meta.get("last_inspection")
        if cached_insp and cached_insp.get("version") == current_version:
            return self._result(
                "inspect_mesh",
                project_id,
                cached_insp,
            )

        exported = meta.get("last_export")
        warnings = []
        if (
            exported
            and exported["version"] == current_version
            and exported["format"] in ("stl", "3mf")
        ):
            path = self.workspace.safe(Path(exported["path"]))
            if path.parent != self.workspace.safe(self.workspace.project(project_id) / "exports"):
                raise DesignError("Export path is outside the project's exports directory.")
            if (
                path.exists()
                and path.stat().st_size <= self.settings.max_export_bytes
                and self._artifact(path, current_version, "export")["sha256"]
                == exported["sha256"]
            ):
                mesh = self._inspect(path)
                data = {**mesh, "version": current_version, "units": meta["units"]}
                meta["last_inspection"] = data
                self.workspace.save_metadata(meta)
                return self._result(
                    "inspect_mesh",
                    project_id,
                    data,
                )
            warnings.append("Cached export missing or changed; inspecting a fresh temporary STL.")
        with tempfile.TemporaryDirectory(dir=self.workspace.project(project_id)) as temp:
            output = Path(temp) / "inspection.stl"
            run = self.runner.execute(
                self.workspace.source(project_id), output, self.settings.export_timeout
            )
            if not run["success"]:
                return self._result(
                    "inspect_mesh",
                    project_id,
                    {"run": run},
                    False,
                    warnings + run["warnings"],
                    run["errors"],
                )
            mesh = self._inspect(output)
        data = {**mesh, "version": current_version, "units": meta["units"]}
        meta["last_inspection"] = data
        self.workspace.save_metadata(meta)
        return self._result(
            "inspect_mesh",
            project_id,
            data,
            warnings=warnings,
        )

    def compare_dimensions(
        self,
        project_id: str,
        expected_dimensions: Dimensions,
        tolerance: float = 0.1,
        percent_tolerance: float | None = None,
    ) -> Response:
        """Compare X/Y/Z in project units; null skips an axis, tolerances use the larger bound."""
        compare(None, expected_dimensions, tolerance, percent_tolerance)
        mesh = self.inspect_mesh(project_id)
        if not mesh.success:
            return mesh.model_copy(update={"tool": "compare_dimensions"})
        data = compare(
            mesh.data.get("dimensions"), expected_dimensions, tolerance, percent_tolerance
        )
        return self._result(
            "compare_dimensions",
            project_id,
            data,
            data["passed"],
            warnings=mesh.warnings,
            errors=[] if data["passed"] else ["Dimensions outside requested tolerance."],
        )

    def check_printability(
        self,
        project_id: str,
        build_volume: BuildVolume | None = None,
        require_watertight: bool = True,
    ) -> Response:
        """Check mesh and build extents; wall thickness, supports and clearance stay unknown."""
        mesh = self.inspect_mesh(project_id)
        if not mesh.success:
            return mesh.model_copy(update={"tool": "check_printability"})
        data = printability(
            mesh.data,
            build_volume,
            require_watertight,
            self.workspace.metadata(project_id)["units"],
        )
        return self._result(
            "check_printability",
            project_id,
            data,
            data["passed"],
            mesh.warnings + data["warnings"],
            [f"Failed check: {k}" for k, v in data["checks"].items() if not v],
        )

    def finalize_model(
        self,
        project_id: str,
        output_format: Format = "stl",
        expected_dimensions: Dimensions | None = None,
        tolerance: float = 0.1,
        build_volume: BuildVolume | None = None,
        require_watertight: bool = True,
        render_views: list[View] | None = None,
    ) -> Response:
        """Validate, render, export and inspect one revision; finalize only if all gates pass."""
        compare(None, expected_dimensions or Dimensions(), tolerance)
        selected = DEFAULT_VIEWS if render_views is None else render_views
        if not 1 <= len(selected) <= self.settings.max_previews or "custom" in selected:
            raise DesignError(
                "Finalization requires 1 to configured maximum named views, excluding custom."
            )
        meta = self.workspace.metadata(project_id)
        meta.update(status="checking", last_report=None)
        self.workspace.save_metadata(meta)
        steps: dict[str, Any] = {}
        artifacts: list[dict[str, Any]] = []
        errors: list[str] = []
        warnings: list[str] = []
        for name, action in (
            ("validation", lambda: self.validate_scad(project_id)),
            ("previews", lambda: self.render_preview_set(project_id, selected)),
            ("export", lambda: self.export_model(project_id, output_format)),
            ("mesh", lambda: self.inspect_mesh(project_id)),
        ):
            try:
                result = action()
            except Exception as exc:
                result = self._result(name, project_id, success=False, errors=[sanitize(str(exc))])
            steps[name] = result.model_dump()
            artifacts.extend(result.artifacts)
            warnings.extend(result.warnings)
            errors.extend(f"{name}: {message}" for message in result.errors)
        mesh = steps["mesh"]["data"] if steps["mesh"]["success"] else {}
        dimension_check = (
            compare(mesh.get("dimensions"), expected_dimensions, tolerance)
            if expected_dimensions
            else None
        )
        print_check = printability(mesh, build_volume, require_watertight, meta["units"])
        warnings.extend(print_check["warnings"])
        if dimension_check and not dimension_check["passed"]:
            errors.append("Adjust geometry to meet the requested dimensions.")
        errors.extend(
            f"Correct mesh check: {key}."
            for key, value in print_check["checks"].items()
            if not value
        )
        if output_format in ("dxf", "svg"):
            errors.append(
                "3D print finalization requires a 3D export format; use export_model for 2D output."
            )
        finalized = all(s["success"] for s in steps.values()) and not errors
        report = {
            "project_id": project_id,
            "version": meta["current_version"],
            "created_at": utc_now(),
            "finalized": finalized,
            "steps": steps,
            "dimension_check": dimension_check,
            "printability": print_check,
            "errors": errors,
            "warnings": warnings,
            "policy": {
                "output_format": output_format,
                "tolerance": tolerance,
                "expected_dimensions": expected_dimensions.model_dump()
                if expected_dimensions
                else None,
                "build_volume": build_volume.model_dump() if build_volume else None,
                "require_watertight": require_watertight,
                "render_views": selected,
            },
            "suggested_actions": []
            if finalized
            else list(dict.fromkeys(errors))
            + ["Review diagnostics, update_model with expected_version, and finalize again."],
        }
        path = self.workspace.safe(
            self.workspace.project(project_id)
            / "reports"
            / f"v{meta['current_version']}-{uuid.uuid4().hex}.json"
        )
        self.workspace.json_write(path, report)
        meta = self.workspace.metadata(project_id)
        meta.update(status="finalized" if finalized else "needs_changes", last_report=report)
        self.workspace.save_metadata(meta)
        artifacts.append(self._artifact(path, meta["current_version"], "report"))
        return self._result(
            "finalize_model", project_id, report, finalized, warnings, errors, artifacts
        )

    def list_versions(self, project_id: str) -> Response:
        """List immutable versions, UTC timestamps, summaries and SHA-256 checksums."""
        return self._result(
            "list_versions", project_id, {"versions": self.workspace.versions(project_id)}
        )

    def restore_version(self, project_id: str, version: int, expected_version: int) -> Response:
        """Restore a historical snapshot as a new version, retaining the complete history."""
        code = self.workspace.source(project_id, version).read_text(encoding="utf-8")
        meta = self.workspace.update(
            project_id, code, f"Restore version {version}", expected_version
        )
        return self._result(
            "restore_version", project_id, {"metadata": meta, "version": meta["current_version"]}
        )

    def delete_project(self, project_id: str, confirm_project_id: str) -> Response:
        """Move a project to trash only when the confirmation ID matches exactly."""
        target = self.workspace.delete(project_id, confirm_project_id)
        return self._result(
            "delete_project",
            project_id,
            {
                "trash_path": str(target),
                "restore_path": str(self.workspace.root / "projects" / project_id),
            },
        )
