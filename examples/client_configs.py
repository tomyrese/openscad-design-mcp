import json
import sys
from pathlib import Path

from openscad_design_mcp.config import discover_openscad
from openscad_design_mcp.errors import DesignError


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    try:
        openscad = str(discover_openscad())
    except DesignError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from None
    output = root / "workspace" / "client-configs"
    output.mkdir(parents=True, exist_ok=True)
    python = str(Path(sys.executable).absolute())
    environment = {
        "OPENSCAD_PATH": openscad,
        "OPENSCAD_MCP_WORKSPACE": str(root / "workspace"),
    }
    command = [python, "-m", "openscad_design_mcp"]
    local = {"type": "local", "command": command, "environment": environment}
    configs = {
        "antigravity-claude.json": {
            "mcpServers": {
                "openscad-design": {
                    "command": python,
                    "args": command[1:],
                    "env": environment,
                }
            }
        },
        "opencode-v1.json": {
            "$schema": "https://opencode.ai/config.json",
            "mcp": {"openscad-design": {**local, "enabled": True, "timeout": 30000}},
        },
        "opencode-v2.json": {
            "$schema": "https://opencode.ai/config.json",
            "mcp": {
                "servers": {
                    "openscad-design": {
                        **local,
                        "disabled": False,
                        "codemode": False,
                        "timeout": {"startup": 30000, "catalog": 30000, "execution": 1500000},
                    }
                }
            },
        },
    }
    for name, data in configs.items():
        (output / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    toml = [
        "[mcp_servers.openscad-design]",
        "command = " + json.dumps(python, ensure_ascii=False),
        'args = ["-m", "openscad_design_mcp"]',
        "startup_timeout_sec = 30",
        "tool_timeout_sec = 1500",
        "",
        "[mcp_servers.openscad-design.env]",
        *(f"{key} = {json.dumps(value, ensure_ascii=False)}" for key, value in environment.items()),
    ]
    (output / "codex.toml").write_text("\n".join(toml) + "\n", encoding="utf-8")
    print("Configuration examples saved to:")
    print(output)
    print("Copy the server entry into your client settings. Existing settings were not changed.")


if __name__ == "__main__":
    main()
