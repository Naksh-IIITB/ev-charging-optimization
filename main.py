from __future__ import annotations

from pathlib import Path

from src.baselines import simulate_fcfs, simulate_uncontrolled
from src.evaluation import run_sensitivity_analysis, summarize_results
from src.optimization import solve_optimization
from src.reporting import build_academic_report, save_report
from src.scenario import generate_scenario


def run_demo() -> None:
    scenario = generate_scenario(
        num_ev=12,
        seed=42,
        include_solar=True,
        grid_capacity_kw=180.0,
        ports=5,
        lambda_peak=25.0,
        price_scale=1.0,
        solar_scale=1.0,
    )
    optimization_result = solve_optimization(
        evs=scenario["evs"],
        time_slots=scenario["time_slots"],
        prices=scenario["prices"],
        grid_capacity_kw=scenario["grid_capacity_kw"],
        ports=scenario["ports"],
        lambda_peak=scenario["lambda_peak"],
        include_solar=scenario["include_solar"],
        solar_generation=scenario["solar"],
        efficiency=scenario["efficiency"],
        dt_hours=scenario["dt_hours"],
    )

    baseline_results = {
        "uncontrolled": simulate_uncontrolled(
            scenario["evs"],
            scenario["time_slots"],
            scenario["prices"],
            scenario["grid_capacity_kw"],
            scenario["ports"],
            scenario["solar"],
            scenario["efficiency"],
            scenario["dt_hours"],
        ),
        "fcfs": simulate_fcfs(
            scenario["evs"],
            scenario["time_slots"],
            scenario["prices"],
            scenario["grid_capacity_kw"],
            scenario["ports"],
            scenario["solar"],
            scenario["efficiency"],
            scenario["dt_hours"],
        ),
    }

    sensitivity = run_sensitivity_analysis(scenario)
    report = build_academic_report(scenario, optimization_result, baseline_results, sensitivity)
    output_dir = Path(__file__).resolve().parent / "results"
    output_dir.mkdir(exist_ok=True)
    optimization_result["schedule_df"].to_csv(output_dir / "optimized_schedule.csv")
    save_report(report, output_dir)

    print(summarize_results(optimization_result, baseline_results))
    print(f"\nReport saved to: {output_dir / 'academic_report.md'}")


if __name__ == "__main__":
    run_demo()
