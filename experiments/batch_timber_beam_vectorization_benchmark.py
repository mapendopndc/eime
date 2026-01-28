"""
Batch Timber Beam Vectorization Benchmark

Compares performance of a single load combination vs a vectorized batch
of load combinations for the TimberBeamCalculator.
"""

from __future__ import annotations

from time import perf_counter
import warnings

import numpy as np
from pint.errors import UnitStrippedWarning
from pint import UnitRegistry

from design.csa_o86_2025.calculators import TimberBeamCalculator
from design.csa_o86_2025.tables import specified_strengths, service_condition_factors


ureg = UnitRegistry()

# Unit shorthands
m = ureg.m
mm = ureg.mm
kPa = ureg.kPa
MPa = ureg.MPa
nd = ureg.dimensionless


def build_base_inputs():
    """Return shared beam/material inputs."""
    # Beam geometry
    span_m = 6.0 * m
    spacing_m = 0.4 * m
    b = 130 * mm
    d = 456 * mm
    L = span_m.to(mm)

    # Material specification
    species = "Douglas Fir-Larch"
    grade = "20f-E"
    service_condition = "Dry-service conditions"

    strengths_table = specified_strengths()
    material_props = strengths_table.data.loc[grade, species]

    f_b = material_props["f_b_pos"] * MPa
    f_v = material_props["f_v"] * MPa

    service_table = service_condition_factors()
    K_Sb = service_table.data.loc["K_Sb", service_condition] * nd
    K_Sv = service_table.data.loc["K_Sv", service_condition] * nd

    # Design factors
    phi_b = 0.9 * nd
    phi_v = 0.9 * nd
    K_H = 1.0 * nd
    K_T = 1.0 * nd
    K_x = 1.0 * nd

    return {
        "span_m": span_m,
        "spacing_m": spacing_m,
        "b": b,
        "d": d,
        "L": L,
        "f_b": f_b,
        "f_v": f_v,
        "K_Sb": K_Sb,
        "K_Sv": K_Sv,
        "phi_b": phi_b,
        "phi_v": phi_v,
        "K_H": K_H,
        "K_T": K_T,
        "K_x": K_x,
    }


def compute_load_effects(span_m, spacing_m, dead_load_kPa, live_load_kPa):
    """Compute factored effects and duration factors for loads."""
    w_dead = dead_load_kPa * spacing_m
    w_live = live_load_kPa * spacing_m
    w_factored = 1.25 * w_dead + 1.5 * w_live

    M_f = (w_factored * span_m**2) / 8
    V_f = (w_factored * span_m) / 2

    total_load = w_dead + w_live
    P_L_percent = (w_dead / total_load * 100)
    P_S_percent = (w_live / total_load * 100)

    return M_f, V_f, P_L_percent, P_S_percent


def run_single(calculator: TimberBeamCalculator, base_inputs):
    """Run a single load combination."""
    dead_load_kPa = 1.5 * kPa
    live_load_kPa = 1.9 * kPa

    M_f, V_f, P_L_percent, P_S_percent = compute_load_effects(
        base_inputs["span_m"],
        base_inputs["spacing_m"],
        dead_load_kPa,
        live_load_kPa,
    )

    return calculator.design(
        b=base_inputs["b"],
        d=base_inputs["d"],
        L=base_inputs["L"],
        f_b=base_inputs["f_b"],
        f_v=base_inputs["f_v"],
        M_f=M_f,
        V_f=V_f,
        P_L_percent=P_L_percent,
        P_S_percent=P_S_percent,
        K_H=base_inputs["K_H"],
        K_Sb=base_inputs["K_Sb"],
        K_Sv=base_inputs["K_Sv"],
        K_T=base_inputs["K_T"],
        K_x=base_inputs["K_x"],
        phi_b=base_inputs["phi_b"],
        phi_v=base_inputs["phi_v"],
    )


def run_batch(calculator: TimberBeamCalculator, base_inputs, n_cases: int):
    """Run a vectorized batch of load combinations."""
    rng = np.random.default_rng(42)
    dead_loads = rng.uniform(0.5, 2.5, size=n_cases) * kPa
    live_loads = rng.uniform(0.5, 3.5, size=n_cases) * kPa

    M_f, V_f, P_L_percent, P_S_percent = compute_load_effects(
        base_inputs["span_m"],
        base_inputs["spacing_m"],
        dead_loads,
        live_loads,
    )

    return calculator.design(
        b=base_inputs["b"],
        d=base_inputs["d"],
        L=base_inputs["L"],
        f_b=base_inputs["f_b"],
        f_v=base_inputs["f_v"],
        M_f=M_f,
        V_f=V_f,
        P_L_percent=P_L_percent,
        P_S_percent=P_S_percent,
        K_H=base_inputs["K_H"],
        K_Sb=base_inputs["K_Sb"],
        K_Sv=base_inputs["K_Sv"],
        K_T=base_inputs["K_T"],
        K_x=base_inputs["K_x"],
        phi_b=base_inputs["phi_b"],
        phi_v=base_inputs["phi_v"],
    )


