"""
NBCC 2020 load combination logic (simplified ULS).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Mapping, Sequence, TYPE_CHECKING
import json

import numpy as np

if TYPE_CHECKING:
    from pint import Quantity


_ALLOWED_LOAD_TYPES = ("D", "L", "S", "W", "E")


@dataclass(frozen=True)
class LoadCombinationResult:
    """
    Structured results for factored load combinations.
    """

    names: Sequence[str]
    load_types: Sequence[str]
    factors: np.ndarray
    components: Dict[str, "Quantity"]
    total: "Quantity"
    duration_long_percent: "Quantity"
    duration_short_percent: "Quantity"


def nbcc_uls_combinations(
    nominal_loads: Mapping[str, "Quantity"],
    include_wind: bool = True,
    include_seismic: bool = False,
    combo_table_path: Path | None = None,
) -> LoadCombinationResult:
    """
    Build simplified NBCC 2020 ULS load combinations.
    """
    normalized = _normalize_nominal_loads(nominal_loads)
    load_types = _select_load_types(normalized, include_wind, include_seismic)
    base_unit = _base_unit_from_loads(normalized)

    normalized = {key: value.to(base_unit) for key, value in normalized.items()}
    for load_type in load_types:
        normalized.setdefault(load_type, 0.0 * base_unit)

    combo_defs = _load_combo_defs(combo_table_path)
    combo_defs = _filter_combo_defs(combo_defs, include_wind, include_seismic)
    names, factors = _build_factors(combo_defs, load_types)

    components = {
        load_type: factors[:, idx] * normalized[load_type]
        for idx, load_type in enumerate(load_types)
    }
    total = _sum_components(components.values())

    duration_long, duration_short = _duration_percentages(
        normalized,
        factors,
        load_types,
        long_term_keys=("D",),
        short_term_keys=("L", "S", "W", "E"),
    )

    return LoadCombinationResult(
        names=names,
        load_types=load_types,
        factors=factors,
        components=components,
        total=total,
        duration_long_percent=duration_long,
        duration_short_percent=duration_short,
    )


def _normalize_nominal_loads(nominal_loads: Mapping[str, "Quantity"]) -> Dict[str, "Quantity"]:
    if not nominal_loads:
        raise ValueError("nominal_loads must include at least one load.")

    normalized: Dict[str, "Quantity"] = {}
    for key, value in nominal_loads.items():
        if not hasattr(value, "to"):
            raise TypeError(
                f"Load '{key}' must be a pint Quantity; got {type(value).__name__}."
            )
        load_key = key.strip().upper()
        if load_key not in _ALLOWED_LOAD_TYPES:
            raise ValueError(
                f"Unsupported load key '{key}'. Supported keys: {_ALLOWED_LOAD_TYPES}."
            )
        normalized[load_key] = value

    if "D" not in normalized:
        raise ValueError("Dead load 'D' is required for NBCC ULS combinations.")

    return normalized


def _select_load_types(
    nominal_loads: Mapping[str, "Quantity"],
    include_wind: bool,
    include_seismic: bool,
) -> Sequence[str]:
    load_types = ["D", "L", "S"]
    if include_wind:
        load_types.append("W")
    if include_seismic:
        load_types.append("E")

    for load_type in nominal_loads:
        if load_type not in load_types:
            load_types.append(load_type)

    return load_types


def _base_unit_from_loads(nominal_loads: Mapping[str, "Quantity"]):
    first_load = next(iter(nominal_loads.values()))
    return first_load.units


def _load_combo_defs(combo_table_path: Path | None):
    table_path = combo_table_path or Path(__file__).resolve().parent / "tables" / "uls_combinations.json"
    with table_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    combos = payload.get("combos", [])
    if not combos:
        raise ValueError(f"No combinations found in table: {table_path}")

    return combos


def _filter_combo_defs(combo_defs, include_wind: bool, include_seismic: bool):
    filtered = []
    for combo in combo_defs:
        tags = set(combo.get("tags", []))
        if "wind" in tags and not include_wind:
            continue
        if "seismic" in tags and not include_seismic:
            continue
        filtered.append(combo)

    if not filtered:
        raise ValueError("No combinations selected after filtering.")

    return filtered


def _build_factors(combo_defs, load_types: Sequence[str]):
    names = [combo["name"] for combo in combo_defs]
    factors = np.zeros((len(combo_defs), len(load_types)))

    for combo_index, combo in enumerate(combo_defs):
        factor_map = combo.get("factors", {})
        for load_index, load_type in enumerate(load_types):
            factors[combo_index, load_index] = factor_map.get(load_type, 0.0)

    return names, factors


def _sum_components(components: Iterable["Quantity"]):
    components = list(components)
    if not components:
        raise ValueError("No components provided to sum.")

    total = components[0]
    for component in components[1:]:
        total = total + component
    return total


def _duration_percentages(
    nominal_loads: Mapping[str, "Quantity"],
    factors: np.ndarray,
    load_types: Sequence[str],
    long_term_keys: Sequence[str],
    short_term_keys: Sequence[str],
):
    base_unit = _base_unit_from_loads(nominal_loads)
    registry = next(iter(nominal_loads.values()))._REGISTRY
    nd = registry.dimensionless

    total_nominal = np.zeros(factors.shape[0])
    long_nominal = np.zeros(factors.shape[0])
    short_nominal = np.zeros(factors.shape[0])

    for load_index, load_type in enumerate(load_types):
        nominal_mag = nominal_loads[load_type].to(base_unit).magnitude
        active = factors[:, load_index] != 0.0

        total_nominal += np.where(active, nominal_mag, 0.0)
        if load_type in long_term_keys:
            long_nominal += np.where(active, nominal_mag, 0.0)
        if load_type in short_term_keys:
            short_nominal += np.where(active, nominal_mag, 0.0)

    long_percent = np.where(
        total_nominal == 0.0,
        0.0,
        100.0 * long_nominal / total_nominal,
    )
    short_percent = np.where(
        total_nominal == 0.0,
        0.0,
        100.0 * short_nominal / total_nominal,
    )

    return long_percent * nd, short_percent * nd


__all__ = ["LoadCombinationResult", "nbcc_uls_combinations"]
