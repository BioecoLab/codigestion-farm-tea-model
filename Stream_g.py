'Stream'

import biosteam as bst




def manure_properties(cows, manure_T, price, lactating_cows, moisture_lactating,
                      moisture_dry, VS_lactating, VS_dry, Carbon_lactating, Carbon_dry,
                      Nitrogen_lactating, Nitrogen_dry):


    #Lactating cows
    lactating_cows_number = cows*lactating_cows # Number of lactating cows
    lactating_cow_manure = 68 # Avg amount in kg/day animal according to ASAE (2005)
    lactating_manure_flowrate = lactating_cows_number*lactating_cow_manure # Avg amount in kg/day
    lactating_manure_water = moisture_lactating # Manure water content % according to ASAE (2005)
    lactating_manure_solids = 1-lactating_manure_water #Manure total solids %
    lactating_manure_vsolids = VS_lactating # Manure volatile solids % w.b. ASAE (2005).
    lactating_manure_ash = lactating_manure_solids-VS_lactating # Manure ash content % w.b.
    lactating_manure_nitrogen = Nitrogen_lactating # Manure nitrogen content % w.b..
    lactating_manure_carbon = Carbon_lactating # Manure carbon content % w.b.
    lactating_manure_water_flow = (lactating_cows_number*lactating_cow_manure*lactating_manure_water)/24 # Avg amount in kg/hr total dry herd
    lactating_manure_vsolids_flow = (lactating_cows_number*lactating_cow_manure*lactating_manure_vsolids)/24 # Avg amount in kg/hr total dry herd
    lactating_manure_ash_flow = (lactating_cows_number*lactating_cow_manure*lactating_manure_ash)/24 # Avg amount in kg/hr total dry herd

    #Dry cows
    dry_cows_number = cows*(1-lactating_cows) # Number of dry cows
    dry_cow_manure = 38 # Avg amount in kg/day animal according to ASAE (2005)
    dry_manure_flowrate = dry_cows_number*dry_cow_manure # Avg amount in kg/day
    dry_manure_water = moisture_dry # Manure water content % according to ASAE (2005)
    dry_manure_solids = 1-dry_manure_water #Manure total solids %
    dry_manure_vsolids = VS_dry # Manure volatile solids % w.b.  ASAE (2005). Aprox 85%
    dry_manure_ash = dry_manure_solids-VS_dry # % w.b.
    dry_manure_nitrogen = Nitrogen_dry # Manure nitrogen content % w.b.
    dry_manure_carbon = Carbon_dry # Manure carbon content % w.b.
    dry_manure_water_flow = (dry_cows_number*dry_cow_manure*dry_manure_water)/24 # Avg amount in kg/hr total dry herd
    dry_manure_vsolids_flow = (dry_cows_number*dry_cow_manure*dry_manure_vsolids)/24 # Avg amount in kg/hr total dry herd
    dry_manure_ash_flow = (dry_cows_number*dry_cow_manure*dry_manure_ash)/24 # Avg amount in kg/hr total dry herd

    # Total manure Characteristics. ADDING water coming from parlor and barn
    parlor_system = True 
    if parlor_system == True: #If parlor_system = True parlor system is hose system (conservative scenario)
        if cows <= 200:
            parlor_water = (437.5 + (1.25 * cows))/264.17 #m3/day
        elif cows <= 700:
            parlor_water = (457.5 + (0.9375 * cows))/264.17 #m3/day
        else:
            parlor_water = (477.5 + (0.625 * cows))/264.17 #m3/day
    else:
        if cows <= 200:
            parlor_water = (387.5 + (45 * cows))/264.17 #m3/day
        elif cows <= 700:
            parlor_water = (432.5 + (37.5 * cows))/264.17 #m3/day
        else:
            parlor_water = (477.5 + (30 * cows))/264.17 #m3/day
    barn_water = 100 * cows / 264.17 #m3/day


    manure_per_day = lactating_cows_number*lactating_cow_manure + dry_cows_number*dry_cow_manure +(parlor_water*1000) # lactating and dry cow manure and parlor water in kg/day
    manure_density = 1001.858 # Assuming same as water (kg/m3)
    manure_flowrate = manure_per_day/24 # Manure flow rate in kg/hr
    flow_manure_vsolids = lactating_manure_vsolids_flow + dry_manure_vsolids_flow # Total manure volatile solids flow in kg/hr
    flow_manure_water = lactating_manure_water_flow + dry_manure_water_flow + (parlor_water*1000/24) # Total manure water flow in kg/hr
    flow_manure_ash = lactating_manure_ash_flow + dry_manure_ash_flow # Total manure ash flow in kg/hr
    manure_water = flow_manure_water/manure_flowrate # Manure water content %
    manure_solids = 1-manure_water # Manure total solids %
    manure_vsolids = flow_manure_vsolids/manure_flowrate # Manure volatile solids %
    manure_ash = flow_manure_ash/manure_flowrate # Manure ash content %
    manure_carbon_content = ((lactating_manure_flowrate/24)*lactating_manure_carbon) + ((dry_manure_flowrate/24)*dry_manure_carbon) # Carbon content in kg/hr
    manure_nitrogen_content = ((lactating_manure_flowrate/24)*lactating_manure_nitrogen) + ((dry_manure_flowrate/24)*dry_manure_nitrogen) # Nitrogen content in kg/hr


    manure = bst.Stream(
                'Manure',
                total_flow= manure_flowrate,
                VolatileSolids=flow_manure_vsolids,
                Water=flow_manure_water,
                Ash=flow_manure_ash,
                units='kg/hr',
                phase='l',
                T=manure_T + 273.15,
                price=price,
            )

    return {
        'stream': manure,
        'manure_per_day': manure_per_day,
        'density': manure_density,
        'flowrate': manure_flowrate,
        'manure_vsolids': manure_vsolids,
        'manure_solids': manure_solids,
        'manure_carbon': manure_carbon_content,
        'manure_nitrogen': manure_nitrogen_content,
        'water_frac': manure_water,
    }


