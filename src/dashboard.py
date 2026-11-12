from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from .baselines import simulate_fcfs, simulate_uncontrolled
from .evaluation import run_sensitivity_analysis, summarize_results
from .optimization import solve_optimization
from .reporting import build_academic_report, save_report
from .scenario import generate_scenario, load_scenario_from_csv


def _compute_scenario_and_results(config: dict):
    scenario = generate_scenario(
        num_ev=int(config["num_ev"]),
        seed=int(config["seed"]),
        start_hour=float(config["start_hour"]),
        end_hour=float(config["end_hour"]),
        dt_hours=float(config["dt_hours"]),
        grid_capacity_kw=float(config["grid_capacity_kw"]),
        ports=int(config["ports"]),
        lambda_peak=float(config["lambda_peak"]),
        include_solar=bool(config["include_solar"]),
        price_scale=float(config["price_scale"]),
        solar_scale=float(config["solar_scale"]),
        battery_capacity_min=float(config["battery_capacity_min"]),
        battery_capacity_max=float(config["battery_capacity_max"]),
        initial_soc_min=float(config["initial_soc_min"]),
        initial_soc_max=float(config["initial_soc_max"]),
        target_soc_min=float(config["target_soc_min"]),
        target_soc_max=float(config["target_soc_max"]),
        max_power_min=float(config["max_power_min"]),
        max_power_max=float(config["max_power_max"]),
        efficiency=float(config["efficiency"]),
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
    return scenario, optimization_result, baseline_results, sensitivity


def render_dashboard() -> None:
    st.set_page_config(page_title="Intelligent EV Charging Optimization", layout="wide")
    st.title("Intelligent EV Charging Optimization")
    st.caption("Research-ready MILP scheduling interface for cost-aware EV charging")

    with st.sidebar:
        st.header("Scenario controls")
        config = {
            "num_ev": st.slider("Number of EVs", 5, 40, 12),
            "seed": st.number_input("Random seed", min_value=1, max_value=1000, value=42, step=1),
            "start_hour": st.slider("Start hour", 6.0, 10.0, 9.0, step=0.5),
            "end_hour": st.slider("End hour", 14.0, 24.0, 18.0, step=0.5),
            "dt_hours": st.selectbox("Time step", [0.25, 0.5, 1.0], index=0),
            "ports": st.slider("Charging ports", 2, 18, 5),
            "grid_capacity_kw": st.slider("Grid capacity (kW)", 80, 500, 180),
            "lambda_peak": st.slider("Peak-demand penalty", 0.0, 200.0, 25.0, step=1.0),
            "include_solar": st.checkbox("Include solar generation", value=True),
            "price_scale": st.slider("Price scale", 0.5, 2.0, 1.0, step=0.1),
            "solar_scale": st.slider("Solar scale", 0.0, 2.0, 1.0, step=0.1),
            "battery_capacity_min": st.slider("Battery capacity min (kWh)", 30, 80, 45, step=1),
            "battery_capacity_max": st.slider("Battery capacity max (kWh)", 40, 100, 80, step=1),
            "initial_soc_min": st.slider("Initial SOC min (%)", 5, 40, 10, step=1),
            "initial_soc_max": st.slider("Initial SOC max (%)", 20, 70, 55, step=1),
            "target_soc_min": st.slider("Target SOC min (%)", 60, 95, 70, step=1),
            "target_soc_max": st.slider("Target SOC max (%)", 70, 100, 95, step=1),
            "max_power_min": st.slider("EV max power min (kW)", 5.0, 20.0, 10.0, step=0.5),
            "max_power_max": st.slider("EV max power max (kW)", 10.0, 40.0, 22.0, step=0.5),
            "efficiency": st.slider("Charging efficiency", 0.75, 1.0, 0.92, step=0.01),
        }

        uploaded_file = st.file_uploader("Upload EV CSV (optional)", type=["csv"])
        if uploaded_file is not None:
            csv_df = pd.read_csv(uploaded_file)
            custom_scenario = load_scenario_from_csv(dataframe=csv_df)
            st.success(f"Loaded {len(custom_scenario['evs'])} EVs from uploaded CSV.")
            scenario_to_use = custom_scenario
        else:
            scenario_to_use = None

    if scenario_to_use is not None:
        scenario = scenario_to_use
    else:
        scenario, optimization_result, baseline_results, sensitivity = _compute_scenario_and_results(config)

    if scenario_to_use is not None:
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

    tabs = st.tabs(["Optimization", "Sensitivity analysis", "Academic report"])
    with tabs[0]:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total cost", f"₹{optimization_result['metrics']['total_cost']:.2f}")
        col2.metric("Peak demand", f"{optimization_result['metrics']['peak_kw']:.2f} kW")
        col3.metric("Energy delivered", f"{optimization_result['metrics']['energy_delivered_kwh']:.2f} kWh")
        col4.metric("Solar used", f"{optimization_result['metrics']['solar_utilized_kwh']:.2f} kWh")

        st.subheader("Optimization summary")
        st.code(summarize_results(optimization_result, baseline_results), language="text")

        st.subheader("Optimized EV charging schedule")
        st.dataframe(optimization_result["schedule_df"].round(2), use_container_width=True)

        st.subheader("Grid load comparison")
        load_df = pd.DataFrame(
            {
                "Uncontrolled": baseline_results["uncontrolled"]["power_matrix"].sum(axis=0),
                "FCFS": baseline_results["fcfs"]["power_matrix"].sum(axis=0),
                "Optimized": optimization_result["schedule_df"].sum(axis=0).to_numpy(),
            },
            index=[f"{slot:.2f}" for slot in scenario["time_slots"]],
        )
        st.line_chart(load_df)

        st.subheader("Fleet requirements")
        ev_table = pd.DataFrame(
            [
                {
                    "EV": ev.ev_id,
                    "Arrival": ev.arrival_hour,
                    "Departure": ev.departure_hour,
                    "Initial SOC": ev.initial_soc,
                    "Target SOC": ev.target_soc,
                    "Required energy (kWh)": round(ev.required_energy_kwh, 2),
                    "Max power (kW)": round(ev.max_power_kw, 2),
                }
                for ev in scenario["evs"]
            ]
        )
        st.dataframe(ev_table, use_container_width=True)

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(scenario["time_slots"], scenario["prices"], label="Price (₹/kWh)", color="tab:blue")
        ax.plot(scenario["time_slots"], scenario["solar"], label="Solar (kW)", color="tab:green")
        ax.legend()
        ax.set_title("Electricity price and solar profile")
        ax.set_xlabel("Time (hours)")
        ax.set_ylabel("Value")
        st.pyplot(fig)

    with tabs[1]:
        sensitivity_df = pd.DataFrame([
            {
                "grid_capacity_kw": values["grid_capacity_kw"],
                "ports": values["ports"],
                "lambda_peak": values["lambda_peak"],
                "cost": values["cost"],
                "peak_kw": values["peak_kw"],
            }
            for values in sensitivity.values()
        ])
        st.dataframe(sensitivity_df.sort_values("cost"), use_container_width=True)

        if not sensitivity_df.empty:
            fig2, ax2 = plt.subplots(figsize=(10, 5))
            ax2.scatter(sensitivity_df["grid_capacity_kw"], sensitivity_df["cost"], c=sensitivity_df["lambda_peak"], cmap="viridis")
            ax2.set_title("Sensitivity: cost vs grid capacity")
            ax2.set_xlabel("Grid capacity (kW)")
            ax2.set_ylabel("Cost (₹)")
            st.pyplot(fig2)

    with tabs[2]:
        report = build_academic_report(scenario, optimization_result, baseline_results, sensitivity)
        st.markdown(report)
        report_path = save_report(report, Path("results"))
        st.success(f"Academic report saved to: {report_path}")
        st.download_button("Download report", data=report, file_name="academic_report.md", mime="text/markdown")


if __name__ == "__main__":
    render_dashboard()
