"""FastMCP stdio server exposing the VanningLayout Step6 solver."""

from __future__ import annotations

from math import isfinite
from typing import Any

from vanning.geometry import Container
from vanning.problem_spec import (
    CONTAINER_20FT,
    CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    CONTAINER_20FT_MAX_PAYLOAD_KG,
    STEP5_MIN_SUPPORT_AREA_RATIO,
)
from vanning.step3_weighted_3d import WeightedItem3D
from vanning.step4_center_of_gravity_3d import CenterBalancedBin3D
from vanning.step6_bin_count_minimization_3d import (
    MinimizedBinCountPackingSummary3D,
    pack_min_bin_count_3d_by_destination,
)


def pack_vanning_layout(
    items: list[dict[str, Any]],
    container: dict[str, Any] | None = None,
    max_weight_kg: float = CONTAINER_20FT_MAX_PAYLOAD_KG,
    max_center_offset_mm: float = CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    min_support_area_ratio: float = STEP5_MIN_SUPPORT_AREA_RATIO,
    default_allow_rotate: bool = True,
) -> dict[str, Any]:
    """Pack 3D boxes into near-minimum-count containers.

    Each item requires item_id, length, width, height, weight_kg, and dest.
    Dimensions are millimeters and weight is kilograms. The optional container
    accepts length/width/height or l/w/h. Results include one placement list per
    container.
    """
    layout = solve_vanning_layout(
        items=items,
        container=container,
        max_weight_kg=max_weight_kg,
        max_center_offset_mm=max_center_offset_mm,
        min_support_area_ratio=min_support_area_ratio,
        default_allow_rotate=default_allow_rotate,
    )
    return layout


def solve_vanning_layout(
    items: list[dict[str, Any]],
    container: dict[str, Any] | None = None,
    max_weight_kg: float = CONTAINER_20FT_MAX_PAYLOAD_KG,
    max_center_offset_mm: float = CONTAINER_20FT_CENTER_OF_GRAVITY_RADIUS_MM,
    min_support_area_ratio: float = STEP5_MIN_SUPPORT_AREA_RATIO,
    default_allow_rotate: bool = True,
) -> dict[str, Any]:
    """Validate MCP-facing JSON input and return a JSON-serializable layout."""
    weighted_items = _parse_items(items, default_allow_rotate=default_allow_rotate)
    target_container = _parse_container(container)
    summary = pack_min_bin_count_3d_by_destination(
        weighted_items,
        target_container,
        max_weight_kg=_finite_float(max_weight_kg, "max_weight_kg"),
        max_center_offset_mm=_finite_float(max_center_offset_mm, "max_center_offset_mm"),
        min_support_area_ratio=_finite_float(min_support_area_ratio, "min_support_area_ratio"),
    )
    return _summary_to_dict(summary, target_container)


def create_mcp_server() -> Any:
    """Create the FastMCP server. Import FastMCP lazily for testability."""
    FastMCP = _load_fastmcp()
    server = FastMCP("VanningLayout")
    server.tool()(pack_vanning_layout)
    return server


def main() -> None:
    create_mcp_server().run(transport="stdio")


def _load_fastmcp() -> Any:
    try:
        from fastmcp import FastMCP

        return FastMCP
    except ImportError:
        try:
            from mcp.server.fastmcp import FastMCP

            return FastMCP
        except ImportError as exc:
            raise RuntimeError(
                "FastMCP is required to run the MCP server. Install it with "
                "`pip install fastmcp` or `pip install mcp`."
            ) from exc


