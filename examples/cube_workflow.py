import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main() -> None:
    root = Path(__file__).resolve().parents[1]
    transport = StdioTransport(
        command=sys.executable,
        args=["-m", "openscad_design_mcp"],
        env={"OPENSCAD_MCP_WORKSPACE": str(root / "workspace")},
    )
    async with Client(transport, timeout=1500) as client:
        created = await client.call_tool(
            "create_project",
            {
                "name": "Cube kiểm thử",
                "description": "MCP stdio end-to-end",
                "requirements": "20 x 20 x 10 mm, watertight",
                "initial_scad_code": (root / "examples" / "cube.scad").read_text(encoding="utf-8"),
            },
        )
        data = created.structured_content
        if not data or not data["success"]:
            raise RuntimeError(str(data))
        project_id = data["project_id"]
        result = await client.call_tool(
            "finalize_model",
            {
                "project_id": project_id,
                "expected_dimensions": {"x": 20, "y": 20, "z": 10},
                "build_volume": {"x": 220, "y": 220, "z": 250},
            },
        )
        print(json.dumps(result.structured_content, ensure_ascii=True, indent=2))
        if not result.structured_content or not result.structured_content["success"]:
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
