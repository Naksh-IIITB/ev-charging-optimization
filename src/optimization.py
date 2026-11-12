from __future__ import annotations

import os
from typing import Any, Dict, List

os.environ.setdefault("GLOG_minloglevel", "3")

import numpy as np
import pandas as pd
from ortools.linear_solver import pywraplp


def solve_optimization(
    evs: List[Any],
    time_slots: List[float],
    prices: List[float],
    grid_capacity_kw: float,
    ports: int,
    lambda_peak: float,
    include_solar: bool,
    solar_generation: List[float],
    efficiency: float,
    dt_hours: float,
) -> Dict[str, Any]:
    num_ev = len(evs)
    num_slots = len(time_slots)
    dt = dt_hours if dt_hours > 0 else 0.25

    solver = pywraplp.Solver.CreateSolver("SCIP")
    if solver is None:
        raise RuntimeError("No compatible MILP solver was found in this environment.")
    solver.SetTimeLimit(1000)
    solver.SetNumThreads(1)

    power = {
        (i, t): solver.NumVar(0.0, solver.infinity(), f"p_{i}_{t}")
        for i in range(num_ev)
        for t in range(num_slots)
    }
    charging_port = {
        (i, t): solver.IntVar(0, 1, f"z_{i}_{t}")
        for i in range(num_ev)
        for t in range(num_slots)
    }
    peak_demand = solver.NumVar(0.0, solver.infinity(), "peak_demand")
    grid_draw = {
        t: solver.NumVar(0.0, grid_capacity_kw, f"grid_draw_{t}") for t in range(num_slots)
    }
    solar_used = {
        t: solver.NumVar(0.0, solar_generation[t], f"solar_used_{t}") for t in range(num_slots)
    } if include_solar else {t: None for t in range(num_slots)}

    for i, ev in enumerate(evs):
        required = ev.required_energy_kwh
        solver.Add(sum(power[(i, t)] * dt for t in range(num_slots)) * efficiency >= required)

        for t, slot_start in enumerate(time_slots):
            if not ev.available_in_slot(slot_start, dt):
                solver.Add(charging_port[(i, t)] == 0)
            solver.Add(power[(i, t)] <= ev.max_power_kw * charging_port[(i, t)])

    for t in range(num_slots):
        solver.Add(sum(charging_port[(i, t)] for i in range(num_ev)) <= ports)
        total_load = sum(power[(i, t)] for i in range(num_ev))
        if include_solar:
            solver.Add(solar_used[t] <= solar_generation[t])
            solver.Add(solar_used[t] <= total_load)
            solver.Add(grid_draw[t] == total_load - solar_used[t])
        else:
            solver.Add(grid_draw[t] == total_load)
        solver.Add(grid_draw[t] <= grid_capacity_kw)
        solver.Add(grid_draw[t] <= peak_demand)

    objective = sum(prices[t] * grid_draw[t] * dt for t in range(num_slots)) + lambda_peak * peak_demand
    solver.Minimize(objective)
    status = solver.Solve()

    schedule = np.zeros((num_ev, num_slots))
    for i in range(num_ev):
        for t in range(num_slots):
            schedule[i, t] = power[(i, t)].solution_value() if power[(i, t)].solution_value() is not None else 0.0

    grid_schedule = np.array([
        grid_draw[t].solution_value() if grid_draw[t].solution_value() is not None else 0.0
        for t in range(num_slots)
    ])
    solar_schedule = np.array([
        solar_used[t].solution_value() if solar_used[t] is not None and solar_used[t].solution_value() is not None else 0.0
        for t in range(num_slots)
    ])
    peak_kw = float(peak_demand.solution_value() if peak_demand.solution_value() is not None else 0.0)
    objective_value = float(solver.Objective().Value()) if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE) else 0.0

    index = [ev.ev_id for ev in evs]
    schedule_df = pd.DataFrame(schedule, index=index, columns=[f"{slot:.2f}" for slot in time_slots])
    grid_df = pd.DataFrame({
        "grid_draw_kw": grid_schedule,
        "solar_used_kw": solar_schedule,
        "total_load_kw": schedule.sum(axis=0),
    }, index=[f"{slot:.2f}" for slot in time_slots])

    metrics = {
        "status": "Optimal" if status == pywraplp.Solver.OPTIMAL else "Feasible" if status == pywraplp.Solver.FEASIBLE else "Infeasible",
        "objective_value": objective_value,
        "peak_kw": peak_kw,
        "total_cost": float(np.sum(grid_schedule * np.asarray(prices) * dt)),
        "energy_delivered_kwh": float(np.sum(schedule) * dt),
        "solar_utilized_kwh": float(np.sum(solar_schedule) * dt),
    }

    for i, ev in enumerate(evs):
        delivered = float(np.sum(schedule[i, :]) * dt)
        metrics[f"ev_{ev.ev_id}_delivered_kwh"] = delivered
        metrics[f"ev_{ev.ev_id}_required_kwh"] = ev.required_energy_kwh

    return {
        "schedule_df": schedule_df,
        "grid_df": grid_df,
        "metrics": metrics,
        "peak_kw": peak_kw,
        "objective_value": objective_value,
        "status": metrics["status"],
        "power_matrix": schedule,
    }