def run_batch_from_arrays(
    calculator: TimberBeamCalculator,
    base_inputs,
    dead_loads,
    live_loads,
):
    """Run a vectorized batch using pre-generated load arrays."""
    M_f, V_f, P_L_percent, P_S_percent = compute_load_effects(
        base_inputs["span_m"],
        base_inputs["spacing_m"],
        dead_loads,
        live_loads,
    )

    return calculator.design(
        b=base_inputs["b"],
        d=base_inputs["d"],
        L=base_inputs["L"],
        f_b=base_inputs["f_b"],
        f_v=base_inputs["f_v"],
        M_f=M_f,
        V_f=V_f,
        P_L_percent=P_L_percent,
        P_S_percent=P_S_percent,
        K_H=base_inputs["K_H"],
        K_Sb=base_inputs["K_Sb"],
        K_Sv=base_inputs["K_Sv"],
        K_T=base_inputs["K_T"],
        K_x=base_inputs["K_x"],
        phi_b=base_inputs["phi_b"],
        phi_v=base_inputs["phi_v"],
    )


def run_loop(calculator: TimberBeamCalculator, base_inputs, dead_loads, live_loads):
    """Run a loop-based batch using scalar calculations."""
    last_result = None
    for dead_load_kPa, live_load_kPa in zip(dead_loads, live_loads):
        M_f, V_f, P_L_percent, P_S_percent = compute_load_effects(
            base_inputs["span_m"],
            base_inputs["spacing_m"],
            dead_load_kPa,
            live_load_kPa,
        )

        last_result = calculator.design(
            b=base_inputs["b"],
            d=base_inputs["d"],
            L=base_inputs["L"],
            f_b=base_inputs["f_b"],
            f_v=base_inputs["f_v"],
            M_f=M_f,
            V_f=V_f,
            P_L_percent=P_L_percent,
            P_S_percent=P_S_percent,
            K_H=base_inputs["K_H"],
            K_Sb=base_inputs["K_Sb"],
            K_Sv=base_inputs["K_Sv"],
            K_T=base_inputs["K_T"],
            K_x=base_inputs["K_x"],
            phi_b=base_inputs["phi_b"],
            phi_v=base_inputs["phi_v"],
        )

        # Avoid unbounded procedure growth during loop benchmarks
        calculator.procedures.clear()

    return last_result


def main():
    warnings.filterwarnings("error", category=UnitStrippedWarning)

    base_inputs = build_base_inputs()

    single_repeats = 10
    batch_cases = 2000

    # Warm-up
    warm_calc = TimberBeamCalculator()
    run_single(warm_calc, base_inputs)

    # Single benchmark
    single_calc = TimberBeamCalculator()
    start = perf_counter()
    for _ in range(single_repeats):
        run_single(single_calc, base_inputs)
    single_elapsed = perf_counter() - start

    rng = np.random.default_rng(42)
    dead_loads = rng.uniform(0.5, 2.5, size=batch_cases) * kPa
    live_loads = rng.uniform(0.5, 3.5, size=batch_cases) * kPa

    # Loop benchmark
    loop_calc = TimberBeamCalculator()
    start = perf_counter()
    run_loop(loop_calc, base_inputs, dead_loads, live_loads)
    loop_elapsed = perf_counter() - start

    # Batch benchmark (vectorized)
    batch_calc = TimberBeamCalculator()
    start = perf_counter()
    batch_results = run_batch_from_arrays(batch_calc, base_inputs, dead_loads, live_loads)
    batch_elapsed = perf_counter() - start

    single_avg = single_elapsed / single_repeats
    batch_per_case = batch_elapsed / batch_cases
    loop_per_case = loop_elapsed / batch_cases
    speedup = single_avg / batch_per_case if batch_per_case > 0 else float("inf")
    vector_vs_loop = loop_per_case / batch_per_case if batch_per_case > 0 else float("inf")

    print("=" * 72)
    print("TIMBER BEAM VECTOR BATCH BENCHMARK")
    print("=" * 72)
    print(f"Single case (avg over {single_repeats} runs): {single_avg:.6f} s")
    print(f"Batch cases: {batch_cases}")
    print(f"Loop total time: {loop_elapsed:.6f} s")
    print(f"Loop time per case: {loop_per_case:.6f} s")
    print(f"Batch total time: {batch_elapsed:.6f} s")
    print(f"Batch time per case: {batch_per_case:.6f} s")
    print(f"Estimated speedup (single avg / batch per case): {speedup:.1f}x")
    print(f"Vector vs loop speedup: {vector_vs_loop:.1f}x")
    print(f"Batch results shape: {batch_results.shape}")


if __name__ == "__main__":
    main()
