# Lignocellulosic biomass co-digestion in dairy farms

**Authors:** Camila Valderrama, Elmin Rahic, Hunter Porcano, Juliana Vasco-Correa

[BioSTEAM](https://biosteam.readthedocs.io/en/latest/index.html)-based models for techno-economic and uncertainty analysis of anaerobic digestion systems using dairy manure and lignocellulosic co-digestion. Supports electricity and renewable natural gas pathways with modules for simulation, cost estimation, and Monte Carlo analysis.

## Overview
In this study, we propose a co-digestion system of dairy manure with switchgrass, winter rye, and corn stover in a dairy farm setting, referred to as ["Grass-to-Gas"](https://cchange.research.iastate.edu/grass2gas) (G2G). A BioSTEAM process model was developed to simulate farm-scale anaerobic digestion (AD) systems under multiple feedstock and process configurations. Two biomass supply conditions were evaluated: biomass grown on-farm and biomass purchased externally. Energy conversion pathways included electricity generation via combined heat and power (CHP) unit and renewable natural gas (RNG) production through biogas upgrading.

![Process flow diagram](/docs/images/RNG_model.png)

## Scenarios
- System: 1,000-cow dairy farm
- Pathways:
  - CHP -> combined heat and power (electricity and heat)
  - RNG -> renewable natural gas
- Feedstocks ('feedstock' in [Inputs_g.py](Inputs_g.py)):
  - CORN -> corn stover
  - SWG -> switchgrass
  - WR -> winter rye
  - Manure -> dairy manure only
- Biomass supply ('feedstock_flow' in [Inputs_g.py](Inputs_g.py)):
  - LAND -> on-farm production
  - CN -> external purchase


## Repository structure
[System_CHP_g.py](System_CHP_g.py): Builds and simulates the AD system for electricity generation via CHP.

[System_RNG_g.py](System_RNG_g.py): Builds and simulates the AD system for RNG production.

[Chemicals_g.py](Chemicals_g.py): Defines chemical components and thermodynamic properties used across all AD models.

[Inputs_g.py](Inputs_g.py): Centralizes and resolves all model inputs, assumptions, and scenario parameters.

[Process_settings_g.py](Process_settings_g.py): Calculates thermal properties for energy and heat balance in the AD system.

[Reactions_g.py](Reactions_g.py): Estimates biogas production using yield-based methane generation from feedstocks.

[Stream_g.py](Stream_g.py): Creates BioSTEAM stream objects from feedstock, farm, and composition data.

[TEA_g.py](TEA_g.py): Implements techno-economic analysis to compute financial performance metrics.

[Units_g.py](Units_g.py): Defines custom process units and cost models for the AD system.

## Getting started
To run the model:
1. Modify input parameters in [Inputs_g.py](Inputs_g.py) (e.g., feedstock, biomass supply, herd size).
2. Run the desired system script:
    - [System_CHP_g.py](System_CHP_g.py) for electricity simulations.
    - [System_RNG_g.py](System_RNG_g.py) for renewable natural gas simulations.
3. Results (e.g., NPV, IRR, TCI, production metrics) are generated from the system simulation.

## How to cite:
Valderrama, C.; Rahic, E.; Porcano, H.; Vasco-Correa, J. (2026). *Lignocellulosic biomass co-digestion in dairy farms*. GitHub repository. https://github.com/BioecoLab/codigestion-farm-tea-model (accessed Month Day, Year).

## Related publications:
Valderrama, C. (2026). Techno-economic feasibility study of renewable natural gas production for dairy farms (Master’s thesis, The Pennsylvania State University).

Valderrama C, Rahic E, Porcano H, et al (2026) Data for: Feasibility of Grass-to-Gas on Dairy Farms: A Probabilistic Techno-Economic Comparison of Renewable Natural Gas and Electricity Production [Data set]. ScholarSphere. https://doi.org/10.26207/h8ad-e347

