# VanningLayout MCP server

This project exposes the Step6 near-minimum-bin 3D packing solver as a FastMCP
tool over stdio.

## Install

```powershell
pip install -r requirements-mcp.txt
```

## Run

```powershell
python -m vanning.mcp_server
```

The server uses stdio transport and registers one tool:

- `pack_vanning_layout`

## Tool input

`pack_vanning_layout` accepts JSON-like arguments:

```json
{
  "items": [
    {
      "item_id": "A",
      "length": 400,
      "width": 400,
      "height": 400,
      "weight_kg": 6,
      "dest": "X",
      "allow_rotate": false
    },
    {
      "item_id": "B",
      "length": 400,
      "width": 400,
      "height": 400,
      "weight_kg": 4,
      "dest": "X",
      "allow_rotate": false
    }
  ],
  "container": {
    "length": 2000,
    "width": 2000,
    "height": 2000
  },
  "max_weight_kg": 10,
  "max_center_offset_mm": 1000,
  "min_support_area_ratio": 0.8
}
```

Notes:

- Dimensions are millimeters.
- Weights are kilograms.
- `container` is optional. If omitted, the built-in 20ft container constants are
  used.
- `allow_rotate` is optional per item. If omitted, `default_allow_rotate` is
  used, and its default is `true`.
- Short aliases are accepted: item `id/l/w/h/weight/destination`, and container
  `l/w/h`.

## Tool output

The result is a JSON-serializable object with:

- `bin_count` and `initial_bin_count`
- total payload weight
- center-of-gravity constraint status
- one `bins` entry per container
- one `placements` entry per placed item, including `x/y/z`, placed
  `length/width/height`, `rotated`, `dest`, and `weight_kg`

## Codex MCP config example

Add an entry like this to `C:\Users\hoppe\.codex\config.toml`, adjusting the
Python executable if you use a virtual environment:

```toml
[mcp_servers.vanning_layout]
command = "python"
args = ["-m", "vanning.mcp_server"]
cwd = "C:\\Users\\hoppe\\work\\VanningLayout"
```
