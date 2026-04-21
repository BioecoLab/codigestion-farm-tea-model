
'System RNG'

from Inputs_g import inputs

'Inputs.py file'
data = inputs()

#manure_storage = False #True if a manure pit needs to be constructed in the farm
#grass_storage = False #True if a grass storage unit (slab for bales) needs to be constructed in the farm
#digestate_storage = False #True if a digestate storage unit needs to be constructed in the farm
#heat_mixtank = False #True if mixing tank before the digester will be heating the slurry. If not it will be only a mixing tank


def create_system(data, manure_storage = True, grass_storage = True, digestate_storage = False, heat_mixtank = False, parlor_system = True, upgrading = True):

    from Inputs_g import get_stream_prices, stream_densities
    from Chemicals_g import create_chemicals
    from Stream_g import manure_properties, grass_properties, water_slurry_properties
    from Process_settings_g import Cp_manure, Cp_grass, k_manure, k_grass, Cp_mixture, k_mixture, external_temperature, Cp_water
    from Reactions_g import ideal_gas_volume_mL, biogas_methane_conversions
    from Units_g import ManureStorageTank, GrassStorageTank, Shredder, MixingTank, ContinousFermentation, H2SRemovalUnit, Biogas_cooling, SolidsSeparator, DigestateStorageTank, Membrane_Separation, BoilerUnit, CHPUnit, IsentropicCompressor
    
    import biosteam as bst
    from biosteam import units
    from biosteam import Splitter

    prices = get_stream_prices(water_price=data['water_price'],
                            manure_price=data['manure_price'],
                            RIN_price=data['RIN_price'],
                            solid_digestate_price=data['solid_digestate_price'],
                            liquid_digestate_price=data['liquid_digestate_price'],
                            Natural_gas_price=data['Natural_gas_price'],)


    RNG_price_value = prices['RNG']
    Nat_gas = prices['Natural_gas']

    densities = stream_densities(feedstock = data['feedstock'])

    'Chemicals.py file'
    
    chemicals = create_chemicals(VS_density=densities['VS'],
                                 Ash_density=densities['Ash'])
    bst.settings.set_thermo(chemicals)


    'Stream.py file'
    manure_data = manure_properties(cows = data['cows'],
                                    manure_T= data['manure_inlet_temperature'],
                                    price = prices['manure'],
                                    lactating_cows= data['Lactating_cows'],
                                    moisture_lactating= data['Manure_moisture_lactating'],
                                    moisture_dry= data['Manure_moisture_dry'],
                                    VS_lactating= data['Manure_VS_lactating'],
                                    VS_dry= data['Manure_VS_dry'],
                                    Carbon_lactating= data['Manure_Carbon_lactating'],
                                    Carbon_dry= data['Manure_Carbon_dry'],
                                    Nitrogen_lactating= data['Manure_Nitrogen_lactating'],
                                    Nitrogen_dry= data['Manure_Nitrogen_dry'],
                                    )


    grass_data = grass_properties(cows = data['cows'],
                                feedstock = data['feedstock'],
                                feedstock_flow = data['feedstock_flow'],
                                CN_ratio = data['CN'],
                                grass_price = data['grass_price'],
                                grass_T = data['grass_inlet_temperature'],
                                manure_carbon_content=manure_data['manure_carbon'],
                                manure_nitrogen_content=manure_data['manure_nitrogen'],
                                grass_moisture = data['Moisture_grass'],
                                grass_VS = data['VS_grass'],
                                grass_Carbon_percentage = data['Carbon_grass'],
                                grass_Nitrogen_percentage = data['Nitrogen_grass'],
                                grass_Biomass = data['Biomass_yield_grass'],
                                )

    water_data = water_slurry_properties(manure_per_day = manure_data['manure_per_day'],
                                        grass_per_day = grass_data['grass_per_day'],
                                        manure_solids= manure_data['manure_solids'],
                                        grass_water = grass_data['water_frac'],
                                        water_T = data['water_inlet_temperature'],
                                        price = prices['water'],
                                        TS_digester = data['Total_solids_digester']
                                        )

    Carbon_Nitrogen_ratio = (manure_data['manure_carbon']+ grass_data['grass_carbon'])/(manure_data['manure_nitrogen']+grass_data['grass_nitrogen'])

    'Process_settings.py file'

    Cp_manure_data = Cp_manure(manure_T = data['manure_inlet_temperature'],
                                manure_water_frac = manure_data['water_frac'])

    Cp_grass_data = Cp_grass(feedstock = data['feedstock'])

    Cp_water_data = Cp_water()

    Cp_mixture_data = Cp_mixture(water_flowrate= water_data['water_flowrate'],
                                slurry_flowrate= water_data['slurry_flowrate'],
                                manure_flowrate = manure_data['flowrate'],
                                grass_flowrate = grass_data['flowrate'],
                                Cp_manure_value = Cp_manure_data['Cp_manure'],
                                Cp_grass_value = Cp_grass_data['Cp_grass'],)

    k_manure_data = k_manure(manure_T = data['manure_inlet_temperature'],
                            manure_water_frac = manure_data['water_frac'])
    
    k_grass_data = k_grass(feedstock = data['feedstock'])

    k_mixture_data = k_mixture(water_flowrate= water_data['water_flowrate'],
                            slurry = water_data['slurry_flowrate'],
                            manure_flowrate = manure_data['flowrate'],
                            grass_flowrate = grass_data['flowrate'],
                            k_manure_value = k_manure_data['k_manure'],
                            k_grass_value = k_grass_data['k_grass'],)

    external_temperature_data = external_temperature(external_temperature_value = data['external_temperature'])

    'Reactions.py file'

    Ideal_gas_data = ideal_gas_volume_mL(T_K = data['Temperature_digester'] + 273.15)  # K
    Methane_data = biogas_methane_conversions(manure_flowrate = manure_data['flowrate'],
                                            grass_flowrate = grass_data['flowrate'],
                                            manure_vsolids= manure_data['manure_vsolids'],
                                            grass_vsolids= grass_data['grass_vsolids'],
                                            CH4_yield_manure = data['CH4_yield_manure'],
                                            CH4_yield_grass = data['CH4_yield_grass'],
                                            Gas_volume = Ideal_gas_data['Gas_volume']) # mL CH4/g VS


    'Settings'
    steam_utility = bst.settings.get_agent('low_pressure_steam') #Using low pressure steam because our heating needs are not that high.
    bst.settings.heating_agents = [steam_utility]
    steam_utility.heat_transfer_efficiency = 1.0   ##This is heat transfer efficiency. The boiler already takes this into account, so it can be ignored.
    steam_utility.heat_transfer_price = 0 

    cooling_utility = bst.settings.get_agent('chilled_brine')   #Chilled brine was used for the gas cooling stage in order to get the gas cool enough to remove all the moisture.
    bst.settings.cooling_agents = [cooling_utility]
    cooling_utility.heat_transfer_efficiency = 0.8

    bst.settings.electricity_price = data['electricity_price'] #Electricity price in $/kWh
    bst.stream_utility_prices['Natural gas'] = prices['Natural_gas'] #Natural gas price in $/kg

    'Mixing tank streams' #This is to help BioSTEAM recognize the streams and for it to calculate the amount of water needed
    Manure = bst.Stream('Manure', units='kg/hr')
    Grass = bst.Stream('Switchgrass', units='kg/hr')
    Water = bst.Stream('Water', units='kg/hr')

    'Recycle stream'
    Recirculated_slurry = bst.Stream('Recirculated_slurry', units='kg/hr', phase='l')
    Recirculated_slurry.imass['H2O'] = 5000 # kg/hr initial guess for the first run
    
    'Product streams'
    RNG = bst.Stream('RNG', units='kg/hr', phase='g', price=prices['RNG'])
    solid_digestate = bst.Stream('Solid_Digestate', units='kg/hr', phase='s', price=prices['solid_digestate'])
    liquid_digestate = bst.Stream('Liquid_Digestate', units='kg/hr', phase='l', price=prices['liquid_digestate'])
   
    'Unit operations'

    Manure_Pit = ManureStorageTank(manure_storage=manure_storage,
                                parlor_system=parlor_system,
                                manure_solids_value=manure_data['manure_solids'],
                                manure_per_day=manure_data['manure_per_day'],
                                manure_density =manure_data['density'],
                                ID='Manure_Pit', ins=[manure_data['stream']], outs='Manure')

    # Set number of cows
    Manure_Pit.number_of_cows = data['cows']

    Manure_Pump = units.Pump('Manure_Pump', ins=Manure_Pit-0, outs=Manure)

    Grass_Storage = GrassStorageTank(grass_storage=grass_storage,
                                     grass_flow=data['feedstock_flow'],
                                     annual_bales=grass_data['bales_per_year'],
                                     ID='Grass_Storage', ins=grass_data['stream'], outs='grass')

    Grass_Shredder = Shredder('Grass_Shredder', Grass_Storage-0, outs=Grass)

    Mixing_Tank = MixingTank(heat_mixtank = heat_mixtank,
                                Cp_manure_value = Cp_manure_data['Cp_manure'],
                                Cp_grass_value = Cp_grass_data['Cp_grass'],
                                Cp_water = Cp_water_data,
                                Cp_mixture_value = Cp_mixture_data['Cp_mixture'],
                                temperature_digester = data['Temperature_digester'],
                                external_temperature_value = data['external_temperature'],
                                water_temperature = data['water_inlet_temperature'],
                                TS_digester = data['Total_solids_digester'],
                                ID='Heated_Tank', ins=[Manure, Grass, Water, Recirculated_slurry], outs='Slurry', T=data['Temperature_digester']+273.15)

    Digester = ContinousFermentation(upgrading = upgrading,
                                     hrt_hr = data['HRT']*24,
                                     Cp_mixture_value = Cp_mixture_data['Cp_mixture'],
                                     k_mixture_value = k_mixture_data['k_mixture'],
                                     external_temperature_value = data['external_temperature'],
                                     temperature_digester = data['Temperature_digester'],
                                     CH4_mass_yield = Methane_data['CH4_mass_yield'],
                                     CO2_mass_yield = Methane_data['CO2_mass_yield'],
                                     ID ='Digester', ins= Mixing_Tank-0, outs=('Biogas', 'Digestate'), T=data['Temperature_digester']+273.15, tau = data['HRT']*24)

    Moisture_Removal = Biogas_cooling('Moisture_Removal', ins = Digester-0, outs=('Dry_Biogas'), T=data['external_temperature']+273.15, rigorous=True, cool_only=True)
    
    Water_trap = units.Splitter('Water_trap', ins=Moisture_Removal-0, outs=('Water','Dry_Gas'), split={'Water': 1.0, 'CH4': 0, 'CO2': 0})

    H2S_Removal = H2SRemovalUnit('H2S_Removal', ins=Water_trap-1, outs=('Biogas'))

    Gas_Upgrading = Membrane_Separation(ID='Gas_Upgrading', ins=H2S_Removal-0, outs = ('RNG', 'CO2'), cap_factor=data['Cap_factor']) 

    RNG_Compressor = IsentropicCompressor(ID='RNG_Compressor', ins=Gas_Upgrading-0, outs=RNG, P=1.379e6, vle=False, eta=0.80)

    Dewater = SolidsSeparator('Solids_Separator', ins = (Digester-1), outs=(solid_digestate, 'Liquid_stream'), split=dict(Ash=0.997, VolatileSolids=0.997), moisture_content=0.60)

    Recycle_loop = Splitter('Recirculation', ins=(Dewater-1), outs=('Recycle_digestate', 'Liquid_digestate'), split=0.5)

    Digestate_Pump = units.Pump('Liq_Digestate_pump', ins=(Recycle_loop-0), outs=Recirculated_slurry)

    Digestate_storage = DigestateStorageTank('Digestate_storage', ins=Recycle_loop-1, outs=liquid_digestate, digestate_storage=digestate_storage)
    Digestate_storage.number_of_cows = data['cows']                 

    Boiler = BoilerUnit(ID = 'Boiler', ins = ('Natural_gas','Water'), 
                        boiler_efficiency=0.8, 
                        natural_gas_price=prices['Natural_gas'], 
                        water_price = prices['water'], 
                        satisfy_system_electricity_demand=False, 
                        water_temperature=data['water_inlet_temperature'],
                        Cp_H2O=Cp_water(),
                        Digester_unit=Digester)

    system_sys = bst.System('RNG_plat', path = (Manure_Pit, Manure_Pump, Grass_Storage, Grass_Shredder, Mixing_Tank, Digester, Moisture_Removal, Water_trap, H2S_Removal, Gas_Upgrading, RNG_Compressor, Dewater, Recycle_loop, Digestate_Pump, Mixing_Tank, Digestate_storage, Boiler))

    return system_sys, prices, manure_data, grass_data, water_data, Carbon_Nitrogen_ratio, Digester, RNG_price_value, Nat_gas

