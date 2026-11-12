from __future__ import annotations

from typing import Any, Dict, List, Tuple

import numpy as np

from .optimization import solve_optimization


def compare_strategies(optimization_result: Dict[str, Any], baseline_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    comparison: Dict[str, Any] = {"optimized": optimization_result["metrics"], "baselines": baseline_results}
    for key, metrics in baseline_results.items():
        if metrics["metrics"]["cost"]:
            improvement = (metrics["metrics"]["cost"] - optimization_result["metrics"]["total_cost"]) / metrics["metrics"]["cost"]
            comparison[f"{key}_cost_savings_pct"] = max(0.0, improvement * 100.0)
    return comparison


def summarize_results(optimization_result: Dict[str, Any], baseline_results: Dict[str, Dict[str, Any]]) -> str:
    metrics = optimization_result["metrics"]
    lines = [
        "EV Charging Optimization Summary",
        "=" * 32,
        f"Status: {optimization_result['status']}",
        f"Total electricity cost: ₹{metrics['total_cost']:.2f}",
        f"Peak grid demand: {metrics['peak_kw']:.2f} kW",
        f"Energy delivered: {metrics['energy_delivered_kwh']:.2f} kWh",
        f"Solar utilized: {metrics['solar_utilized_kwh']:.2f} kWh",
    ]
    for name, info in baseline_results.items():
        baseline_cost = info["metrics"]["cost"]
        lines.append(f"{name.title()} baseline cost: ₹{baseline_cost:.2f}")
    return "\n".join(lines)


def run_sensitivity_analysis(scenario: Dict[str, Any]) -> Dict[str, Any]:
    grid_options = [max(80.0, scenario["grid_capacity_kw"] * 0.75), scenario["grid_capacity_kw"], scenario["grid_capacity_kw"] * 1.25]
    peak_penalties = [0.0, float(scenario["lambda_peak"])]
    port_options = [max(2, scenario["ports"] - 1), scenario["ports"], min(20, scenario["ports"] + 2)]

    results = {}
    for grid_cap in grid_options:
        for ports in port_options:
            for penalty in peak_penalties:
                key = f"grid_{grid_cap:.0f}_ports_{ports}_lambda_{penalty:.0f}"
                try:
                    optimization_result = solve_optimization(
                        evs=scenario["evs"],
                        time_slots=scenario["time_slots"],
                        prices=scenario["prices"],
                        grid_capacity_kw=float(grid_cap),
                        ports=int(ports),
                        lambda_peak=float(penalty),
                        include_solar=scenario["include_solar"],
                        solar_generation=scenario["solar"],
                        efficiency=scenario["efficiency"],
                        dt_hours=scenario["dt_hours"],
                    )
                except Exception:
                    continue
                results[key] = {
                    "grid_capacity_kw": float(grid_cap),
                    "ports": int(ports),
                    "lambda_peak": float(penalty),
                    "cost": float(optimization_result["metrics"]["total_cost"]),
                    "peak_kw": float(optimization_result["metrics"]["peak_kw"]),
                    "status": optimization_result["status"],
                }
    return results