def grass_properties(cows, feedstock, feedstock_flow, CN_ratio, grass_price, 
                     grass_T, manure_carbon_content, manure_nitrogen_content,
                     grass_moisture, grass_VS, grass_Carbon_percentage, grass_Nitrogen_percentage,
                     grass_Biomass):

    'Feedstock characteristics depend on the type of feedstock and the flow basis'

    if feedstock == 'SWG': #Switchgrass
        if feedstock_flow == 'CN': #C/N ratio basis
            grass_nitrogen = grass_Nitrogen_percentage # Grass nitrogen content %
            grass_carbon = grass_Carbon_percentage # Grass carbon content %
            grass_water = grass_moisture # Grass water content %
            #grass_per_hour = (manure_carbon_content - (CN_ratio * manure_nitrogen_content))/((CN_ratio * grass_nitrogen) - grass_carbon) #kg/hr to have a desired C/N ratio
            grass_per_hour = 1175.71 # kg/hr to have a C/N ratio of 30:1
            grass_per_day = grass_per_hour*24 # in kg/day
            flow_per_year = grass_per_day*365 # Annual amount of switchgrass harvested in kg
            
            #Doing inverse equations of LAND scenario to estimate land needed

            grass_per_year = (1-grass_water) * flow_per_year # in kg/year dry matter
            biomass_loss_field = 0.30 # % of biomass that is lost in the field after harvest. Not collected
            biomass_loss_storage = 0.06 # % of biomass that is lost in storage.
            annual_yield = grass_per_year / ((1-biomass_loss_field)*(1-biomass_loss_storage) * 1000) # Adding losses in harvesting and storage in d.m. Mg/year
            yield_per_ha = grass_Biomass # dry matter Mg/ha/year
            area_grass = annual_yield / yield_per_ha # Hectares of land for switchgrass growth in hectare per year

            grass_price = grass_price/(1-grass_water) # Adjusting price from dry matter basis to $/kg switchgrass w.b.


        elif feedstock_flow == 'LAND': #Land area basis
            area_farm = 1.5/2.471 # Hectares of dairy farm per cow
            f_land_swg = 0.5 # Fraction of land used for switchgrass growth
            area_grass = area_farm * cows * f_land_swg # Hectares of land for switchgrass growth hectare
            yield_per_ha = grass_Biomass # dry matter Mg/ha/year
            annual_yield = area_grass * yield_per_ha # Annual amount of switchgrass harvested in metric ton/year
            biomass_loss_field = 0.30 # % of biomass that is lost in the field after harvest. Not collected
            biomass_loss_storage = 0.06 # % of biomass that is lost in storage.
            grass_water = grass_moisture # Grass water content %
            flow_per_year = annual_yield * (1-biomass_loss_field) * (1-biomass_loss_storage) * 1000 # Annual amount of switchgrass harvested in dry matter kg
            flow_per_year = (flow_per_year)/(1-grass_water) # Adjusting for moisture content (Total mass in kg/year)
            grass_per_day = flow_per_year/365 # Avg switchgrass available per day in kg/day
            grass_per_hour = grass_per_day/24 # Avg switchgrass available per hour in kg/hr
            
            grass_price = grass_price/(1-grass_water) # Adjusting price from dry matter basis to $/kg switchgrass w.b.   

        grass_water = grass_moisture # Grass water content % w.b.
        grass_vsolids = (1-grass_water)*grass_VS # Grass volatile solids % w.b.
        grass_ash = (1-grass_water-grass_vsolids) # Grass ash content  % w.b.
        grass_nitrogen = grass_Nitrogen_percentage # Grass nitrogen content % w.b.
        grass_carbon = grass_Carbon_percentage # Grass carbon content % w.b.
        grass_density = 1195 # Grass particle density (kg/m3)
        bale_density = 175 # Switchgrass bale density (kg/m3)

        #Amount of bales per year
        bale_volume = flow_per_year/bale_density # m3 per year
        bale_size = 3*4*8 # ft3
        bale_volume_ft3 = bale_volume/0.02832 # ft3
        annual_bales = bale_volume_ft3/bale_size # bales per year


        #grass_inlet_temperature=20 #grass inlet temperature °C

        flow_grass_vsolids = grass_per_hour * grass_vsolids #Calculating the flow of volatile solids in grass in kg/hr
        flow_grass_water = grass_per_hour * grass_water #Calculating the flow of water in grass in kg/hr
        flow_grass_ash = grass_per_hour * grass_ash #Calculating the flow of ash in grass in kg/hr

        grass_carbon_content = (grass_per_hour*grass_carbon) # Carbon content in kg/hr
        grass_nitrogen_content = (grass_per_hour*grass_nitrogen) # Nitrogen content in kg/hr   

            
        

    
    if feedstock == 'CORN': #Corn stover
        if feedstock_flow == 'CN': #C/N ratio basis
            grass_nitrogen = grass_Nitrogen_percentage # Grass nitrogen content % in dry basis
            grass_carbon = grass_Carbon_percentage # Grass carbon content % in dry basis
            grass_water = grass_moisture # Grass water content %
            #grass_per_hour = (manure_carbon_content - (CN_ratio * manure_nitrogen_content))/((CN_ratio * grass_nitrogen) - grass_carbon) #kg/hr to have a desired C/N ratio
            grass_per_hour = 1175.71 # kg/hr fixed input
            grass_per_day = grass_per_hour*24 # in kg/day
            flow_per_year = grass_per_day*365 # Annual amount of corn stover harvested in kg

            #Doing inverse equations of LAND scenario to estimate land needed

            grass_per_year = (1-grass_water) * flow_per_year # in kg/year dry matter
            biomass_loss_field = 0.30 # % of biomass that is lost in the field after harvest. Not collected
            biomass_loss_storage = 0.06 # % of biomass that is lost in storage.
            biomass_to_collect = grass_per_year / ((1-biomass_loss_field)*(1-biomass_loss_storage) * 1000) # Adding losses in harvesting and storage in d.m. Mg/year
            conservation_allowance = 0.715*2.471 # dry matter Mg/ha portion of corn stover that can be removed from the field without harming the soil
            #annual_yield = biomass_to_collect + (conservation_allowance * area_grass) # Annual amount of corn harvested in metric ton/year
            yield_per_ha = grass_Biomass # dry matter Mg/ha/year
            residue_to_grain_ratio = 1.0 # Corn residue to grain ratio
            area_grass = biomass_to_collect / ((yield_per_ha * residue_to_grain_ratio) - conservation_allowance) # Hectares of land for corn growth in hectare per year

            grass_price = grass_price/(1-grass_water) # Adjusting price from dry matter basis to $/kg corn stover w.b.   


        elif feedstock_flow == 'LAND': #Land area basis
            area_farm = 1.5/2.471 # Hectares of dairy farm per cow
            f_land_corn = 0.5 # Fraction of land used for corn grain growth
            area_grass = area_farm * cows * f_land_corn # Hectares of land for corn growth hectare
            yield_per_ha = grass_Biomass # dry matter Mg/ha/year
            residue_to_grain_ratio = 1.0 # Corn residue to grain ratio
            annual_yield = area_grass * yield_per_ha * residue_to_grain_ratio # Annual amount of corn harvested in dry matter metric ton/year
            conservation_allowance = 0.715*2.471 # dry matter Mg/ha portion of corn stover that can be removed from the field without harming the soil
            biomass_to_collect = annual_yield - (conservation_allowance * area_grass) # Amount of biomass that can be collected without harming the soil in metric ton
            biomass_loss_harvest = 0.30 # % of biomass that is lost in the field after harvest. Not collected. Dry matter     
            biomass_loss_storage = 0.06 # % of biomass that is lost in storage. Dry matter
            grass_water = grass_moisture # Grass water content %
            flow_per_year = (biomass_to_collect * 1000) * (1-biomass_loss_harvest) * (1 - biomass_loss_storage) # Annual amount of dry matter corn stover harvested in dry matter kg/year
            flow_per_year = (flow_per_year)/(1-grass_water) # Adjusting for moisture content (Total mass in kg/year)
            grass_per_day = flow_per_year/365 # Adjusting for moisture content (Total mass in kg/year)
            grass_per_hour = grass_per_day/24 # Avg corn stover available per hour in kg/h

            grass_price = grass_price/(1-grass_water) # Adjusting price from dry matter basis to $/kg corn stover w.b.   

        grass_water = grass_moisture # Grass water content % w.b.
        grass_vsolids = grass_VS # Grass volatile solids % w.b.
        grass_ash = (1-grass_water-grass_vsolids) # Grass ash content % w.b.
        grass_nitrogen = grass_Nitrogen_percentage # Grass nitrogen content % w.b.
        grass_carbon = grass_Carbon_percentage # Grass carbon content % w.b.
        grass_density = 861.7 # Grass particle density (kg/m3)
        bale_density = 164 # Switchgrass bale density (kg/m3)

        #Amount of bales per year
        bale_volume = flow_per_year/bale_density # m3 per year
        bale_size = 3*4*8 # ft3
        bale_volume_ft3 = bale_volume/0.02832 # ft3
        annual_bales = bale_volume_ft3/bale_size # bales per year
        #grass_inlet_temperature=20 #grass inlet temperature °C

        flow_grass_vsolids = grass_per_hour * grass_vsolids #Calculating the flow of volatile solids in grass in kg/hr
        flow_grass_water = grass_per_hour * grass_water #Calculating the flow of water in grass in kg/hr
        flow_grass_ash = grass_per_hour * grass_ash #Calculating the flow of ash in grass in kg/hr

        grass_carbon_content = (grass_per_hour*grass_carbon) # Carbon content in kg/hr
        grass_nitrogen_content = (grass_per_hour*grass_nitrogen) # Nitrogen content in kg/hr



    if feedstock == 'WR': #Winter rye
        if feedstock_flow == 'CN': #C/N ratio basis
            grass_water = grass_moisture # Grass water content %
            grass_nitrogen = grass_Nitrogen_percentage # Grass nitrogen content %
            grass_carbon = grass_Carbon_percentage # Grass carbon content % 
            #grass_per_hour = (manure_carbon_content - (CN_ratio * manure_nitrogen_content))/((CN_ratio * grass_nitrogen) - grass_carbon) #kg/hr to have a desired C/N ratio
            grass_per_hour = 1175.71 # kg/hr fixed input
            grass_per_day = grass_per_hour*24 # in kg/day
            flow_per_year = grass_per_day*365 # Annual amount of winter rye harvested in kg
            
            #Doing inverse equations of LAND scenario to estimate land needed

            grass_per_year = (1-grass_water) * flow_per_year # in kg/year dry matter
            biomass_loss_field = 0.30 # % of biomass that is lost in the field after harvest. Not collected
            biomass_loss_storage = 0.06 # % of biomass that is lost in storage.
            annual_yield = grass_per_year / ((1-biomass_loss_field)*(1-biomass_loss_storage) * 1000) # Adding losses in harvesting and storage in d.m. Mg/year
            yield_per_ha = grass_Biomass # dry matter Mg/ha/year
            area_grass = annual_yield / yield_per_ha # Hectares of land for winter rye growth in hectare per year

            grass_price = grass_price/(1-grass_water) # Adjusting price from dry matter basis to $/kg winter rye w.b.
            


        elif feedstock_flow == 'LAND': #Land area basis
            area_farm = 1.5/2.471 # Hectares of dairy farm per cow
            f_land_wr = 0.7 # Fraction of land used for winter rye growth
            area_grass = area_farm * cows * f_land_wr # Hectares of land for winter rye growth hectare
            yield_per_ha = grass_Biomass # dry matter Mg/ha/year
            annual_yield = area_grass * yield_per_ha # Annual amount of winter rye harvested in metric ton/year
            biomass_loss_harvest = 0.30 # % of biomass that is lost in the field after harvest. Not collected
            biomass_loss_storage = 0.06 # % of biomass that is lost in storage. Dry matter
            grass_water = grass_moisture # Grass water content 
            flow_per_year = annual_yield * (1-biomass_loss_harvest) * (1 - biomass_loss_storage) * 1000 # Annual amount of dry matter winter rye harvested in kg
            flow_per_year = (flow_per_year)/(1-grass_water) # Adjusting for moisture content (Total mass in kg/year)
            grass_per_day = flow_per_year/365 # Avg winter rye available per day in kg/day
            grass_per_hour = grass_per_day/24 # Avg winter rye available per hour in kg/hr
            
            grass_price = grass_price/(1-grass_water) # Adjusting price from dry matter basis to $/kg winter rye w.b.

        grass_water = grass_moisture # Grass water content % w.b.
        grass_vsolids = grass_VS # Grass volatile solids % w.b.
        grass_ash = (1-grass_water-grass_vsolids) # Grass ash content % w.b.
        grass_nitrogen = grass_Nitrogen_percentage # Grass nitrogen content % w.b.
        grass_carbon = grass_Carbon_percentage # Grass carbon content % w.b.
        grass_density = 1195 # Grass particle density (kg/m3)
        bale_density = 169.5 # Switchgrass bale density (kg/m3)

        #Amount of bales per year
        bale_volume = flow_per_year/bale_density # m3 per year
        bale_size = 3*4*8 # ft3
        bale_volume_ft3 = bale_volume/0.02832 # ft3
        annual_bales = bale_volume_ft3/bale_size # bales per year

        flow_grass_vsolids = grass_per_hour * grass_vsolids #Calculating the flow of volatile solids in grass in kg/hr
        flow_grass_water = grass_per_hour * grass_water #Calculating the flow of water in grass in kg/hr
        flow_grass_ash = grass_per_hour * grass_ash #Calculating the flow of ash in grass in kg/hr

        grass_carbon_content = (grass_per_hour*grass_carbon) # Carbon content in kg/hr
        grass_nitrogen_content = (grass_per_hour*grass_nitrogen) # Nitrogen content in kg/hr

    

    grass = bst.Stream(
                'Grass',
                total_flow=grass_per_hour, 
                VolatileSolids=flow_grass_vsolids, 
                Water=flow_grass_water,
                Ash=flow_grass_ash,
                units='kg/hr',    
                phase='s',
                T = grass_T + 273.15,
                price=grass_price,
            )

    
    return {
        'stream': grass,
        'grass_per_day': grass_per_day,
        'density': grass_density,
        'flowrate': grass_per_hour,
        'grass_vsolids': grass_vsolids,
        'grass_carbon': grass_carbon_content,
        'grass_nitrogen': grass_nitrogen_content,
        'water_frac': grass_water,
        'bales_per_year': annual_bales,
        'area_grass': area_grass,
        'flow_per_year': flow_per_year,
    }



def water_slurry_properties(manure_per_day,grass_per_day, manure_solids, grass_water, water_T, price, TS_digester):
    
    dry_matter=(manure_per_day*manure_solids)+(grass_per_day*(1-grass_water)) #Dry matter weight in kg/day of manure and switchgrass. Total solids
    total_weight_slurry=dry_matter/TS_digester #This is the total weight of the slurry (manure+grass) after adding the water to obtain a moisture content of 90%. In kg/day
    water_flowrate=((total_weight_slurry-manure_per_day-grass_per_day)/24) #Water added to achieve 90% moisture content. In kg/hr
    slurry_flowrate = total_weight_slurry/24 # Slurry (manure+grass) flow rate in kg/hr

    water = bst.Stream(
                    'Water',
                    total_flow=water_flowrate, 
                    VolatileSolids=0, 
                    Water=water_flowrate,
                    Ash=0,
                    units='kg/hr',    
                    phase='l',
                    T = water_T + 273.15,
                    price=price,
                )


    return {
        'stream': water,
        'water_flowrate': water_flowrate,
        'slurry_flowrate': slurry_flowrate,
    }