def _parse_items(items: list[dict[str, Any]], default_allow_rotate: bool) -> list[WeightedItem3D]:
    if not isinstance(items, list) or not items:
        raise ValueError("items must be a non-empty list")

    allow_rotate_default = _bool_value(default_allow_rotate, "default_allow_rotate")
    parsed: list[WeightedItem3D] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"items[{index}] must be an object")

        item_id = _string_field(item, "item_id", ("id",), f"items[{index}]")
        if item_id in seen_ids:
            raise ValueError(f"duplicate item_id: {item_id}")
        seen_ids.add(item_id)

        parsed.append(
            WeightedItem3D(
                item_id=item_id,
                length=_float_field(item, "length", ("l",), f"items[{index}]"),
                width=_float_field(item, "width", ("w",), f"items[{index}]"),
                height=_float_field(item, "height", ("h",), f"items[{index}]"),
                weight_kg=_float_field(item, "weight_kg", ("weight",), f"items[{index}]"),
                dest=_string_field(item, "dest", ("destination",), f"items[{index}]"),
                allow_rotate=_bool_value(
                    item.get("allow_rotate", allow_rotate_default),
                    f"items[{index}].allow_rotate",
                ),
            )
        )
    return parsed


def _parse_container(container: dict[str, Any] | None) -> Container:
    if container is None:
        return CONTAINER_20FT
    if not isinstance(container, dict):
        raise ValueError("container must be an object")
    return Container(
        l=_float_field(container, "length", ("l",), "container"),
        w=_float_field(container, "width", ("w",), "container"),
        h=_float_field(container, "height", ("h",), "container"),
    )


def _summary_to_dict(summary: MinimizedBinCountPackingSummary3D, container: Container) -> dict[str, Any]:
    return {
        "bin_count": summary.bin_count,
        "initial_bin_count": summary.initial_bin_count,
        "total_weight_kg": summary.total_weight_kg,
        "max_observed_center_offset_mm": summary.max_observed_center_offset_mm,
        "all_bins_within_center_constraint": summary.all_bins_within_center_constraint,
        "constraints": {
            "max_center_offset_mm": summary.max_center_offset_mm,
            "min_support_area_ratio": summary.min_support_area_ratio,
        },
        "container": _container_to_dict(container),
        "bins": [_bin_to_dict(index, bin_) for index, bin_ in enumerate(summary.bins, start=1)],
    }


def _bin_to_dict(index: int, bin_: CenterBalancedBin3D) -> dict[str, Any]:
    return {
        "bin_index": index,
        "dest": bin_.dest,
        "item_count": len(bin_.placements),
        "total_weight_kg": bin_.total_weight_kg,
        "remaining_weight_kg": bin_.remaining_weight_kg,
        "center_of_gravity": {
            "x": bin_.center_of_gravity_x,
            "y": bin_.center_of_gravity_y,
            "offset_mm": bin_.center_offset_mm,
            "within_limit": bin_.satisfies_center_constraint,
        },
        "placements": [
            {
                "item_id": placement.item.item_id,
                "dest": placement.item.dest,
                "weight_kg": placement.item.weight_kg,
                "x": placement.x,
                "y": placement.y,
                "z": placement.z,
                "length": placement.length,
                "width": placement.width,
                "height": placement.height,
                "rotated": placement.rotated,
                "allow_rotate": placement.item.allow_rotate,
            }
            for placement in sorted(
                bin_.placements,
                key=lambda placed: (placed.z, placed.y, placed.x, placed.item.item_id),
            )
        ],
    }


def _container_to_dict(container: Container) -> dict[str, float]:
    return {
        "length": container.l,
        "width": container.w,
        "height": container.h,
    }


def _float_field(
    mapping: dict[str, Any],
    primary: str,
    aliases: tuple[str, ...],
    context: str,
) -> float:
    for name in (primary, *aliases):
        if name in mapping:
            return _finite_float(mapping[name], f"{context}.{primary}")
    raise ValueError(f"{context}.{primary} is required")


def _string_field(
    mapping: dict[str, Any],
    primary: str,
    aliases: tuple[str, ...],
    context: str,
) -> str:
    for name in (primary, *aliases):
        if name in mapping:
            value = mapping[name]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{context}.{primary} must be a non-empty string")
            return value.strip()
    raise ValueError(f"{context}.{primary} is required")


def _finite_float(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _bool_value(value: Any, name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    raise ValueError(f"{name} must be a boolean")


if __name__ == "__main__":
    main()
