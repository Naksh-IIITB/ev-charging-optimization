import unittest

from src.optimization import solve_optimization
from src.scenario import generate_scenario


class OptimizationTest(unittest.TestCase):
    def test_optimization_satisfies_energy_requirements(self):
        scenario = generate_scenario(num_ev=6, seed=7, include_solar=True, ports=3, grid_capacity_kw=150.0)
        result = solve_optimization(
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

        self.assertEqual(result["status"], "Optimal")
        for ev in scenario["evs"]:
            delivered = result["schedule_df"].loc[ev.ev_id].sum() * scenario["dt_hours"]
            self.assertGreaterEqual(delivered * scenario["efficiency"], ev.required_energy_kwh * 0.99)

    def test_optimization_respects_port_capacity(self):
        scenario = generate_scenario(num_ev=5, seed=11, include_solar=False, ports=2, grid_capacity_kw=100.0)
        result = solve_optimization(
            evs=scenario["evs"],
            time_slots=scenario["time_slots"],
            prices=scenario["prices"],
            grid_capacity_kw=scenario["grid_capacity_kw"],
            ports=scenario["ports"],
            lambda_peak=scenario["lambda_peak"],
            include_solar=False,
            solar_generation=[0.0 for _ in scenario["time_slots"]],
            efficiency=scenario["efficiency"],
            dt_hours=scenario["dt_hours"],
        )

        for slot in range(len(scenario["time_slots"])):
            active = (result["schedule_df"][f"{scenario['time_slots'][slot]:.2f}"] > 1e-6).sum()
            self.assertLessEqual(active, scenario["ports"])


if __name__ == "__main__":
    unittest.main()
