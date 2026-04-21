
'REACTIONS'

import numpy as np


# Universal gas constant in L·atm/mol·K
R = 0.08205746

def ideal_gas_volume_mL(T_K):

    # #Returns gas volume (mL) of 1 mol ideal gas at given T=37°C (K) and P= 1atm (atm) - treating CH4 and CO2 as ideal gases
    Gas_volume = (1 * R * T_K) * 1000
    return {'Gas_volume': Gas_volume}   # mol

def biogas_methane_conversions(manure_flowrate, grass_flowrate, manure_vsolids, grass_vsolids, CH4_yield_manure, CH4_yield_grass, Gas_volume):
    
    # Total VS input (g/hr)
    VS_solids = (((manure_flowrate * 1000) * manure_vsolids) +
                 ((grass_flowrate * 1000) * grass_vsolids))
     
    VS_solids_manure = ((manure_flowrate * 1000) * manure_vsolids) # g VS from manure
    VS_solids_grass = ((grass_flowrate * 1000) * grass_vsolids) # g VS from grass

    CH4_volume = (CH4_yield_manure * VS_solids_manure) + (CH4_yield_grass * VS_solids_grass)  # mL CH4
    CH4_yield = CH4_volume / VS_solids  # mL CH4/g VS overall methane yield
    CH4_mass_yield = ((CH4_yield / Gas_volume)*16)  #Mass (g) of CH4 per g VS
    biogas_volume = ((CH4_yield / 0.6) * VS_solids)  # Assuming 60% CH4 - mL biogas
    CO2_volume = biogas_volume - CH4_volume #Calculates CO2 yield in mL based on the difference between biogas and methane.
    CO2_yield = CO2_volume / VS_solids # mL CO2/g VS
    CO2_mass_yield = ((CO2_yield / Gas_volume) * 44)  # g CO2 / g VS

    return {
        'CH4_yield': CH4_yield,
        'CH4_mass_yield': CH4_mass_yield,
        'CH4_volume': CH4_volume,
        'CO2_volume': CO2_volume,
        'CO2_mass_yield': CO2_mass_yield,
        'biogas_volume': biogas_volume,
    }
