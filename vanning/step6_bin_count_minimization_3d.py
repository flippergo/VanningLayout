"""Step6: reduce container count by repartitioning Step5-feasible bins."""

from collections import defaultdict
from dataclasses import dataclass
from math import ceil

from vanning.geometry import Container
from vanning.problem_spec import STEP5_MIN_SUPPORT_AREA_RATIO
from vanning.step3_weighted_3d import WeightedItem3D, _exceeds_weight_limit
from vanning.step4_center_of_gravity_3d import CenterBalancedBin3D
from vanning.step5_realistic_stability_3d import (
    pack_realistic_stable_3d_by_destination_ffd,
    pack_single_realistic_stable_bin,
)


@dataclass(frozen=True)
class MinimizedBinCountPackingSummary3D:
    """Summary of the Step6 bin-count minimization result."""

    bins: list[CenterBalancedBin3D]
    max_center_offset_mm: float
    min_support_area_ratio: float
    initial_bin_count: int

    @property
    def bin_count(self) -> int:
        return len(self.bins)

    @property
    def total_weight_kg(self) -> float:
        return sum(bin_.total_weight_kg for bin_ in self.bins)

    @property
    def max_observed_center_offset_mm(self) -> float:
        return max((bin_.center_offset_mm for bin_ in self.bins), default=0.0)

    @property
    def all_bins_within_center_constraint(self) -> bool:
        return all(bin_.satisfies_center_constraint for bin_ in self.bins)


def pack_min_bin_count_3d_by_destination(
    items: list[WeightedItem3D],
    container: Container,
    max_weight_kg: float,
    max_center_offset_mm: float,
    min_support_area_ratio: float = STEP5_MIN_SUPPORT_AREA_RATIO,
) -> MinimizedBinCountPackingSummary3D:
    """Build a Step5 solution, then iteratively try to reduce one bin per destination."""
    initial_summary = pack_realistic_stable_3d_by_destination_ffd(
        items,
        container,
        max_weight_kg=max_weight_kg,
        max_center_offset_mm=max_center_offset_mm,
        min_support_area_ratio=min_support_area_ratio,
    )

    bins_by_dest: dict[str, list[CenterBalancedBin3D]] = defaultdict(list)
    for bin_ in initial_summary.bins:
        bins_by_dest[bin_.dest].append(bin_)

    minimized_bins: list[CenterBalancedBin3D] = []
    for dest_bins in bins_by_dest.values():
        minimized_bins.extend(
            _minimize_destination_bins(
                dest_bins,
                container=container,
                max_weight_kg=max_weight_kg,
                max_center_offset_mm=max_center_offset_mm,
                min_support_area_ratio=min_support_area_ratio,
            )
        )

    summary = MinimizedBinCountPackingSummary3D(
        bins=minimized_bins,
        max_center_offset_mm=max_center_offset_mm,
        min_support_area_ratio=min_support_area_ratio,
        initial_bin_count=initial_summary.bin_count,
    )
    if not summary.all_bins_within_center_constraint:
        raise ValueError("center of gravity constraint violated")

    return summary


def _minimize_destination_bins(
    bins: list[CenterBalancedBin3D],
    container: Container,
    max_weight_kg: float,
    max_center_offset_mm: float,
    min_support_area_ratio: float,
) -> list[CenterBalancedBin3D]:
    current_bins = list(bins)
    current_items = [placement.item for bin_ in current_bins for placement in bin_.placements]
    min_possible_bin_count = ceil(sum(item.weight_kg for item in current_items) / max_weight_kg)

    while len(current_bins) > min_possible_bin_count:
        current_items = [placement.item for bin_ in current_bins for placement in bin_.placements]
        reduced_bins = _try_pack_items_into_bin_count(
            current_items,
            target_bin_count=len(current_bins) - 1,
            container=container,
            max_weight_kg=max_weight_kg,
            max_center_offset_mm=max_center_offset_mm,
            min_support_area_ratio=min_support_area_ratio,
        )
        if reduced_bins is None:
            break
        current_bins = reduced_bins

    return current_bins


def _try_pack_items_into_bin_count(
    items: list[WeightedItem3D],
    target_bin_count: int,
    container: Container,
    max_weight_kg: float,
    max_center_offset_mm: float,
    min_support_area_ratio: float,
) -> list[CenterBalancedBin3D] | None:
    if not items:
        return []
    if target_bin_count <= 0:
        return None

    item_key_by_identity = {
        id(item): index
        for index, item in enumerate(
            sorted(items, key=lambda candidate: (candidate.item_id, candidate.weight_kg, candidate.volume))
        )
    }
    ordered = sorted(
        items,
        key=lambda item: (
            -item.weight_kg,
            -item.volume,
            -max(item.length, item.width),
            item_key_by_identity[id(item)],
        ),
    )
    pack_cache: dict[tuple[int, ...], CenterBalancedBin3D | None] = {}
    failed_states: set[tuple[int, tuple[tuple[int, ...], ...]]] = set()

    def pack_items(bin_items: list[WeightedItem3D]) -> CenterBalancedBin3D | None:
        key = tuple(sorted(item_key_by_identity[id(item)] for item in bin_items))
        if key not in pack_cache:
            try:
                pack_cache[key] = pack_single_realistic_stable_bin(
                    bin_items,
                    container=container,
                    max_weight_kg=max_weight_kg,
                    max_center_offset_mm=max_center_offset_mm,
                    min_support_area_ratio=min_support_area_ratio,
                )
            except ValueError:
                pack_cache[key] = None
        return pack_cache[key]

    def search(
        item_index: int,
        bin_items: list[list[WeightedItem3D]],
        bin_weights: list[float],
    ) -> list[CenterBalancedBin3D] | None:
        state_key = (
            item_index,
            tuple(
                sorted(
                    tuple(sorted(item_key_by_identity[id(item)] for item in bucket))
                    for bucket in bin_items
                )
            ),
        )
        if state_key in failed_states:
            return None

        if item_index == len(ordered):
            packed_bins = [pack_items(bucket) for bucket in bin_items if bucket]
            if any(packed is None for packed in packed_bins):
                failed_states.add(state_key)
                return None
            return [packed for packed in packed_bins if packed is not None]

        item = ordered[item_index]
        seen_bucket_signatures: set[tuple[int, ...]] = set()

        for bucket_index in range(target_bin_count):
            bucket_signature = tuple(sorted(item_key_by_identity[id(existing)] for existing in bin_items[bucket_index]))
            if bucket_signature in seen_bucket_signatures:
                continue
            seen_bucket_signatures.add(bucket_signature)

            if _exceeds_weight_limit(bin_weights[bucket_index] + item.weight_kg, max_weight_kg):
                continue

            trial_bucket = bin_items[bucket_index] + [item]
            bin_items[bucket_index] = trial_bucket
            bin_weights[bucket_index] += item.weight_kg
            result = search(item_index + 1, bin_items, bin_weights)
            if result is not None:
                return result
            bin_weights[bucket_index] -= item.weight_kg
            bin_items[bucket_index] = trial_bucket[:-1]

            if not bucket_signature:
                break

        failed_states.add(state_key)
        return None

    return search(
        item_index=0,
        bin_items=[[] for _ in range(target_bin_count)],
        bin_weights=[0.0 for _ in range(target_bin_count)],
    )
