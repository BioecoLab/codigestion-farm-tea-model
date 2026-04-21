'Process settings'

import biosteam as bst


def Cp_manure(manure_T, manure_water_frac):
    
    #Specific heat of manure in kJ/kg°C
    Cp_manure_value = (0.68298+(0.025662*manure_T)+(0.01206*manure_water_frac*100))
    return {'Cp_manure': Cp_manure_value}

def Cp_grass(feedstock):

    #Specific heat of grass in kJ/kg°C

    if feedstock == "SWG":
        Cp_grass_value = 1.438 # kJ/kg °C
    elif feedstock == "CORN":
        Cp_grass_value = 1.668 # kJ/kg °C
    elif feedstock == "WR":
        Cp_grass_value = 1.455 # kJ/kg °C
    
    
    return {'Cp_grass': Cp_grass_value}

def Cp_water(): return 4.184 # kJ/kg°C

def Cp_mixture(water_flowrate, slurry_flowrate, manure_flowrate, grass_flowrate, Cp_manure_value, Cp_grass_value):

    Cp_mixture_value = (Cp_water()*(water_flowrate/slurry_flowrate))+(Cp_manure_value*(manure_flowrate/slurry_flowrate))+(Cp_grass_value*(grass_flowrate/slurry_flowrate)) # kJ/kg °C
    return {
        'Cp_mixture': Cp_mixture_value
    }

# Thermal conductivities (W/m°C)
def k_manure(manure_T, manure_water_frac):
    
    k_manure_value = -0.239615+(0.00356*manure_T)+(0.00813*manure_water_frac*100) #W/m °C
    return {
        'k_manure': k_manure_value
    }

def k_grass(feedstock): 
    
    if feedstock == "SWG":
        k_grass_value = 0.621
    elif feedstock == "CORN":
        k_grass_value = 0.20
    elif feedstock == "WR":
        k_grass_value = 0.621

    return {
        'k_grass': k_grass_value
    }

def k_water(): return 0.606

def k_mixture(water_flowrate, slurry, manure_flowrate, grass_flowrate, k_manure_value, k_grass_value):

    k_mixture_value = (k_water()*(water_flowrate/slurry))+(k_manure_value*(manure_flowrate/slurry))+(k_grass_value*(grass_flowrate/slurry)) #W/m °C

    
    return {
        'k_mixture': k_mixture_value
    }


def external_temperature(external_temperature_value): 

    external_temperature_value = external_temperature_value + 273.15 #Conversion to K
    
    return {
        'external_temperature': external_temperature_value
    }
