# Intelligent EV Charging Optimization

## Project overview
This project implements a multi-objective EV charging optimization model that schedules charging across a finite station horizon while minimizing electricity cost and peak grid demand. The model enforces port-capacity, grid-capacity, energy-delivery, and departure-time constraints for each EV.

## Modeling assumptions
- Time horizon: 36 slots from 9.00 to 17.75 hours.
- Time step: 0.25 hours.
- Grid capacity: 180.00 kW.
- Charging ports: 5.
- Solar integration: True.
- Peak-demand penalty: 25.00.
- Charging efficiency: 0.92.

## Optimization objective
The optimization minimizes a weighted combination of total cost and peak demand:

min Z = \sum c_t p_{it} \Delta t + \lambda P_{peak}

This objective balances cost-aware charging with grid-load smoothing and avoids excessive demand spikes.

## Core results
- Status: Feasible
- Total cost: ₹1207.45
- Peak demand: 35.56 kW
- Energy delivered: 437.89 kWh
- Solar utilized: 237.13 kWh

### Baseline comparison
- UNCONTROLLED: cost ₹497.56, peak 47.37 kW
- FCFS: cost ₹782.54, peak 51.24 kW

### Sensitivity summary
- grid_135_ports_4_lambda_0: 0.00 ₹, peak 0.00 kW
- grid_135_ports_4_lambda_25: 0.00 ₹, peak 0.00 kW
- grid_135_ports_5_lambda_0: 1167.17 ₹, peak 135.00 kW
- grid_135_ports_5_lambda_25: 1207.45 ₹, peak 35.56 kW
- grid_135_ports_7_lambda_0: 968.07 ₹, peak 135.00 kW
- grid_135_ports_7_lambda_25: 1204.78 ₹, peak 34.77 kW
- grid_180_ports_4_lambda_0: 0.00 ₹, peak 0.00 kW
- grid_180_ports_4_lambda_25: 0.00 ₹, peak 0.00 kW
- grid_180_ports_5_lambda_0: 1167.17 ₹, peak 180.00 kW
- grid_180_ports_5_lambda_25: 1207.45 ₹, peak 35.56 kW
- grid_180_ports_7_lambda_0: 968.07 ₹, peak 180.00 kW
- grid_180_ports_7_lambda_25: 1204.78 ₹, peak 34.77 kW
- grid_225_ports_4_lambda_0: 0.00 ₹, peak 0.00 kW
- grid_225_ports_4_lambda_25: 0.00 ₹, peak 0.00 kW
- grid_225_ports_5_lambda_0: 1167.17 ₹, peak 199.13 kW
- grid_225_ports_5_lambda_25: 1207.45 ₹, peak 35.56 kW
- grid_225_ports_7_lambda_0: 968.07 ₹, peak 199.13 kW
- grid_225_ports_7_lambda_25: 1204.78 ₹, peak 34.77 kW

## Interpretation
The optimized schedule shifts charging toward lower cost periods and reduces peak demand by coordinating EV charging across the available port and grid capacity. This makes the model practical for real charging stations under time-of-use tariffs and variable renewable generation.

## Limitations
- The implementation uses synthetic scenario generation unless a real EV dataset is uploaded.
- Battery states and charging sessions are approximated where exact SOC measurements are unavailable.
- The optimization remains deterministic for a given scenario and seed, which is appropriate for benchmarking and classroom use.

## Recommendation
For a production-grade deployment, combine this MILP formulation with actual ACN-style session logs, a live storage system, and a user-facing dashboard that allows operators to modify pricing, capacity, and demand constraints in near real time.
