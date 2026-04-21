'Inputs'

from scipy.optimize import fsolve

def inputs(**kwargs):
    
    #Feedstock prices and values
    Feedstock_table = {
        'SWG': { #Switchgrass
            'LAND': {'grass_price': 32/1000, 'CH4_yield_grass': 139.86, 'CN':20,
                     'Moisture_grass': 0.15, 'VS_grass': 0.917, 'Carbon_grass': 0.4693,
                     'Nitrogen_grass': 0.0046, 'Biomass_yield_grass': 15.69},
            'CN': {'grass_price': 90/1000, 'CH4_yield_grass': 139.86, 'CN':30,
                     'Moisture_grass': 0.15, 'VS_grass': 0.917, 'Carbon_grass': 0.4693,
                     'Nitrogen_grass': 0.0046, 'Biomass_yield_grass': 15.69},
            },
        'CORN': { #Corn stover
            'LAND': {'grass_price': 17.59/1000, 'CH4_yield_grass': 168.89, 'CN':20,
                     'Moisture_grass': 0.052, 'VS_grass': 0.8802, 'Carbon_grass': 0.4326,
                     'Nitrogen_grass': 0.006, 'Biomass_yield_grass': 11.71},
            'CN': {'grass_price': 78.64/1000, 'CH4_yield_grass': 168.89, 'CN':26.35,
                     'Moisture_grass': 0.052, 'VS_grass': 0.8802, 'Carbon_grass': 0.4326,
                     'Nitrogen_grass': 0.006, 'Biomass_yield_grass': 11.71},
            },
        'WR': { #Winter rye
            'LAND': {'grass_price': 55.2/1000, 'CH4_yield_grass': 249.15, 'CN':20,
                     'Moisture_grass': 0.041, 'VS_grass': 0.885, 'Carbon_grass': 0.37,
                     'Nitrogen_grass': 0.01, 'Biomass_yield_grass': 8.99},
            'CN': {'grass_price': 121/1000, 'CH4_yield_grass': 249.15, 'CN':19.77,
                   'Moisture_grass': 0.041, 'VS_grass': 0.885, 'Carbon_grass': 0.37,
                     'Nitrogen_grass': 0.01, 'Biomass_yield_grass': 8.99},
            },
    }
    
    # Define defaults
    
    default = {
        
        #SCENARIO DEFINITION
        'cows': 1000,
        
        'feedstock': 'WR', #CORN = Corn stover, SWG = Switchgrass, WR = Winter rye
        'feedstock_flow': 'CN', #CN = Purchased scenario, LAND = farm-grown scenario
        
        #OPERATIONAL PARAMETERS

        'manure_inlet_temperature': 20, #°C
        'grass_inlet_temperature': 14, #°C
        'water_inlet_temperature': 10, #°C
        'external_temperature': 14, #°C
        'Total_solids_digester':0.10, #10% of total solids in the digester
        'HRT': 22, # Desired Hydraulic Retention Time in days
        'Temperature_digester': 37, #°C
        'Cap_factor': 0.95, #0.95 Assumption of the capacity factor of the plant with employees on site
        'CHP_efficiency': 0.685, #68.5% Assumption of the overall efficiency of the CHP unit
        'CHP_elec_efficiency': 0.35, #35% Assumption of the electricity efficiency of the CHP unit

        #METHANE YIELDS
        'CH4_yield_manure': 134.15, #mL CH4/g VS
        'CH4_yield_grass': None, #mL CH4/g VS, depends on grass type

        #PRICE AND ECONOMIC PARAMETERS
        
        'RIN_price': 2.97, #$/gal
        'solid_digestate_price': 0.03525, #$/kg
        'liquid_digestate_price': 0,
        'electricity_price': 0.1733, #$/kWh
        'water_price': 0.00295, #$/gal
        'manure_price': 0,
        'Natural_gas_price': 4.29, #$/1000 cubic feet
        'km_to_pipeline': 2, #km
        'grass_price': None, #$/kg

        'Grant_percentage': 0, #%0.5 = 50% grant

        #FEEDSTOCK CHARACTERISTICS
        #DAIRY MANURE

        'Lactating_cows': 0.85, #Percentage of lactating cows in the farm
        'Manure_moisture_lactating': 0.87, #Percentage of moisture in lactating cows
        'Manure_moisture_dry': 0.87, #Percentage of moisture in dry cows
        'Manure_VS_lactating': 0.109, #Percentage % w.b. of VS in lactating cows
        'Manure_VS_dry': 0.111, #Percentage % w.b. of VS in dry cows
        'Manure_Carbon_lactating': 0.060, #Percentage of carbon in lactating cows (% of w.b.)
        'Manure_Carbon_dry': 0.061, #Percentage of carbon in dry cows (% of w.b.)
        'Manure_Nitrogen_lactating': 0.007, #Percentage of carbon in lactating cows % w.b.
        'Manure_Nitrogen_dry': 0.006, #Percentage of nitrogen in dry cows % d.m.

        #GRASS

        'CN': None, #CN ratio to achieve, for CN ratio scenario
        'Moisture_grass': None, #Percentage of moisture in grass % w.b.
        'VS_grass': None, #Percentage of volatile solids in grass % w.b. or % of d.m. depends on grass, see Stream.py
        'Carbon_grass': None, #Percentage of carbon in grass % w.b.
        'Nitrogen_grass': None, #Percentage of nitrogen in grass % w.b.
        'Biomass_yield_grass': None, #Percentage of biomass yield in grass Mg/ha

    }
    default.update(kwargs)

    feedstock = default['feedstock']
    flow = default['feedstock_flow']

    table_props = Feedstock_table[feedstock][flow]

    if 'grass_price' not in kwargs or default['grass_price'] is None:
        default['grass_price'] = table_props['grass_price']

    if 'CH4_yield_grass' not in kwargs or default['CH4_yield_grass'] is None:
        default['CH4_yield_grass'] = table_props['CH4_yield_grass']

    if 'CN' not in kwargs or default['CN'] is None:
        default['CN'] = table_props['CN']

    if 'Moisture_grass' not in kwargs or default['Moisture_grass'] is None:
        default['Moisture_grass'] = table_props['Moisture_grass']
    
    if 'VS_grass' not in kwargs or default['VS_grass'] is None:
        default['VS_grass'] = table_props['VS_grass']
    
    if 'Carbon_grass' not in kwargs or default['Carbon_grass'] is None:
        default['Carbon_grass'] = table_props['Carbon_grass']

    if 'Nitrogen_grass' not in kwargs or default['Nitrogen_grass'] is None:
        default['Nitrogen_grass'] = table_props['Nitrogen_grass']

    if 'Biomass_yield_grass' not in kwargs or default['Biomass_yield_grass'] is None:
        default['Biomass_yield_grass'] = table_props['Biomass_yield_grass']

    return default