def run_model(data):
    system_sys, prices, manure_data, grass_data, water_data, Carbon_Nitrogen_ratio, Digester, RNG_price_value, Nat_gas = create_system(data)
    system_sys.simulate()

    biogas_flow = Digester.outs[0].F_mass
   
    from TEA_g import AD_TEA

    tea = AD_TEA(system                 =   system_sys,
                IRR                     =   0.08,                       # Internal rate of return
                duration                =   (2025, 2045),               # Start and end year
                depreciation            =   'MACRS7',                   # Number of years
                income_tax              =   0.3955,                     # PA income tax
                operating_days          =   365*data['Cap_factor'],  # Operating days per year
                construction_schedule   =   (0.4, 0.6), 
                WC_over_FCI             =   0.05,                       #5% of fixed capital cost
                investment_tax_credit   =   0.4,                        #Investment tax credit
                upgrading_cost          =   True,                       #Upgrading cost, if any
                km_to_pipeline          =   data['km_to_pipeline'],     #Distance to pipeline in km)
                Grant_assistance        =   True,                       #Grant assistance, if any
                Grant_percentage        =   data['Grant_percentage'],   #Grant assistance, percentage of total capital cost
    )

    npv = tea.NPV
    irr = tea.solve_IRR()
    tci = tea.TCI

    #system_sys.save_report('System_RNG_WR_CN.xlsx') #This is to save a report with all the information of the system, including stream tables, unit tables, and economic tables. It can be useful for debugging and for understanding the system better.

    return {'NPV': npv, 'IRR': irr, 'TCI': tci, 'CN_ratio': Carbon_Nitrogen_ratio, 'biogas_kg_hr': biogas_flow, 
            'RNG': RNG_price_value, 'Natural_gas': Nat_gas, 
            'Grass_flow_kg_hr': grass_data['flowrate'],
            }

run_model(data)
