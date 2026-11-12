from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any

import numpy as np
import pandas as pd


@dataclass
class EV:
    ev_id: str
    arrival_hour: float
    departure_hour: float
    initial_soc: float
    target_soc: float
    battery_capacity_kwh: float
    max_power_kw: float
    efficiency: float = 0.92

    @property
    def required_energy_kwh(self) -> float:
        if self.target_soc <= self.initial_soc:
            return 0.0
        return self.battery_capacity_kwh * (self.target_soc - self.initial_soc) / 100.0 / self.efficiency

    def available_in_slot(self, slot_start: float, dt_hours: float) -> bool:
        slot_end = slot_start + dt_hours
        return self.arrival_hour < slot_end and self.departure_hour > slot_start


def build_time_slots(start_hour: float = 9.0, end_hour: float = 18.0, dt_hours: float = 0.25) -> List[float]:
    slots: List[float] = []
    current = start_hour
    while current < end_hour:
        slots.append(round(current, 2))
        current += dt_hours
    return slots


def create_price_profile(time_slots: List[float], scale: float = 1.0) -> List[float]:
    prices: List[float] = []
    for idx, slot in enumerate(time_slots):
        hour = slot % 24.0
        if 9.0 <= hour < 10.0:
            price = 8.0
        elif 10.0 <= hour < 11.0:
            price = 7.0
        elif 11.0 <= hour < 12.0:
            price = 6.0
        elif 12.0 <= hour < 13.0:
            price = 5.0
        elif 13.0 <= hour < 14.0:
            price = 4.0
        elif 14.0 <= hour < 15.0:
            price = 5.0
        elif 15.0 <= hour < 16.0:
            price = 6.0
        elif 16.0 <= hour < 17.0:
            price = 7.0
        elif 17.0 <= hour < 18.0:
            price = 8.5
        else:
            price = 6.5
        if idx % 2 == 0:
            price += 0.3
        prices.append(round(price * scale, 2))
    return prices


def create_solar_profile(time_slots: List[float], scale: float = 1.0) -> List[float]:
    solar: List[float] = []
    for slot in time_slots:
        hour = slot % 24.0
        if 9.0 <= hour < 10.0:
            output = 12.0
        elif 10.0 <= hour < 11.0:
            output = 28.0
        elif 11.0 <= hour < 12.0:
            output = 45.0
        elif 12.0 <= hour < 13.0:
            output = 58.0
        elif 13.0 <= hour < 14.0:
            output = 52.0
        elif 14.0 <= hour < 15.0:
            output = 42.0
        elif 15.0 <= hour < 16.0:
            output = 26.0
        elif 16.0 <= hour < 17.0:
            output = 14.0
        else:
            output = 0.0
        solar.append(round(max(0.0, output * scale), 2))
    return solar


def _ensure_feasible_ev(ev: EV) -> EV:
    if ev.target_soc <= ev.initial_soc:
        ev.target_soc = min(95.0, ev.initial_soc + 30.0)
    if ev.target_soc > 100.0:
        ev.target_soc = 100.0
    if ev.max_power_kw <= 0:
        ev.max_power_kw = 12.0
    return ev


def generate_scenario(
    num_ev: int = 10,
    seed: int = 42,
    start_hour: float = 9.0,
    end_hour: float = 18.0,
    dt_hours: float = 0.25,
    grid_capacity_kw: float = 180.0,
    ports: int = 5,
    lambda_peak: float = 25.0,
    include_solar: bool = True,
    price_scale: float = 1.0,
    solar_scale: float = 1.0,
    battery_capacity_min: float = 45.0,
    battery_capacity_max: float = 80.0,
    initial_soc_min: float = 10.0,
    initial_soc_max: float = 55.0,
    target_soc_min: float = 70.0,
    target_soc_max: float = 95.0,
    max_power_min: float = 10.0,
    max_power_max: float = 22.0,
    efficiency: float = 0.92,
) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    time_slots = build_time_slots(start_hour=start_hour, end_hour=end_hour, dt_hours=dt_hours)
    prices = create_price_profile(time_slots, scale=price_scale)
    solar = create_solar_profile(time_slots, scale=solar_scale)

    evs: List[EV] = []
    for idx in range(1, num_ev + 1):
        arrival = start_hour + rng.uniform(0.0, max(1.0, (end_hour - start_hour) / 2.0))
        duration = rng.uniform(2.0, 6.0)
        departure = min(end_hour, arrival + duration)
        if departure <= arrival + 0.5:
            departure = min(end_hour, arrival + 1.5)

        battery_capacity = float(rng.uniform(battery_capacity_min, battery_capacity_max))
        initial_soc = float(rng.uniform(initial_soc_min, initial_soc_max))
        target_soc = float(rng.uniform(target_soc_min, target_soc_max))
        max_power_kw = float(rng.uniform(max_power_min, max_power_max))

        ev = EV(
            ev_id=f"EV{idx}",
            arrival_hour=round(arrival, 2),
            departure_hour=round(departure, 2),
            initial_soc=initial_soc,
            target_soc=target_soc,
            battery_capacity_kwh=battery_capacity,
            max_power_kw=max_power_kw,
            efficiency=efficiency,
        )
        ev = _ensure_feasible_ev(ev)
        evs.append(ev)

    return {
        "evs": evs,
        "time_slots": time_slots,
        "prices": prices,
        "solar": solar if include_solar else [0.0 for _ in time_slots],
        "grid_capacity_kw": float(grid_capacity_kw),
        "ports": int(ports),
        "lambda_peak": float(lambda_peak),
        "include_solar": bool(include_solar),
        "dt_hours": float(dt_hours),
        "efficiency": float(efficiency),
        "price_scale": float(price_scale),
        "solar_scale": float(solar_scale),
        "seed": int(seed),
    }


def load_scenario_from_csv(csv_path: str | None = None, dataframe: pd.DataFrame | None = None) -> Dict[str, Any]:
    if dataframe is not None:
        df = dataframe.copy()
    elif csv_path:
        df = pd.read_csv(csv_path)
    else:
        raise ValueError("Either csv_path or dataframe must be provided.")

    required_cols = {"ev_id", "arrival_hour", "departure_hour", "initial_soc", "target_soc", "battery_capacity_kwh", "max_power_kw"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {sorted(missing)}")

    evs = []
    for row in df.to_dict(orient="records"):
        ev = EV(
            ev_id=str(row["ev_id"]),
            arrival_hour=float(row["arrival_hour"]),
            departure_hour=float(row["departure_hour"]),
            initial_soc=float(row["initial_soc"]),
            target_soc=float(row["target_soc"]),
            battery_capacity_kwh=float(row["battery_capacity_kwh"]),
            max_power_kw=float(row["max_power_kw"]),
            efficiency=float(row.get("efficiency", 0.92)),
        )
        evs.append(_ensure_feasible_ev(ev))

    time_slots = build_time_slots(start_hour=min(ev.arrival_hour for ev in evs), end_hour=max(ev.departure_hour for ev in evs), dt_hours=0.25)
    prices = create_price_profile(time_slots)
    solar = create_solar_profile(time_slots)

    return {
        "evs": evs,
        "time_slots": time_slots,
        "prices": prices,
        "solar": solar,
        "grid_capacity_kw": 180.0,
        "ports": max(1, len(evs) // 2),
        "lambda_peak": 25.0,
        "include_solar": True,
        "dt_hours": 0.25,
        "efficiency": 0.92,
        "price_scale": 1.0,
        "solar_scale": 1.0,
        "seed": 42,
    }