def get_stream_prices(water_price,
                      manure_price,
                      RIN_price,
                      solid_digestate_price,
                      liquid_digestate_price,
                      Natural_gas_price,):
    
    water_price = water_price * (1 / (0.003785 * 1000))  # $/kg

    'RIN price'
    Energy_content_ethanol = 75583 #BTU/gallon of ethanol
    Energy_content_natgas = 1.036 #mmBTU/thousand cubic feet of natural gas. 
    Energy_content_methane = 50 #MJ/kg of methane
    Energy_content_methane = Energy_content_methane * 947.81 #MJ/kg to BTU/kg
    RIN_price_kg = (RIN_price/Energy_content_ethanol)*Energy_content_methane #USD/kg of methane
    Natural_gas_kg = (Natural_gas_price/Energy_content_natgas)*(Energy_content_methane/10**6) #USD/kg of methane - assuming natural gas as mostly methane
    RNG_price = RIN_price_kg + Natural_gas_kg #USD/kg of methane

    return {
        'water': water_price,
        'manure': manure_price,
        'RNG': RNG_price,
        'Natural_gas': Natural_gas_kg,
        'solid_digestate': solid_digestate_price,
        'liquid_digestate': liquid_digestate_price
    }

def stream_densities(feedstock):
    # Densities in BioSTEAM depends on the components of the stream.
    # I need to calculate the value for Volatile solids and Ash content to get the overall density.

    water_density = 998.7 #kg/m3 at 17°C (half of manure and grass inlet temperatures)
    Manure_density = 1001.858 #kg/m3
    A1, B1, C1, D1 = Manure_density, (0.878/water_density), 0.1030, 0.0190 # Constants are the composition of manure (Water, VS, and Ash)
    if feedstock == 'SWG': #Switchgrass
        grass_density = 1195 # Grass particle density (kg/m3)
        A2, B2, C2, D2 = grass_density, (0.15/water_density), 0.7752, 0.0748 # Constants are the composition of switchgrass (Water, VS, and Ash)
    if feedstock == 'CORN': #Corn stover
        grass_density = 861.7 # Grass particle density (kg/m3)
        A2, B2, C2, D2 = grass_density, (0.0524/water_density), 0.8802, 0.0674 # Constants are the composition of switchgrass (Water, VS, and Ash)
    if feedstock == 'WR': #Winter rye
        grass_density = 1195 # Grass particle density (kg/m3)
        A2, B2, C2, D2 = grass_density, (0.0409/water_density), 0.8846, 0.0745 # Constants are the composition of switchgrass (Water, VS, and Ash)

    def equations(vars):
        y, z = vars
        eq1 = A1-1 / (B1 + (C1/y) + (D1/z))
        eq2 = A2-1 / (B2 + (C2/y) + (D2/z))
        return [eq1, eq2]
    
    #Initial guess
    y0, z0 = 1, 1
    y_sol, z_sol = fsolve(equations, (y0, z0))

    VS_density = y_sol #kg/m3
    Ash_density = z_sol #kg/m3

    return {
        'VS': VS_density,
        'Ash': Ash_density,
    }


