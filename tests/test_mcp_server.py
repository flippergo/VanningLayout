import asyncio
import importlib.util
import unittest
from unittest.mock import patch

from vanning.mcp_server import create_mcp_server, pack_vanning_layout, solve_vanning_layout


class VanningMcpServerTests(unittest.TestCase):
    def test_solves_layout_from_json_like_payload(self) -> None:
        result = solve_vanning_layout(
            items=[
                {
                    "item_id": "A",
                    "length": 400,
                    "width": 400,
                    "height": 400,
                    "weight_kg": 6,
                    "dest": "X",
                    "allow_rotate": False,
                },
                {
                    "item_id": "B",
                    "length": 400,
                    "width": 400,
                    "height": 400,
                    "weight_kg": 4,
                    "dest": "X",
                    "allow_rotate": False,
                },
            ],
            container={"length": 2000, "width": 2000, "height": 2000},
            max_weight_kg=10,
            max_center_offset_mm=1000,
        )

        self.assertEqual(result["bin_count"], 1)
        self.assertEqual(result["initial_bin_count"], 1)
        self.assertEqual(result["total_weight_kg"], 10)
        self.assertTrue(result["all_bins_within_center_constraint"])
        self.assertEqual(result["container"], {"length": 2000.0, "width": 2000.0, "height": 2000.0})

        bin_ = result["bins"][0]
        self.assertEqual(bin_["dest"], "X")
        self.assertEqual(bin_["item_count"], 2)
        self.assertEqual({placement["item_id"] for placement in bin_["placements"]}, {"A", "B"})

    def test_accepts_short_aliases_for_item_and_container_fields(self) -> None:
        result = solve_vanning_layout(
            items=[
                {
                    "id": "A",
                    "l": 400,
                    "w": 400,
                    "h": 400,
                    "weight": 5,
                    "destination": "X",
                },
            ],
            container={"l": 2000, "w": 2000, "h": 2000},
            max_weight_kg=10,
            max_center_offset_mm=1000,
        )

        placement = result["bins"][0]["placements"][0]
        self.assertEqual(placement["item_id"], "A")
        self.assertTrue(placement["allow_rotate"])

    def test_rejects_duplicate_item_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate item_id"):
            solve_vanning_layout(
                items=[
                    {
                        "item_id": "A",
                        "length": 400,
                        "width": 400,
                        "height": 400,
                        "weight_kg": 5,
                        "dest": "X",
                    },
                    {
                        "item_id": "A",
                        "length": 400,
                        "width": 400,
                        "height": 400,
                        "weight_kg": 5,
                        "dest": "X",
                    },
                ],
                container={"length": 2000, "width": 2000, "height": 2000},
                max_weight_kg=10,
                max_center_offset_mm=1000,
            )

    def test_registers_fastmcp_tool(self) -> None:
        class FakeFastMCP:
            def __init__(self, name):
                self.name = name
                self.registered_tool = None

            def tool(self):
                def decorator(func):
                    self.registered_tool = func
                    return func

                return decorator

        with patch("vanning.mcp_server._load_fastmcp", return_value=FakeFastMCP):
            server = create_mcp_server()

        self.assertEqual(server.name, "VanningLayout")
        self.assertIs(server.registered_tool, pack_vanning_layout)

    @unittest.skipIf(importlib.util.find_spec("fastmcp") is None, "fastmcp is not installed")
    def test_calls_tool_with_real_fastmcp_client(self) -> None:
        async def call_tool():
            from fastmcp import Client

            async with Client(create_mcp_server()) as client:
                tools = await client.list_tools()
                result = await client.call_tool(
                    "pack_vanning_layout",
                    {
                        "items": [
                            {
                                "item_id": "A",
                                "length": 400,
                                "width": 400,
                                "height": 400,
                                "weight_kg": 6,
                                "dest": "X",
                                "allow_rotate": False,
                            },
                            {
                                "item_id": "B",
                                "length": 400,
                                "width": 400,
                                "height": 400,
                                "weight_kg": 4,
                                "dest": "X",
                                "allow_rotate": False,
                            },
                        ],
                        "container": {"length": 2000, "width": 2000, "height": 2000},
                        "max_weight_kg": 10,
                        "max_center_offset_mm": 1000,
                    },
                )
            return tools, result

        tools, result = asyncio.run(call_tool())

        self.assertIn("pack_vanning_layout", {tool.name for tool in tools})
        self.assertEqual(result.data["bin_count"], 1)
        self.assertEqual(result.data["bins"][0]["item_count"], 2)


if __name__ == "__main__":
    unittest.main()
