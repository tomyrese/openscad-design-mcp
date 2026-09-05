import re


class DesignError(Exception):
    def __init__(self, message: str, code: str = "operation_failed") -> None:
        super().__init__(message)
        self.code = code


def sanitize(value: str, limit: int = 16000) -> str:
    value = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", value)
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    value = re.sub(r"(?i)(?:[A-Z]:[\\/]|/)(?:[^\s\"'<>:]+[\\/])+[^\s\"'<>:]*", "<path>", value)
    return value[:limit]
