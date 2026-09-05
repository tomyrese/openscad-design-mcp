import asyncio
import sys

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from openscad_design_mcp.server import TOOL_NAMES, create_server


def test_mcp_schemas_and_structured_errors(settings):
    async def run():
        async with Client(create_server(settings)) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools} == set(TOOL_NAMES)
            for tool in tools:
                assert "self" not in tool.input_schema.get("properties", {})
                assert tool.output_schema
                assert "success" in tool.output_schema["properties"]
            update = next(t for t in tools if t.name == "update_model")
            assert "expected_version" in update.input_schema["required"]
            result = await client.call_tool("read_model", {"project_id": "../bad"})
            assert result.structured_content["success"] is False
            result = await client.call_tool("list_projects", {})
            assert result.structured_content["data"]["projects"] == []

    asyncio.run(run())


def test_stdio_module_launch(settings):
    async def run():
        transport = StdioTransport(
            sys.executable,
            ["-m", "openscad_design_mcp"],
            env={"OPENSCAD_MCP_WORKSPACE": str(settings.workspace)},
        )
        async with Client(transport, timeout=30) as client:
            assert len(await client.list_tools()) == 17
            result = await client.call_tool("list_projects", {})
            assert result.structured_content["success"]

    asyncio.run(run())
