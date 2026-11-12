from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
import pandas as pd


def _feasible_power_for_ev(ev: Any, remaining_energy_kwh: float, dt_hours: float, grid_remaining_kw: float, slot_port_usage: int, ports: int) -> float:
    max_by_energy = remaining_energy_kwh / (dt_hours * ev.efficiency)
    max_by_ev = ev.max_power_kw
    max_by_port = max(0.0, (ports - slot_port_usage) * ev.max_power_kw)
    return max(0.0, min(max_by_energy, max_by_ev, max_by_port, grid_remaining_kw))


def simulate_uncontrolled(
    evs: List[Any],
    time_slots: List[float],
    prices: List[float],
    grid_capacity_kw: float,
    ports: int,
    solar_generation: List[float],
    efficiency: float,
    dt_hours: float,
) -> Dict[str, Any]:
    schedule = np.zeros((len(evs), len(time_slots)))
    remaining = [ev.required_energy_kwh for ev in evs]
    current_port_usage = np.zeros(len(time_slots), dtype=int)
    for t_idx, slot_start in enumerate(time_slots):
        active = [idx for idx, ev in enumerate(evs) if ev.available_in_slot(slot_start, dt_hours) and remaining[idx] > 1e-9]
        if not active:
            continue
        grid_remaining = grid_capacity_kw
        sorted_active = sorted(active, key=lambda idx: evs[idx].departure_hour, reverse=True)
        for idx in sorted_active:
            if current_port_usage[t_idx] >= ports:
                break
            ev = evs[idx]
            power_limit = _feasible_power_for_ev(ev, remaining[idx], dt_hours, grid_remaining, current_port_usage[t_idx], ports)
            if power_limit <= 0:
                continue
            schedule[idx, t_idx] = power_limit
            remaining[idx] -= power_limit * dt_hours * efficiency
            grid_remaining -= power_limit
            current_port_usage[t_idx] += 1

    return {
        "schedule_df": pd.DataFrame(schedule, index=[ev.ev_id for ev in evs], columns=[f"{slot:.2f}" for slot in time_slots]),
        "metrics": _summarize_metrics(schedule, evs, time_slots, prices, grid_capacity_kw, solar_generation, efficiency, dt_hours),
        "power_matrix": schedule,
    }


def simulate_fcfs(
    evs: List[Any],
    time_slots: List[float],
    prices: List[float],
    grid_capacity_kw: float,
    ports: int,
    solar_generation: List[float],
    efficiency: float,
    dt_hours: float,
) -> Dict[str, Any]:
    schedule = np.zeros((len(evs), len(time_slots)))
    remaining = [ev.required_energy_kwh for ev in evs]
    order = sorted(range(len(evs)), key=lambda idx: (evs[idx].arrival_hour, evs[idx].departure_hour))
    for t_idx, slot_start in enumerate(time_slots):
        grid_remaining = grid_capacity_kw
        port_usage = sum(1 for i in range(len(evs)) if schedule[i, t_idx] > 0)
        active = [idx for idx in order if evs[idx].available_in_slot(slot_start, dt_hours) and remaining[idx] > 1e-9]
        for idx in active:
            if port_usage >= ports:
                break
            ev = evs[idx]
            power_limit = _feasible_power_for_ev(ev, remaining[idx], dt_hours, grid_remaining, port_usage, ports)
            if power_limit <= 0:
                continue
            schedule[idx, t_idx] = power_limit
            remaining[idx] -= power_limit * dt_hours * efficiency
            grid_remaining -= power_limit
            port_usage += 1
    return {
        "schedule_df": pd.DataFrame(schedule, index=[ev.ev_id for ev in evs], columns=[f"{slot:.2f}" for slot in time_slots]),
        "metrics": _summarize_metrics(schedule, evs, time_slots, prices, grid_capacity_kw, solar_generation, efficiency, dt_hours),
        "power_matrix": schedule,
    }


def _summarize_metrics(
    schedule: np.ndarray,
    evs: List[Any],
    time_slots: List[float],
    prices: List[float],
    grid_capacity_kw: float,
    solar_generation: List[float],
    efficiency: float,
    dt_hours: float,
) -> Dict[str, float]:
    total_load = schedule.sum(axis=0)
    solar_available = np.asarray(solar_generation)
    grid_draw = np.maximum(total_load - solar_available, 0.0)
    peak = float(np.max(grid_draw)) if grid_draw.size else 0.0
    energy_delivered = float(np.sum(schedule) * dt_hours)
    cost = float(np.sum(grid_draw * np.asarray(prices) * dt_hours))
    return {
        "cost": cost,
        "peak_kw": peak,
        "total_energy_kwh": energy_delivered,
        "grid_empty": float(np.sum(grid_draw)),
        "solar_utilized_kwh": float(np.sum(np.minimum(total_load, solar_available)) * dt_hours),
        "grid_capacity_kw": float(grid_capacity_kw),
    }
