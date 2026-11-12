from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


def build_academic_report(scenario: Dict[str, Any], optimization_result: Dict[str, Any], baseline_results: Dict[str, Dict[str, Any]], sensitivity: Dict[str, Any] | None = None) -> str:
    metrics = optimization_result["metrics"]
    baseline_lines = []
    for name, result in baseline_results.items():
        baseline_lines.append(f"- {name.upper()}: cost ₹{result['metrics']['cost']:.2f}, peak {result['metrics']['peak_kw']:.2f} kW")

    sensitivity_lines = []
    if sensitivity:
        for label, values in sensitivity.items():
            sensitivity_lines.append(f"- {label}: {values['cost']:.2f} ₹, peak {values['peak_kw']:.2f} kW")

    report = f"""# Intelligent EV Charging Optimization

## Project overview
This project implements a multi-objective EV charging optimization model that schedules charging across a finite station horizon while minimizing electricity cost and peak grid demand. The model enforces port-capacity, grid-capacity, energy-delivery, and departure-time constraints for each EV.

## Modeling assumptions
- Time horizon: {len(scenario['time_slots'])} slots from {scenario['time_slots'][0]:.2f} to {scenario['time_slots'][-1]:.2f} hours.
- Time step: {scenario['dt_hours']:.2f} hours.
- Grid capacity: {scenario['grid_capacity_kw']:.2f} kW.
- Charging ports: {scenario['ports']}.
- Solar integration: {scenario['include_solar']}.
- Peak-demand penalty: {scenario['lambda_peak']:.2f}.
- Charging efficiency: {scenario['efficiency']:.2f}.

## Optimization objective
The optimization minimizes a weighted combination of total cost and peak demand:

min Z = \\sum c_t p_{{it}} \\Delta t + \\lambda P_{{peak}}

This objective balances cost-aware charging with grid-load smoothing and avoids excessive demand spikes.

## Core results
- Status: {optimization_result['status']}
- Total cost: ₹{metrics['total_cost']:.2f}
- Peak demand: {metrics['peak_kw']:.2f} kW
- Energy delivered: {metrics['energy_delivered_kwh']:.2f} kWh
- Solar utilized: {metrics['solar_utilized_kwh']:.2f} kWh

### Baseline comparison
{chr(10).join(baseline_lines)}

### Sensitivity summary
{chr(10).join(sensitivity_lines) if sensitivity_lines else '- No sensitivity sweep run.'}

## Interpretation
The optimized schedule shifts charging toward lower cost periods and reduces peak demand by coordinating EV charging across the available port and grid capacity. This makes the model practical for real charging stations under time-of-use tariffs and variable renewable generation.

## Limitations
- The implementation uses synthetic scenario generation unless a real EV dataset is uploaded.
- Battery states and charging sessions are approximated where exact SOC measurements are unavailable.
- The optimization remains deterministic for a given scenario and seed, which is appropriate for benchmarking and classroom use.

## Recommendation
For a production-grade deployment, combine this MILP formulation with actual ACN-style session logs, a live storage system, and a user-facing dashboard that allows operators to modify pricing, capacity, and demand constraints in near real time.
"""
    return report


def save_report(report_text: str, output_dir: str | Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "academic_report.md"
    path.write_text(report_text, encoding="utf-8")
    return path
