import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from filelock import FileLock

from .config import Settings
from .errors import DesignError


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def checksum(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def check_code(code: str, limit: int) -> None:
    if not code.strip() or "\x00" in code:
        raise DesignError("SCAD code is empty or contains NUL.", "invalid_code")
    if len(code.encode("utf-8")) > limit:
        raise DesignError(f"SCAD exceeds {limit} bytes.", "code_too_large")
    tokens = re.sub(r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|//[^\n]*', " ", code)
    if re.search(r"\b(?:include|use|import|surface)\b", tokens):
        raise DesignError(
            "External file access is disabled: include, use, import and surface are not allowed. "
            "Inline trusted SCAD modules instead.",
            "external_file_access",
        )


class Workspace:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.workspace.absolute()
        self.safe(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        for name in ("projects", "trash", ".locks", ".tmp"):
            self.safe(self.root / name).mkdir(exist_ok=True)
        self.lock = FileLock(
            str(self.safe(self.root / ".locks" / "workspace.lock")), timeout=settings.lock_timeout
        )

    def safe(self, path: Path) -> Path:
        path = path.absolute()
        if not path.is_relative_to(self.root):
            raise DesignError("Path escapes workspace.", "unsafe_path")
        for part in (path, *path.parents):
            reparse = (
                part.exists()
                and getattr(part.lstat(), "st_file_attributes", 0)
                & stat.FILE_ATTRIBUTE_REPARSE_POINT
            )
            if part.is_symlink() or reparse:
                raise DesignError("Symlinks and junctions are not allowed.", "unsafe_path")
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise DesignError("Resolved path escapes workspace.", "unsafe_path")
        return path

    def project(self, project_id: str) -> Path:
        if re.fullmatch(r"[a-f0-9]{32}", project_id) is None:
            raise DesignError(
                "Invalid project_id: expected 32 lowercase hexadecimal characters.",
                "invalid_project_id",
            )
        path = self.safe(self.root / "projects" / project_id)
        if not path.is_dir():
            raise DesignError("Project not found.", "project_not_found")
        return path

    def atomic(self, path: Path, content: str) -> None:
        path = self.safe(path)
        fd, temporary = tempfile.mkstemp(prefix=".write-", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.safe(path))
        finally:
            Path(temporary).unlink(missing_ok=True)

    def json_write(self, path: Path, data: Any) -> None:
        self.atomic(path, json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))

    def json_read(self, path: Path) -> Any:
        return json.loads(self.safe(path).read_text(encoding="utf-8"))

    def metadata(self, project_id: str) -> dict[str, Any]:
        data: dict[str, Any] = self.json_read(self.project(project_id) / "project.json")
        if data["project_id"] != project_id:
            raise DesignError("Project metadata identity mismatch.", "integrity_error")
        return data

    def save_metadata(self, data: dict[str, Any]) -> None:
        data["updated_at"] = utc_now()
        self.json_write(self.project(data["project_id"]) / "project.json", data)

    def source(self, project_id: str, version: int | None = None) -> Path:
        meta = self.metadata(project_id)
        number = meta["current_version"] if version is None else version
        if not isinstance(number, int) or number < 1 or number > meta["current_version"]:
            raise DesignError("Version does not exist.", "invalid_version")
        base = self.safe(self.project(project_id) / "versions" / str(number))
        source = self.safe(base / "model.scad")
        code = source.read_text(encoding="utf-8")
        if checksum(code) != self.json_read(base / "version.json")["checksum"]:
            raise DesignError("Snapshot checksum mismatch.", "integrity_error")
        check_code(code, self.settings.max_code_bytes)
        if version is None:
            current = self.safe(self.project(project_id) / "current" / "model.scad")
            if not current.exists() or current.read_text(encoding="utf-8") != code:
                self.atomic(current, code)
        return source

    def snapshot(self, base: Path, version: int, code: str, summary: str) -> None:
        target = self.safe(base / "versions" / str(version))
        if target.exists():
            raise DesignError(
                "Uncommitted snapshot exists; inspect workspace before retrying.", "integrity_error"
            )
        stage = self.safe(base / "versions" / f".stage-{uuid.uuid4().hex}")
        stage.mkdir()
        try:
            self.atomic(stage / "model.scad", code)
            self.json_write(
                stage / "version.json",
                {
                    "version": version,
                    "created_at": utc_now(),
                    "change_summary": summary,
                    "checksum": checksum(code),
                },
            )
            stage.rename(target)
        finally:
            if stage.exists():
                shutil.rmtree(self.safe(stage))

    def create(
        self, name: str, description: str, requirements: str, code: str, units: str
    ) -> dict[str, Any]:
        check_code(code, self.settings.max_code_bytes)
        code = code.replace("\r\n", "\n").replace("\r", "\n")
        if not name.strip() or max(map(len, (name, description, requirements))) > 100000:
            raise DesignError("Invalid or oversized project metadata.", "invalid_metadata")
        if units not in ("mm", "cm", "m", "in"):
            raise DesignError("Units must be mm, cm, m or in.", "invalid_units")
        project_id = uuid.uuid4().hex
        base = self.safe(self.root / "projects" / project_id)
        base.mkdir(exist_ok=False)
        for directory in ("current", "versions", "previews", "exports", "reports"):
            (base / directory).mkdir()
        meta = dict(
            project_id=project_id,
            name=name,
            description=description,
            requirements=requirements,
            units=units,
            created_at=utc_now(),
            updated_at=utc_now(),
            current_version=1,
            status="draft",
            last_validation=None,
            last_export=None,
            last_inspection=None,
            last_report=None,
        )
        self.snapshot(base, 1, code, "Initial version")
        self.atomic(base / "current" / "model.scad", code)
        self.json_write(base / "project.json", meta)
        return meta

    def update(
        self, project_id: str, code: str, summary: str, expected_version: int
    ) -> dict[str, Any]:
        check_code(code, self.settings.max_code_bytes)
        code = code.replace("\r\n", "\n").replace("\r", "\n")
        if len(summary) > 100000:
            raise DesignError("Change summary is too large.")
        meta = self.metadata(project_id)
        if meta["current_version"] != expected_version:
            raise DesignError(
                f"Version conflict: current version is {meta['current_version']}.",
                "version_conflict",
            )
        self.source(project_id)
        base = self.project(project_id)
        next_version = expected_version + 1
        self.snapshot(base, next_version, code, summary)
        try:
            self.atomic(base / "current" / "model.scad", code)
            meta.update(
                current_version=next_version,
                status="draft",
                last_validation=None,
                last_export=None,
                last_inspection=None,
                last_report=None,
            )
            self.save_metadata(meta)
        except Exception:
            committed = self.metadata(project_id)["current_version"]
            if committed == expected_version:
                shutil.rmtree(self.safe(base / "versions" / str(next_version)))
                self.source(project_id)
            raise
        return meta

    def versions(self, project_id: str) -> list[dict[str, Any]]:
        meta = self.metadata(project_id)
        return [
            self.json_read(self.project(project_id) / "versions" / str(i) / "version.json")
            for i in range(1, meta["current_version"] + 1)
        ]

    def delete(self, project_id: str, confirm_project_id: str) -> Path:
        if project_id != confirm_project_id:
            raise DesignError("confirm_project_id must match project_id exactly.", "confirmation")
        source = self.project(project_id)
        for child in source.rglob("*"):
            self.safe(child)
        target = self.safe(self.root / "trash" / f"{project_id}-{uuid.uuid4().hex}")
        source.rename(target)
        return target
