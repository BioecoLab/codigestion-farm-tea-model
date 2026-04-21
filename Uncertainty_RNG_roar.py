#!/usr/bin/env python
# Uncertainty_RNG_roar.py

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from scipy.stats import beta as beta_distribution, lognorm, triang
from scipy.optimize import brentq

from Inputs_g import inputs
from System_RNG_g import run_model

Feedstock_table_uncertainty = {
    'SWG': {
        'LAND': {'grass_price': (0.028, 0.032, 0.045), 'CH4_yield_grass': (100.10, 139.85, 195.39), 'CN': (17, 20, 23),
                'Moisture_grass': (0.097, 0.15, 0.19), 'VS_grass': (0.912, 0.917, 0.972), 'Carbon_grass': (0.4650, 0.4693, 0.4730),
                'Nitrogen_grass': (0.0040, 0.0046, 0.0055), 'Biomass_yield_grass': (11.19, 15.69, 18.50)},
        'CN':   {'grass_price': (0.0732, 0.090, 0.110), 'CH4_yield_grass': (100.10, 139.85, 195.39), 'CN': (17, 20, 23),
                 'Moisture_grass': (0.097, 0.15, 0.19), 'VS_grass': (0.912, 0.917, 0.972), 'Carbon_grass': (0.4650, 0.4693, 0.4730),
                'Nitrogen_grass': (0.0040, 0.0046, 0.0055), 'Biomass_yield_grass': (11.19, 15.69, 18.50)},
    },
    'CORN': {
        'LAND': {'grass_price': (0.01338, 0.01759, 0.02719), 'CH4_yield_grass': (118.99, 168.89, 239.72), 'CN': (14, 20, 23),
                 'Moisture_grass': (0.03, 0.052, 0.078), 'VS_grass': (0.8750, 0.8802, 0.9260), 'Carbon_grass': (0.4260, 0.4326, 0.4360),
                'Nitrogen_grass': (0.0050, 0.0060, 0.0064), 'Biomass_yield_grass': (11.25, 11.71, 11.85)},
        'CN':   {'grass_price': (0.06739, 0.07864, 0.10056), 'CH4_yield_grass': (118.99, 168.89, 239.72), 'CN': (14, 20, 23),
                 'Moisture_grass': (0.03, 0.052, 0.078), 'VS_grass': (0.8750, 0.8802, 0.9260), 'Carbon_grass': (0.4260, 0.4326, 0.4360),
                'Nitrogen_grass': (0.0050, 0.0060, 0.0064), 'Biomass_yield_grass': (11.25, 11.71, 11.85)},
    },
    'WR': {
        'LAND': {'grass_price':  (0.0534, 0.0552, 0.057), 'CH4_yield_grass': (127.07, 249.15, 349.5), 'CN': (12, 20, 23),
                 'Moisture_grass': (0.0197, 0.041, 0.1382), 'VS_grass': (0.8449, 0.8850, 0.9158), 'Carbon_grass': (0.25, 0.37, 0.46),
                'Nitrogen_grass': (0.01, 0.01001, 0.0101), 'Biomass_yield_grass': (6.08, 8.99, 11.90)},
        'CN':   {'grass_price': (0.110, 0.121, 0.132), 'CH4_yield_grass': (127.07, 249.15, 349.5), 'CN': (12, 20, 23),
                 'Moisture_grass': (0.0197, 0.041, 0.1382), 'VS_grass': (0.8449, 0.8850, 0.9158), 'Carbon_grass': (0.25, 0.37, 0.46),
                'Nitrogen_grass': (0.01, 0.01001, 0.0101), 'Biomass_yield_grass': (6.08, 8.99, 11.90)},
    }
}

def pert_sample(min_val, mode, max_val, size, lamb=4):
    alpha = 1 + lamb * (mode - min_val) / (max_val - min_val)
    beta_param = 1 + lamb * (max_val - mode) / (max_val - min_val)
    return min_val + (max_val - min_val) * np.random.beta(alpha, beta_param, size=size)

def solve_rin_price_brent(input_data, low=1.5, high=15.0):
    def f(price):
        local_inputs = input_data.copy()
        local_inputs['RIN_price'] = price
        return run_model(inputs(**local_inputs))['NPV']
    
    f_low = f(low)
    f_high = f(high)

    # If already profitable at the minimum RIN price → MSP = lowest price
    if f_low >= 0:
        return low

    # If NPV still negative even at high RIN price → no solution
    if f_high <= 0:
        return np.nan

    return brentq(f, low, high)

def solve_grant_brent(input_data, low=0.0, high=1.0):
    def f(grant):
        local_inputs = input_data.copy()
        local_inputs['Grant_percentage'] = grant
        return run_model(inputs(**local_inputs))['NPV']

    f_low = f(low)
    f_high = f(high)

    # If already profitable at = 0% grant
    if f_low >= 0:
        return 0.0
    
    # If even 100% grant does not fix NPV
    if f_high <= 0:
        return np.nan
    
     # Solve NPV(grant) = 0
    return brentq(f, low, high)


