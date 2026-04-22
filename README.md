# Marketing Simulation Environment

This repository contains a high-fidelity simulation for evaluating marketing strategies.

## Features
- **Persona-based Agents**: 10 unique customer types based on demographic and psychographic data.
- **Dynamic Campaign Engine**: Models various channels (Email, Social, Search, etc.) with cost and effectiveness parameters.
- **Decision Engine**: Probabilistic modeling of agent behavior in response to marketing stimuli.
- **Comprehensive Analytics**: Generates detailed reports on campaign ROI and agent lifecycle.

## Getting Started
1. Run `make setup` to install dependencies.
2. Configure the simulation parameters in `config/simulation_params.yaml`.
3. Run the simulation using `make run`.
4. Check the results in the `results/` directory.

## Running Tests
To run the project tests, use:
```bash
make test
```