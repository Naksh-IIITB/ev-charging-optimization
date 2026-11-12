# Intelligent EV Charging Optimization

This project implements the EV charging optimization blueprint described in the specification: a MILP-based scheduler that minimizes electricity cost and peak grid demand while ensuring each EV receives enough energy before departure.

## Features

- Multi-EV scheduling with limited charging ports
- Grid-capacity and peak-demand constraints
- Time-of-use electricity pricing
- Optional solar energy integration
- Baseline comparison against uncontrolled and FCFS scheduling
- Streamlit dashboard for interactive experimentation

## Project structure

```text
EV-Charging-Optimization/
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── results/
├── src/
│   ├── __init__.py
│   ├── baselines.py
│   ├── dashboard.py
│   ├── evaluation.py
│   ├── optimization.py
│   └── scenario.py
└── tests/
    └── test_optimization.py
```

## Quick start

```bash
cd EV-Charging-Optimization
python3 -m pip install -r requirements.txt
python3 main.py
streamlit run app.py
```

## Optimization model

The scheduler solves a mixed-integer linear program where:

- `p[i, t]` is the power assigned to EV `i` at slot `t`
- `z[i, t]` is a binary port-assignment variable
- `peak_demand` tracks maximum system load
- Electricity cost is minimized with a peak-demand penalty
- Energy-delivery constraints ensure each EV reaches target state of charge before departure

## Example result

The optimization output includes:

- cost savings relative to uncontrolled and FCFS baselines
- peak-demand reduction
- charge schedule per EV and time slot
- solar utilization when enabled

## Notes

This implementation uses synthetic data inspired by the specification while keeping the optimization logic grounded in the MILP formulation.