def sample_grass_CH4(feed, size):
    if feed == 'SWG':   # Switchgrass lognormal
        mu  = np.log(139.8565)
        sigma = 0.2609
        return lognorm(sigma, loc=0, scale=np.exp(mu)).rvs(size)

    elif feed == 'CORN':   # Corn stover lognormal
        mu  = np.log(168.8925)
        sigma = 0.2733
        return lognorm(sigma, loc=0, scale=np.exp(mu)).rvs(size)

    elif feed == 'WR':     # Winter rye triangular
        min_val = 99.82
        mode = 309.03
        max_val = 385.10
        c = (mode - min_val) / (max_val - min_val)
        return triang(c, loc=min_val, scale=max_val - min_val).rvs(size)

    else:
        raise ValueError("Unknown feedstock.")

def main(n_sims, batch_id, base_seed=42):
    # unique seed per batch
    seed = base_seed + batch_id
    np.random.seed(seed)
    print(f"Batch {batch_id}: seed = {seed}, simulations = {n_sims}")

    os.makedirs('data', exist_ok=True)

    base_inputs = inputs()

    feed = base_inputs['feedstock']      
    flow = base_inputs['feedstock_flow']      

    scenario_ranges = Feedstock_table_uncertainty[feed][flow]

    param_pert_ranges = {
        #Operating parameters
        'external_temperature': (10, 14, 18.3),
        'manure_inlet_temperature': (14.28, 20, 25.72),
        'grass_inlet_temperature': (10, 14, 18.3),
        'water_inlet_temperature': (7.14, 10, 12.86),
        'Total_solids_digester': (0.08, 0.1, 0.12),
        'HRT': (15, 22, 30),
        'Cap_factor': (0.92, 0.95, 0.98),
        'solid_digestate_price': (0.02820, 0.03525, 0.04230),
        'km_to_pipeline': (1, 2, 3),
        #Manure properties
        'CH4_yield_manure': (95, 134.15, 166.3),
        'Lactating_cows': (0.77, 0.85, 0.86),
        'Manure_moisture_lactating': (0.777, 0.87, 0.881),
        'Manure_moisture_dry': (0.777, 0.87, 0.881),
        'Manure_VS_lactating': (0.0912, 0.1090, 0.1100),
        'Manure_VS_dry': (0.0912, 0.111, 0.1100),
        'Manure_Carbon_lactating': (0.05017, 0.060, 0.061),
        'Manure_Carbon_dry': (0.05017, 0.061, 0.061),
        'Manure_Nitrogen_lactating': (0.004824, 0.007, 0.007),
        'Manure_Nitrogen_dry': (0.004824, 0.006, 0.007),
        #Grasses properties
        'CN': scenario_ranges['CN'],
        'grass_price': scenario_ranges['grass_price'],
        'Moisture_grass': scenario_ranges['Moisture_grass'],
        'VS_grass': scenario_ranges['VS_grass'], 
        'Carbon_grass': scenario_ranges['Carbon_grass'],
        'Nitrogen_grass': scenario_ranges['Nitrogen_grass'],
        'Biomass_yield_grass': scenario_ranges['Biomass_yield_grass'],
    }


    samples = {
        k: pert_sample(*v, size=n_sims)
        for k, v in param_pert_ranges.items()
    }
    # lognormal for natural gas price
    samples['Natural_gas_price'] = lognorm.rvs(0.3113, loc=0.0, scale=4.7365, size=n_sims)
    # beta for RIN price
    samples['RIN_price'] = 1.5 + (3.5 - 1.5) * beta_distribution.rvs(2.3508, 1.2442, size=n_sims)
    # beta for electricity price
    samples['electricity_price'] = ((14.09 + (18.58 - 14.09) * beta_distribution.rvs(0.6739, 0.4036, size=n_sims))/ 100)
    samples['CH4_yield_grass'] = sample_grass_CH4(feed, n_sims)


    results = []
    for i in range(n_sims):
        try:
            input_vals = {k: samples[k][i] for k in samples}
            data = inputs(**input_vals)

            res = run_model(data)

            rin_msp = solve_rin_price_brent(input_vals)
            min_grant = solve_grant_brent(input_vals)

            results.append({
                **input_vals,
                **res,
                'Minimum_RIN_price': rin_msp,
                'Minimum_Grant_percentage': min_grant
            })

        except Exception as e:
            print(f"  Simulation {i+1} failed: {e}")

    # save CSV
    df = pd.DataFrame(results)
    out_csv = f"data/uncertainty_results_batch_{batch_id}.csv"
    df.to_csv(out_csv, index=False)
    print(f"Batch {batch_id} wrote {len(df)} rows to {out_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Monte Carlo uncertainty")
    parser.add_argument("--n-sims",   type=int, required=True,
                        help="Number of simulations in this batch")
    parser.add_argument("--batch-id", type=int, required=True,
                        help="Unique batch ID (for seeding & output naming)")
    args = parser.parse_args()
    main(args.n_sims, args.batch_id)
