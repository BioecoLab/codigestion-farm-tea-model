
'UNITS'

import biosteam as bst
from biosteam import units, Facility, HeatUtility, HXutility
from biosteam import settings
import numpy as np
from typing import Optional
from scipy.optimize import fsolve
from math import ceil
from biosteam import Splitter
from thermosteam import separations, chemicals

#CEPCI information from: University of Manchester (2025). Chemical Engineering Plant Cost Index.
CEPCI = 800 # CEPCI: 2024
bst.settings.CEPCI = CEPCI
CEPCI1997 = 468.2 # CEPCI: 1997
CEPCI2005 = 386.5 # CEPCI: 1997
CEPCI2009 = 521.9 # CEPCI: 2009
CEPCI2010 = 550.8 # CEPCI: 2010
CEPCI2012 = 585.6 # CEPCI: 2012
CEPCI2014 = 576.1 # CEPCI: 2014
CEPCI2015 = 556.8 # CEPCI: 2015
CEPCI2017 = 567.5 # CEPCI: 2017
CEPCI2020 = 596.2 # CEPCI: 2020

#DIRECT COST FRACTIONS (all relative to purchased equipment cost)
dir_installation      = 0.30
dir_instrumentation   = 0.15
dir_piping            = 0.15
dir_electrical        = 0.10
dir_building_1        = 0.156
dir_building_2        = 0.075
dir_yard_improvement  = 0.05
dir_service_facility  = 0.00  # farm already has its own service facility

#INDIRECT COST FRACTIONS (relative to purchased equipment cost)
# note: we exclude working capital here because BioSTEAM handles that via WC_over_FCI
indir_engineering      = 0.20
indir_construction     = 0.30
indir_legal            = 0.02
indir_contractor_fees  = 0.15
indir_contingency      = 0.15

indirect_factor = sum([
    indir_engineering,
    indir_construction,
    indir_legal,
    indir_contractor_fees,
    indir_contingency
]) #0.82 total

__all__ = ('Tank', 'MixTank', 'StorageTank', 'tank_factory')

'Setting up unit operations'

class ManureStorageTank(bst.Unit):
    _outs_size_is_fixed = _ins_size_is_fixed = True
    _default_vessel_type = 'Storage lagoon'
    _default_tau =  360 # 15 days
    _default_V_wf = 1.0
    _default_vessel_material = 'Clay liner'
    _default_kW_per_m3 = 0.
    _F_BM_default = 1

    _units = {'Number of cows': 'count',
              'Pond Volume': 'm3',
              'Volume excavated': 'm3',
              'Top area covered': 'm2',
              'Storage time': 'days',
              'Power': 'kW'}

    def __init__(self, manure_storage, parlor_system, manure_solids_value, manure_per_day, manure_density, ID='', ins=None, outs=(), thermo=None,):
        super().__init__(ID, ins, outs, thermo)
        self.manure_storage = manure_storage
        self.parlor_system = parlor_system
        self.manure_solids_value= manure_solids_value
        self.manure_per_day = manure_per_day
        self.manure_density = manure_density
    

    def _run(self):
        self.outs[0].copy_like(self.ins[0])

    def _design(self):
        
        if not hasattr(self, 'number_of_cows'):
            raise ValueError("Number of cows has not been set for this storage tank.")

        self.design_results['Number of cows'] = self.number_of_cows  # Number of cows for cost basis

        #Design according to EPA report Cost Methodology for the Final Revisions to the National Pollutant Discharge Elimination System Regulation and the Effluent Guidelines for Concentrated Animal Feeding Operations

        'Pond volume = Sludge volume + Manure and wastewater + freeboard'
        r_sludge = 0.00455 #m3/kg of dry solids/day
        sludge_volume = r_sludge * (self.manure_per_day * self.manure_solids_value * (self._default_tau/24)) #m3/day

        'Parlor water was added in the manure stream'
    
        barn_water = 100 * self.number_of_cows / 264.17 #m3/day

        lagoon_influent = ((self.manure_per_day*(1-self.manure_solids_value))/self.manure_density)*(self._default_tau/24) #m3

        Pond_volume = (lagoon_influent + sludge_volume) #m3/day

        #Dimensions of the lagoon, modeled as a trapezoidal prism
        h_initial = 3.048 #m, 10 feet deep lagoon
        h_freeboard = 0.3048 #m, 1 ft freeboard
        h_lagoon = h_initial + h_freeboard #m, lagoon heigth
        w1=10 #m, bottom width
        f_soil = 0.05 # Compaction factor 20%
        self.Vol_excavated = Pond_volume*(1+f_soil) #m3 20% extra volume for excavation
        s = 3 # side slope 3:1
        w2 = w1+(2*s*h_lagoon)  #m, top width
        L = (2*self.Vol_excavated) / (h_lagoon*(w1+w2))  #m, length of the lagoon
        self.area_covered = w2 * L  #m2, area of the top of the lagoon
        self.Surface_area = Pond_volume / h_lagoon #m2
        width_cover = (Pond_volume / (2*h_lagoon))**0.5 #m, width of the cover assuming a lagoon
        self.cover_area = 2*width_cover**2 #m2, area of the cover assuming a lagoon
        
        self.design_units = {}
        self.design_results['Pond Volume'] = Pond_volume  # Volume excavated in m3
        self.design_results['Volume excavated'] = self.Vol_excavated  # Volume excavated in m3
        self.design_results['Top area covered'] = self.area_covered  # Area of the top of the lagoon to be covered
        self.design_results['Storage time'] = self._default_tau/24 #days


    def _cost(self):
        
        Mobilization_cost = 205 #USD
        Excavation_cost = 2.64 #USD/m3
        Compaction_cost = 0.54 #USD/m3
        Cover_area_cost = 15.07 #USD/m2 reference 2024 
        flare_cost = 2500 #USD cost for flare

        if self.parlor_system == True: #If parlor_system = True parlor system is hose system (conservative scenario)
            Wash_conveyance_cost = 7644 #USD cost for Hose wash system
        else:
            Wash_conveyance_cost = 11025 #USD cost for flush wash system

        Clay_liner_cost = 2.58 #USD/m2, cost of clay liner per m2
        Syntethic_liner_cost = 16.15 #USD/m2, cost of syntethic liner per m2
        
        if self.manure_storage == True:

            Purchase_cost = (
                Mobilization_cost + (Excavation_cost * self.Vol_excavated) + (Compaction_cost * self.Vol_excavated) + Wash_conveyance_cost
            ) * (CEPCI / CEPCI1997) + (self.area_covered*Cover_area_cost)  # Adjusting cost for inflation


            self.baseline_purchase_costs['Storage lagoon'] = Purchase_cost * (1 + dir_instrumentation + dir_piping + dir_yard_improvement + indirect_factor)

            annual_OPEX = (Purchase_cost * 0.05)/8760  # Assuming 5% of the cost is for operation cost per year to per hour
            Utility_kW = annual_OPEX/(bst.settings.electricity_price)  # Convert OPEX into Utility so BioSTEAM considers it in the design results
            self.power_utility(Utility_kW)
            self.design_results['Power'] = Utility_kW

        else:
            self.baseline_purchase_costs['Storage lagoon'] = 0


class GrassStorageTank(bst.Unit):
    _ins_size_is_fixed = _outs_size_is_fixed = True
    _default_tau = 360  # 15 days = 360 hours
    _default_V_wf = 1.0
    _default_kW_per_m3 = 0.

    _units = {'Tons of grass': 'metric ton',
              'Storage time': 'days'}

    def __init__(self, grass_storage, grass_flow, annual_bales, ID='', ins=None, outs=()):
        super().__init__(ID, ins, outs)
        self.grass_storage = grass_storage
        self.grass_flow = grass_flow
        self.annual_bales = annual_bales

    def _run(self):
        self.outs[0].copy_like(self.ins[0])

    def _design(self):
        if self.grass_flow == 'CN': #C/N ratio basis
            self.total_storage = (self.ins[0].F_mass/1000) * self._default_tau #Total Mg or metric ton of grass to be stored
            self.bales_per_month = ceil(self.annual_bales/12) #Total bales per month stored
            self.design_results['Tons of grass'] = self.total_storage  # Tons of grass for cost basis
            self.design_results['Storage time'] = self._default_tau/24 #days
            self.design_results['Monthly bales'] = self.bales_per_month
        elif self.grass_flow == 'LAND': #Land area basis
            tau = 720 #1 month of storage = 720 hours
            self.total_storage = (self.ins[0].F_mass/1000) * tau #Total Mg or metric ton of grass to be stored
            self.bales_per_month = ceil(self.annual_bales/12) #Total bales per month stored
            self.design_results['Tons of grass'] = self.total_storage
            self.design_results['Monthly bales'] = self.bales_per_month  # Tons of grass for cost basis
            self.design_results['Storage time'] = tau/24 #days

    def _cost(self):
        if self.grass_storage:
            if self.grass_flow == 'LAND': #Land area basis
            
                stacking_3_bales = (self.bales_per_month)/3 #Im stacking 3 bales high
                base_size = ceil(stacking_3_bales)*32 #number of bales in the base * 32 ft2 (bales base is 4*8)
                base_size = base_size*1.20 #20% extra space for maneuverability ft2
                
                base_cost = 7.445 #USD/ft2

                tarp_size = 48 * 80 #ft2
                tarp_cost = 1047.51 #USD/tarp 
                stacking_6_bales = (self.annual_bales - self.bales_per_month)/6 #Im stacking 6 bales high for the rest of the year
                tarp_area = ceil(stacking_6_bales)*32 * 1.1 # number of bales in the base * 32 ft2 (bales base is 4*8) * 20% extra for conservative purposes ft2
                total_tarp_cost = (tarp_cost/tarp_size) * tarp_area # USD

                Purchase_cost = (base_cost * base_size)

                self.baseline_purchase_costs['Pole barn'] = Purchase_cost * (1+dir_installation+dir_yard_improvement + indirect_factor) + total_tarp_cost   
                
            
            elif self.grass_flow == 'CN': #C/N ratio basis

                stacking_3_bales = (self.bales_per_month/2)/3 #Im stacking 3 bales high, considering 15 days of storage
                base_size = ceil(stacking_3_bales)*32 #number of bales in the base * 32 ft2 (bales base is 4*8)
                base_size = base_size*1.20 #20% extra space for maneuverability ft2
                
                base_cost = 7.445 #USD/ft2

                Purchase_cost = (base_cost * base_size)*(CEPCI/CEPCI)

                self.baseline_purchase_costs['Pole barn'] = Purchase_cost * (1+dir_installation+dir_yard_improvement + indirect_factor)

        else:
            self.baseline_purchase_costs['Pole barn'] = 0


class Shredder(bst.Unit):
    
    _units = {'Flow rate': 'kg/hr',
              'Power': 'kW',}

    def _design(self):

        self.total_flow = self.ins[0].F_mass
        self.total_flow_ton = self.total_flow / 1000  # Convert to tons/hr
        self.design_results['Flow rate'] = self.total_flow #kg/hr

        Electricity_per_ton = 22.1377 # kWh/ton
        Power = self.total_flow_ton * Electricity_per_ton  # kW
        self.design_results['Power'] = Power  # kW
        self.power_utility(power=self.design_results['Power']) # Adding power


    def _cost(self):

        baseline_costs = 795000 #USD
        base_capacity = 10 #tons/hr
        scaling_exponent = 0.6


        Purchase_cost = (
            baseline_costs * (self.total_flow_ton / base_capacity) ** scaling_exponent
        )*(CEPCI / CEPCI2020) 


        self.baseline_purchase_costs['Shredder'] = Purchase_cost * (1 + dir_installation + dir_electrical + dir_building_1 + dir_yard_improvement + indirect_factor)


class MixingTank(bst.Unit):
    
    _N_ins = 4
    _N_outs = 1

    auxiliary_unit_names = ('mixtank', 'heat_exchanger')
    
    _units = {'Power': 'kW',
              'Duty': 'kJ/hr',
              'Volume': 'm3',
              'Radius': 'm',
              'Height': 'm',
              'Total solids achieved': '%',
              }

    def __init__(self, heat_mixtank, Cp_manure_value, Cp_grass_value, Cp_water, Cp_mixture_value, temperature_digester, external_temperature_value, water_temperature, TS_digester, ID='', ins=None, outs=(), thermo=None, T=None, tau=1):
        super().__init__(ID, ins, outs, thermo)
        self.T = T
        self.tau = tau
        self.kW_per_m3 = 0
        self.heat_mixtank = heat_mixtank
        self.Cp_manure = Cp_manure_value
        self.Cp_grass = Cp_grass_value
        self.Cp_water = Cp_water
        self.Cp_mixture = Cp_mixture_value
        self.temperature_digester = temperature_digester
        self.external_temperature = external_temperature_value
        self.water_temperature = water_temperature
        self.TS_digester = TS_digester
        
        self.mixtank = self.auxiliary(
            'mix_tank',
            bst.MixTank,
            ins=self.ins,
            outs='mixed_streams'
        )
        self.heat_exchanger = self.auxiliary(
            'heat_exchanger',
            bst.HXutility, 
            ins=self.mixtank-0,
            outs=self.outs[0],
            T=self.T, 
        )


    def _run(self):
        
        manure_stream, grass_stream, water_stream, recirculation_stream = self.ins
        out = self.outs[0]

        def nonwater(s):
            return max(0.0, s.F_mass - s.imass['H2O'])
        
        dry_matter = (nonwater(manure_stream) + 
                      nonwater(grass_stream) + 
                      nonwater(recirculation_stream)
                      ) #Dry matter weight in kg/hr for all the inlet streams
        
        if dry_matter <= 1e-12:
            water_flowrate = 0
        else:
            self.total_weight_slurry = dry_matter / self.TS_digester #This is the total weight of the slurry (manure+grass+recirculation) after adding the water to obtain a moisture content of 90%. In kg/hr
            self.manure = manure_stream.F_mass
            self.grass = grass_stream.F_mass
            self.recirculation = recirculation_stream.F_mass
            water_flowrate = (self.total_weight_slurry - manure_stream.F_mass - grass_stream.F_mass - recirculation_stream.F_mass) #Water added to achieve 90% moisture content. In kg/hr

        water_stream.imass['H2O'] = water_flowrate
        water_stream.phase = 'l'
        water_stream.T = self.water_temperature + 273.15

        out.mix_from(self.ins)
        mixed_stream = self.outs[0]

        nonwater_out = max(0.0, out.F_mass - out.imass['H2O'])
        self.TS_achieved = (nonwater_out/out.F_mass) if out.F_mass > 0 else 0.0

        if self.heat_mixtank:
            # Apply heating if enabled
            self.heat_exchanger.T = self.T
            self.heat_exchanger._run()  
        else:
            # If heating is disabled, set outlet temperature to the mixed input temperature
            avg_T = sum(s.F_mass * s.T for s in self.ins) / sum(s.F_mass for s in self.ins)  # Mass-weighted average temperature
            mixed_stream.T = avg_T  # Set output temperature to the mixed stream temperature
            
            self.heat_exchanger.heat_utilities.clear()
            self.heat_exchanger.outs[0].copy_like(mixed_stream)



    def _design(self):
        
        if not self.heat_mixtank:

            #Reactor design
        
            V_wf = self.outs[0].F_vol * self.tau #Working volume m^3
            V_tank = V_wf/0.8   #Total tank volume, 80% is working volume m^3
            Tank_r = (V_tank/(np.pi*3))**(1/3) #radius m 
            Tank_h = Tank_r*3 #height m
            
            # If heating is off, clear heating utilities and return
            self.heat_exchanger.heat_utilities.clear()

            #Work from mixing

            Np = 0.35 #Power number for mixing, assuming Marine propeller
            rho = self.outs[0].rho #kg/m^3
            Ni = 150/60 #Impeller speed in Hz (150 rpm)
            Di = (1/2)*2*Tank_r #Impeller diameter in m
            Power = Np*rho*(Ni**3)*(Di**5) #Work in W
            Work = Power*3600/1000 #kW/hr

            self.design_results['Power'] = Power/1000 #kW
            self.design_results['Duty'] = 0 #kJ/hr
            self.design_results['Volume'] = V_tank
            self.design_results['Radius'] = Tank_r
            self.design_results['Height'] = Tank_h
            self.design_results['Total solids achieved'] = self.TS_achieved*100 
            

            self.mixtank.kW_per_m3 = 0 #Reset the default BioSTEAM power contribution
            self.power_utility(power=self.design_results['Power']) # Adding power that I manually calculated
            
            return
                
        
        #Equations to find duty (heat supplied) accounting for the Qrequired, Qloss, and Work from mixing

        #Qrequired

        T_out = self.T
        
        stream_ins = ((self.ins[0].F_mass * self.Cp_manure * (T_out-self.ins[0].T))+
                      (self.ins[1].F_mass * self.Cp_grass * (T_out-self.ins[1].T))+
                      (self.ins[2].F_mass * self.Cp_water * (T_out-self.ins[2].T))+
                      (self.ins[3].F_mass * self.Cp_water * (T_out-self.ins[3].T))) #property of the streams going in
        
        
        stream_outs = (self.outs[0].F_mass * self.Cp_mixture * (T_out-T_out)) #Its supposed to be zero
        
        #Reactor design to account for heat loss
        
        V_wf = self.outs[0].F_vol * self.tau #Working volume m^3
        V_tank = V_wf/0.8   #Total tank volume, 80% is working volume m^3
        Tank_r = (V_tank/(np.pi*3))**(1/3) #radius m 
        Tank_h = Tank_r*3 #height m
        Tank_area = (2*np.pi*Tank_r*Tank_h)+(2*np.pi*(Tank_r**2)) #Area of the tank m^2
        Tank_U = 0.39 # W/m^2 C

        #Heat loss

        Q_loss = Tank_U*Tank_area*(T_out-self.external_temperature) #Heat loss in W
        Q_loss = Q_loss*3600/1000 #kJ/hr

        #Work from mixing

        Np = 0.35 #Power number for mixing, assuming  Marine propeller
        rho = self.outs[0].rho #kg/m^3
        Ni = 150/60 #Impeller speed in Hz (150 rpm)
        Di = (1/2)*2*Tank_r #Impeller diameter in m
        Power = Np*rho*(Ni**3)*(Di**5) #Work in W
        Work = Power*3600/1000 #kJ/hr

        #Duty

        Duty = stream_ins - stream_outs + Q_loss - Work #kJ/hr
        
        #Adding results to the dictionary

        self.design_results['Power'] = Power/1000 #kW
        self.design_results['Duty'] = Duty #kJ/hr
        self.design_results['Volume'] = V_tank
        self.design_results['Radius'] = Tank_r
        self.design_results['Height'] = Tank_h
        
        self.mixtank.kW_per_m3 = 0 #Reset the default BioSTEAM power contribution
        self.power_utility(power=self.design_results['Power']) # Adding power that I manually calculated
        
        self.mixtank.simulate()
        self.heat_exchanger.simulate()
        self.heat_exchanger.results()

        self.heat_exchanger.heat_utilities.clear() #Clear the heat utility from what is default in BioSTEAM
        self.add_heat_utility(Duty, T_in=self.temperature_digester+273.15, T_out=self.temperature_digester+273.15)  #The temperatures in here don't do anything since the heat demand is set, but the line is still needed to run the code.

        #For the boiler to know how much steam to produce
        hu = self.create_heat_utility()
        hu(duty = Duty, T_in=self.temperature_digester+273.15, T_out=self.temperature_digester+273.15)


    def _cost(self):
        total_mass_flow = sum([stream.F_mass for stream in self.ins])  # Sum the mass flow rates of all input streams
       
        Tank_cost= (203000*((total_mass_flow/264116)**0.7))*(CEPCI/CEPCI2009) #NREL 2011

        Agitator_cost = (90000*((total_mass_flow/264116)**0.5))*(CEPCI/CEPCI2009) #NREL 2011

        Purchase_cost = Tank_cost + Agitator_cost

        self.baseline_purchase_costs['Tank'] = Purchase_cost * (1 + dir_installation + dir_piping + dir_electrical + dir_building_1 + dir_yard_improvement + indirect_factor)



__all__ = ('StirredTankReactor', 'STR', 'ContinuousStirredTankReactor', 'CSTR',)

class ContinousFermentation(bst.CSTR):
    
    _N_ins = 1
    _N_outs = 2   
    T_default = 37 + 273.15
    P_default = 101325
    tau_0_default = None
    V_max_default = 50000 # generates the max digester size in m3
    V_wf_default = 0.7 #Working volume of your anaerobic digester
    dT_hx_loop_default = 5 # 5 Kelvin of temperature variation in the heat exchanger

    batch_default = False
    adiabatic = False
    digester_efficiency = 1 # digester efficiency for biogas production

    auxiliary_unit_names = ('heat_exchanger')

    _units = {'Flowrate': 'kg/hr',
              'Reactor volume (with roof)': 'm3',
              'Reactor volume (tank)': 'm3',
              'Reactor volume gal': 'US gal',
              'Radius': 'm',
              'Number of reactors': '',
              'Heat required': 'kJ/hr',
              'Heat loss': 'kJ/hr',
              'Duty': 'kJ/hr',
              'Power': 'kW',
              }

    def __init__(self, upgrading, hrt_hr, Cp_mixture_value, k_mixture_value, external_temperature_value, temperature_digester, CH4_mass_yield, CO2_mass_yield, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.upgrading = upgrading
        self.hrt_hr = hrt_hr
        self.Cp_mixture = Cp_mixture_value
        self.k_mixture = k_mixture_value
        self.external_temperature = external_temperature_value
        self.temperature_digester = temperature_digester
        self.CH4_mass_yield = CH4_mass_yield
        self.CO2_mass_yield = CO2_mass_yield


    def _init(
            self, 
            T: Optional[float]=None, 
            P: Optional[float]=None, 
            dT_hx_loop: Optional[float]=None,
            tau: Optional[float]=None,
            V_wf: Optional[float]=None, 
            V_max: Optional[float]=None,
            kW_per_m3: Optional[float]=None,
            vessel_material: Optional[str]=None,
            vessel_type: Optional[str]=None,
            tau_0: Optional[float]=None,
            batch: Optional[bool]=None,
            adiabatic: Optional[bool]=None,
        ):



        if adiabatic is None: adiabatic = False
        self.T = self.T_default if T is None else T
        self.P = self.P_default if P is None else P
        self.dT_hx_loop = self.dT_hx_loop_default if dT_hx_loop is None else abs(dT_hx_loop)
        self.tau = self.tau_default if tau is None else tau
        self.V_wf = self.V_wf_default if V_wf is None else V_wf
        self.V_max = self.V_max_default if V_max is None else V_max
        self.kW_per_m3 = self.kW_per_m3_default if kW_per_m3 is None else kW_per_m3
        self.vessel_material = 'Stainless steel 316' if vessel_material is None else vessel_material
        self.vessel_type = 'Vertical' if vessel_type is None else vessel_type
        self.tau_0 = self.tau_0_default if tau_0 is None else tau_0
        self.batch = self.batch_default if batch is None else batch
        self.vent = None

        self.heat_exchanger_vent = self.auxiliary(
            'heat_exchanger_vent',
            bst.HXutility,
            ins = None,
            outs = self.outs[0],
            T = self.T, 
        )
        self.heat_exchanger_effluent = self.auxiliary(
            'heat_exchanger_effluent',
            bst.HXutility,
            ins = None,
            outs = self.outs[1],
            T = self.T, 
        )


    def _design(self):

        #Reactor design (Dimensions)

        V_wf = (self.ins[0].F_vol) * self.tau #Working volume m^3
        V_digester = V_wf/0.7   #Total digester volume, 70% is working volume m^3
        self.V_digester_gallons = V_digester*264.172 #Total digester volume in gallons
        V_tank = V_digester*0.8  #Total tank (cylinder) volume m^3
        r_tank = (V_tank/(np.pi*3))**(1/3) #radius m
        h_tank = r_tank*3 #height m
        tank_area = 2*np.pi*r_tank*h_tank #Area of the tank m^2


        #Finding digester roof height:
        def equation(h, r, V):
            return h**3 - 3*r*h**2 + (3*V/np.pi)

        r_roof = r_tank  # radius of the sphere example
        V_roof = V_digester*0.2  # volume of the spherical cap example

        #This is the initial guess for the height of the roof. It is the same as the radius of the digester wall
        h_initial_guess = r_roof
        h_solution = fsolve(equation, h_initial_guess, args=(r_roof, V_roof))
        roof_height= h_solution[0]

        
        #Equations to find duty (heat supplied) accounting for the Qrequired, Qloss, and Work from mixing
        T_out = self.T
        
        stream_ins = ((self.ins[0].F_mass * self.Cp_mixture * (T_out-self.ins[0].T))) #property of the streams going in
        
        
        stream_outs = (self.outs[0].F_mass * self.Cp_mixture * (T_out-T_out))
        
        #Heat transfer coefficient for Slurry - Equations for heat loss

        rho = self.ins[0].rho #kg/m^3
        Ni = 20/60 #Impeller speed in Hz (20 rpm)
        Di = 2.5 #((1/3)*2*r_tank)/(2**(1/2)) #Impeller diameter in m
        Viscosity = 0.924 # kg/m s

        Reynolds = (rho*(Di**2)*Ni)/Viscosity #Reynolds number

        Cp = self.Cp_mixture #kJ/kg C
        k = self.k_mixture #W/m C

        Prandtl = (Cp*1000*Viscosity)/k #Prandtl number

        Nusselt = (0.36*(Reynolds**0.67)*(Prandtl**0.33)) #Nusselt number

        h_digestate = Nusselt*k/(r_tank*2) #W/m2 C                                                                                                                                                                                                                                                                                                                                                                                                                                   m^2 C

        Design = self.design_results
        ins_F_vol = sum([i.F_vol for i in self.ins if i.phase != 'g'])
        V_total = ins_F_vol * self.tau / self.V_wf
        N = ceil(V_total/self.V_max)
        if N == 0:
                V_reactor = 0
        else:
                V_reactor = V_total / N
        
        self.design_results['Reactor volume (with roof)'] = V_digester #m3
        self.design_results['Reactor volume (tank)'] = V_tank #m3
        self.design_results['Reactor volume gal'] = self.V_digester_gallons
        self.design_results['Radius'] = r_tank #m
        self.design_results['Number of reactors']=N                

        #Conduction heat transfer through the walls. Assuming structure of Penn State digester
        #4 inches Styrofoam
        Thick_styrofoam = 0.1016 #m
        k_styrofoam = 0.033 #W/m C

        #4 inches Concrete
        Thick_concrete = 0.1016 #m
        k_concrete = 1.5 #W/m C

        Wall_resistance = (Thick_styrofoam/(k_styrofoam)) + (Thick_concrete/(k_concrete)) #m^2 C/W
        
        #Convection for air
        #Air at natural free convection
        
        h_air = 10 #W/m^2 C

        #Heat loss

        Q_loss = (T_out-self.external_temperature)/((1/h_digestate)+ Wall_resistance + (1/h_air))  #Heat loss in W/m2
        Q_loss = Q_loss*tank_area*3600/1000 #kJ/hr

        #Heat supplied to the digester

        Duty = stream_ins - stream_outs + Q_loss #kJ/hr

        #Work from mixing - Work is already calculated in the heat loss. This is only to account for power for mixing

        Np = 0.35 #Power number for mixing, assuming Marine propeller
        Power = (Np*rho*(Ni**3)*(Di**5))*2 #Work in W, two impellers for mixing

        #Adding results to the dictionary
        self.design_results['Heat required'] = stream_ins-stream_outs #kJ/hr
        self.design_results['Heat loss'] = Q_loss #kJ/hr
        self.design_results['Duty'] = Duty #kJ/hr
        self.design_results['Power'] = Power/1000 #kW
        
        self.kW_per_m3 = 0 #Reset the default BioSTEAM power contribution
        self.power_utility(power=self.design_results['Power']) # Adding power that I manually calculated
        
        'Steam to heat the digester will come from the CHP unit if modeled, if not from the boiler'



    def _setup(self):
        super()._setup()
        chemicals=bst.Chemicals
        self.fermentation_reaction1 = bst.Reaction('VolatileSolids -> CH4', 'VolatileSolids', self.CH4_mass_yield*self.digester_efficiency, basis = 'wt')
        self.fermentation_reaction2 = bst.Reaction('VolatileSolids -> CO2', 'VolatileSolids', self.CO2_mass_yield*self.digester_efficiency, basis='wt')


    def _run(self): # Mainly source code
        effluent = bst.Stream('effluent')
        vent = bst.Stream('vent')
        effluent.mix_from(self.ins, energy_balance=True) #True to analize temperature change
        effluent.T = self.T
        effluent.P = self.P
        effluent.phase = 'l'

        if not effluent.mol.any():
            raise RuntimeError("Effluent stream has no chemicals")

        self.fermentation_reaction1(effluent)
        self.fermentation_reaction2(effluent)

        vent.phase = 'g'
        vent.empty()
        vent.receive_vent(effluent, energy_balance=True)

        liquid = effluent.copy()
        liquid.phase = 'l'

        self.heat_exchanger_vent.ins[0] = vent  # vent stream
        self.heat_exchanger_effluent.ins[0] = effluent  # effluent stream
        
        self.heat_exchanger_vent.simulate()
        self.heat_exchanger_effluent.simulate()

        self.outs[0].copy_like(self.heat_exchanger_vent.outs[0])
        self.outs[1].copy_like(self.heat_exchanger_effluent.outs[0])
    
    def _cost(self):
        baseline_costs = 6750000
        base_capacity = 31000000 # gallons
        scaling_exponent = 0.6
        
        Purchase_cost = (baseline_costs*((self.V_digester_gallons/base_capacity)**scaling_exponent))*(CEPCI/CEPCI2010)

        self.baseline_purchase_costs['CSTR'] = Purchase_cost * (1 + dir_instrumentation + dir_piping + dir_electrical + dir_yard_improvement + indirect_factor)


class Biogas_cooling(HXutility):

    def __init__(self, ID='', ins=None, outs=(), *, T=None, **kwargs):
        super().__init__(ID, ins, outs, T=T, **kwargs)
        self.T = T  # Cooling biogas to external temperature (K)
    
    def _design(self):

        T_in = self.ins[0].T
        T_out = self.T

        self.outs[0].copy_like(self.ins[0])
        self.outs[0].T = T_out

        self._heat_utility = None
        
    def _cost(self):
        
        Purchase_cost = 9026 #USD Accounting for water trap
        
        self.baseline_purchase_costs['Water Trap'] = Purchase_cost * (1 + dir_installation + dir_piping + indirect_factor)



## GAS UPGRADING
class H2SRemovalUnit(bst.Unit):
    
    _units = {'Power': 'kW',
              'Inlet flow rate': 'Nm3/hr',
              'Pressure': 'Pa',
              'Temperature': '°C',}

    def _run(self):
        self.outs[0].copy_like(self.ins[0])

    def _design(self):

        R = 8.3145 #m3 Pa / mol K
        molar_mass_CH4 = 16.04 #g/mol
        molar_mass_CO2 = 44.01 #g/mol
        molar_mass_H2O = 18.015 #g/mol
        mass_CH4 = self.ins[0].imass['CH4']
        mass_CO2 = self.ins[0].imass['CO2']
        mass_H2O = self.ins[0].imass['H2O']
        moles_CO2 = (mass_CO2*1000)/molar_mass_CO2 #moles/h
        moles_CH4 = (mass_CH4*1000)/molar_mass_CH4 #moles/h
        #moles_H2O = (mass_CH4*1000)/molar_mass_CH4 #moles/h
        moles_total = moles_CH4 + moles_CO2 #moles/h
        self.ins[0].get_property('P', 'Pa')
        self.ins[0].get_property('T', 'K')
        P = 101325 #Pa
        T = 0 + 273.15 #K Assuming normal conditions for biogas to measure

        self.metric_flow = (moles_total * R * T)/P # Metric flow at almost normal conditions of biogas Nm3/h
       
        self.design_results['Inlet flow rate'] = self.metric_flow
        self.design_results['Pressure'] = P
        self.design_results['Temperature'] = T-273.15

    
    def _cost(self):

        Cost_per_m3 = 0.0025 #USD/m3 of biogas
        Cost_per_hr = self.metric_flow * Cost_per_m3  # Cost per hour based on the feed rate USD/hr

        # Assuming an annualized OPEX cost for the H2S removal system

        Utility_kW = Cost_per_hr/(bst.settings.electricity_price)  # Convert OPEX into Utility so BioSTEAM considers it in the design results
        self.power_utility(Utility_kW)
        self.design_results['Power (kW)'] = Utility_kW




#Gas Purification using membrane filtration. This filtration unit was build off of a splitter unit in biosteam.
__all__ = ('Membrane_Filtration') 
class Membrane_Separation(Splitter):
    _units = {'Biogas inlet flow rate': 'Nm3/hr',
                'Methane inlet flow rate': 'Nm3/hr',
                'Methane outlet flow rate': 'kg/hr',
                'Carbon dioxide outlet flow rate': 'kg/hr',
                'Pressure': 'Pa',
                'Temperature': '°C',
                'Methane composition': '% vol',
                'HHV RNG': 'BTU/ft3',
                'Energy flow of methane': 'Btu/hr',
                'Annual energy flow of methane': 'MMBTU/yr',
                'Power': 'kW',
                }

    _default_equipment_lifetime = 15 # 15 years equipment lifetime
    _materials_and_maintenance = {'Membrane replacement': 4000}


    def __init__(self, ID='', ins=None, outs=(), *, order=None, split=None, P=None, cap_factor=None):
        if split is None:
            split = {'CH4': 0.947, 'CO2': 0.053, 'Water':0}
        
        super().__init__(ID, ins, outs, order=order, split=split)
        self.P = 4.0e5  # Membrane exit pressure methane (4 bar)
        self.cap_factor = cap_factor  # Yearly capacity factor for cost calculations


    def _run(self):
        
        super()._run()

        
        P = self.P if self.P is not None else self.ins[0].P
        for out in self.outs:
            out.P = P
            out.T = self.ins[0].T

        P_CO2 = 101325 #Pa, membrane exit pressure CO2 (1 atm)
        self.outs[1].P = P_CO2
        self.outs[1].T = self.ins[0].T


    def _design(self):
        R = 8.3145 #m3 Pa / mol K
        molar_mass_CH4 = 16.04 #g/mol
        molar_mass_CO2 = 44.01 #g/mol
        mass_CH4 = self.ins[0].imass['CH4']
        mass_CO2 = self.ins[0].imass['CO2']
        moles_CO2 = (mass_CO2*1000)/molar_mass_CO2 #moles/h
        moles_CH4 = (mass_CH4*1000)/molar_mass_CH4 #moles/h
        moles_total = moles_CH4 + moles_CO2 #moles/h
        self.ins[0].get_property('P', 'Pa')
        self.ins[0].get_property('T', 'K')
        P = 101325 #Pa
        T = 0 + 273.15 #K Assuming normal conditions for biogas to measure
        mass_flowrate_CH4 = self.outs[0].F_mass #kg/hr
        mass_flowrate_CO2 = self.outs[1].F_mass #kg/hr

        self.metric_flow = (moles_total * R * T)/P # Metric flow at almost normal conditions of biogas Nm3/h
        CH4_metric_flow_inlet = (moles_CH4 * R * T)/P #Nm3/hr
       
        self.design_results['Biogas inlet flow rate'] = self.metric_flow
        self.design_results['Methane inlet flow rate'] = CH4_metric_flow_inlet
        self.design_results['Methane outlet flow rate'] = mass_flowrate_CH4
        self.design_results['Carbon dioxide outlet flow rate'] = mass_flowrate_CO2
        self.design_results['Pressure'] = P
        self.design_results['Temperature'] = T-273.15
        
        #Recovery of 99% of methane but composition of 98% vol methane in the RNG
        CH4_out = moles_CH4 * 0.99 #moles/h
        total_out = CH4_out / 0.98 #moles/h
        CO2_out = total_out - CH4_out #moles/h
        CH4_out_mass = CH4_out * molar_mass_CH4 / 1000  # kg/h
        CO2_out_mass = CO2_out * molar_mass_CO2 / 1000  # kg/h
        z_mass_CH4 = CH4_out_mass / (CH4_out_mass + CO2_out_mass)  # % mass of CH4 in outlet
        
        mass_CH4_out = self.outs[0].imass['CH4']
        mass_CO2_out = self.outs[0].imass['CO2']
        z_mol_CH4 = CH4_out/total_out #% mol

        HHV_methane_BTU_mol = 843.6 #Btu/mol
        HHV_methane_BTU_ft3 = 1069 #Btu/ft3
        energy_flow_methane = CH4_out * HHV_methane_BTU_mol #Btu/hr
        annual_energy_BTU = energy_flow_methane * (24*(365*self.cap_factor)/1000000) #MMBTU/yr cap factor of 95%
        HHV_RNG = z_mol_CH4 * HHV_methane_BTU_ft3 #Btu/ft3
        self.design_results['Methane composition'] = z_mol_CH4 # Minimum of 95% vol, and no more than 2% vol of CO2 according to PECO energy company Philadelphia
        self.design_results['HHV RNG'] = HHV_RNG # Minimum heating value for injection is 970 BTU/ft3 and max 1070 BTU/ft3 according to PECO energy company Philadelphia
        self.design_results['Energy flow of methane'] = energy_flow_methane #Btu/hr
        self.design_results['Annual energy flow of methane'] = annual_energy_BTU #MMBTU/yr
        
        

        Electricity_use = 0.35 #kwh/Nm3
        Utility_kw = Electricity_use * self.metric_flow
        self.design_results['Power'] = Utility_kw
        self.power_utility(Utility_kw)

    def _cost(self):
        baseline_costs = 985000
        base_capacity = 500 # Nm3/h
        scaling_exponent = 0.6
        
        Purchase_cost = (baseline_costs*((self.metric_flow/base_capacity)**scaling_exponent))*(CEPCI/CEPCI2017)
        
        self.baseline_purchase_costs['Membrane Separation'] = Purchase_cost * (1 + dir_installation + dir_instrumentation + dir_piping + dir_electrical + dir_building_2 + dir_yard_improvement + indirect_factor)


__all__=('SolidsSeparator','ScrewPress')

class SolidsSeparator(Splitter):

    _N_ins = 1
    _ins_size_is_fixed = False
    
    def _init(self, split, 
              order=None, moisture_content=None, 
              moisture_ID=None, strict_moisture_content=None):
        super()._init(order=order, split=split)
        self.moisture_content = moisture_content
        self.strict_moisture_content = strict_moisture_content
        if moisture_content is not None:
            if moisture_ID is None:
                moisture_ID = '7732-18-5'
            self.moisture_ID = moisture_ID
    
    def _run(self):
        if self.moisture_content is None:
            separations.mix_and_split(
                self.ins, *self.outs, self.split,
            )
        else:
            self.isplit[self.moisture_ID] = 0.
            separations.mix_and_split_with_moisture_content(
                self.ins, *self.outs, self.split, 
                self.moisture_content, self.moisture_ID,
                self.strict_moisture_content,
            )

    def _cost(self):
        baseline_costs = 275000 #USD
        base_capacity = 5520.43 # kg/h
        scaling_exponent = 0.6
        
        Purchase_cost = (baseline_costs*((self.ins[0].F_mass/base_capacity)**scaling_exponent))*(CEPCI/CEPCI2005)

        self.baseline_purchase_costs['Solids_Separator'] = Purchase_cost * (1 + dir_installation + dir_piping + dir_electrical + dir_yard_improvement + indirect_factor)


        annual_OPEX = (Purchase_cost * 0.02)/8760  # Assuming 2% of the cost is for operation cost per year to per hour
        Utility_kW = annual_OPEX/(bst.settings.electricity_price)  # Convert OPEX into Utility so BioSTEAM considers it in the design results
        self.power_utility(Utility_kW)
        self.design_results['Power (kW)'] = Utility_kW

    
class DigestateStorageTank(bst.Unit):
    _outs_size_is_fixed = _ins_size_is_fixed = True
    _default_vessel_type = 'Field erected'
    _default_tau = 4320  # 180 days according to EPA
    _default_V_wf = 1.0
    _default_kW_per_m3 = 0.

    _units = {'Number of cows': 'count',
              'Pond Volume': 'm3',
              'Volume excavated': 'm3',
              'Surface area': 'm2',
              'Storage time': 'days',
              'Power': 'kW'}

    def __init__(self, ID, ins, outs, digestate_storage):
        super().__init__(ID, ins, outs)
        self.digestate_storage = digestate_storage

    def _run(self):
        self.outs[0].copy_like(self.ins[0])

    def _design(self):
        if not hasattr(self, 'number_of_cows'):
            raise ValueError("Number of cows has not been set for this storage tank.")

        self.design_results['Number of cows'] = self.number_of_cows  # Number of cows for cost basis
    
        Pond_volume = (self.ins[0].F_mass / self.ins[0].rho) * self._default_tau  # Total volume in m³ based on mass flow rate and tau

        #Dimensions of the lagoon
        h = 3.048 + 0.3048 #m, 10 feet deep lagoon + 1 ft freeboard
        self.Vol_excavated = Pond_volume / 1.2 #m3 20% extra volume for excavation
        self.Surface_area = Pond_volume / h #m2
        width_cover = (Pond_volume / (h*2))**0.5 #m, width of the cover assuming a lagoon
        self.cover_area = 2*width_cover**2 #m2, area of the cover assuming a lagoon


        
        self.design_results['Pond Volume'] = Pond_volume  # Volume excavated in m3
        self.design_results['Volume excavated'] = self.Vol_excavated  # Volume excavated in m3
        self.design_results['Surface area'] = self.Surface_area  # Volume excavated in m3
        self.design_results['Storage time'] = self._default_tau/24 #days


    def _cost(self):

        Mobilization_cost = 205 #USD
        Excavation_cost = 2.64 #USD/m3
        Compaction_cost = 0.54 #USD/m3
        Clay_liner_cost = 2.58 #USD/m2, cost of clay liner per m2
        Syntethic_liner_cost = 16.15 #USD/m2, cost of syntethic liner per m2
        Cover_area_cost = 43.06 #USD/m2
        flare_cost = 2500 #USD cost for flare

        if self.digestate_storage:
            
            #I am accounting for delivery and construction cost
            Purchase_cost = (
                Mobilization_cost + (Excavation_cost * self.Vol_excavated) + (Compaction_cost * self.Vol_excavated) + self.cover_area * Cover_area_cost + flare_cost
            ) * (CEPCI / CEPCI1997)  # Adjusting cost for inflation


            self.baseline_purchase_costs['Storage lagoon'] = Purchase_cost * (1 + dir_instrumentation + dir_piping + dir_yard_improvement + indirect_factor)
            #If adding liner 
            #self.baseline_purchase_costs['Storage lagoon'] = (
            #                Mobilization_cost + (Excavation_cost * self.Vol_excavated) + (Compaction_cost * self.Vol_excavated) + (Clay_liner_cost * self.Surface_area) + (Syntethic_liner_cost * self.Surface_area) self.cover_area * Cover_area_cost + flare_cost
            #            )
            #self.power_utility = (self.baseline_purchase_costs['Storage lagoon'] * 0.05)/8760  # Assuming 5% of the cost is for operation cost per year to per hour

            annual_OPEX = (Purchase_cost * 0.05)/8760  # Assuming 5% of the cost is for operation cost per year to per hour
            Utility_kW = annual_OPEX/(bst.settings.electricity_price)  # Convert OPEX into Utility so BioSTEAM considers it in the design results
            self.power_utility(Utility_kW)
            self.design_results['Power (kW)'] = Utility_kW        
        
        else:
            self.baseline_purchase_costs['Storage tank'] = 0


__all__ = ('BoilerTurbogenerator',)

class CHPUnit(bst.Unit):
    _N_ins = 2  # biogas, water
    _N_outs = 2  # emissions, steam
    
    _units = {'Water inlet flow rate': 'kg/hr',
              'Work': 'kW',
              'Steam outlet flow rate': 'kg/hr',
              'CHP capacity': 'kW',
              'Electricity produced': 'kWh',
              'Steam outlet duty': 'kJ/hr',
              'Steam left after Digester heating': 'kg/hr',
              'Digester heating duty': 'kJ/hr',
              'Steam extra needed for Digester': 'kg/hr',
              'Annual electricity': 'MWh/year',}
    

    def __init__(self, ID='', ins=None, outs=('emissions', 'steam'), thermo=None, *,
                 CHP_efficiency= None,
                 CHP_elec_efficiency= None,
                 thermal_efficiency=None,
                 boiler_efficiency_basis='HHV',
                 T_emissions=None,
                 satisfy_system_electricity_demand=False,
                 chp_nameplate_capacity=None,
                 natural_gas_price=None,
                 Digester_unit=None,
                 water_temperature=None,
                 Cp_H2O=None,
                 cap_factor=None):
        super().__init__(ID, ins, outs, thermo)

        self.CHP_efficiency = CHP_efficiency
        self.electric_efficiency = CHP_elec_efficiency
        self.thermal_efficiency = thermal_efficiency or (CHP_efficiency - CHP_elec_efficiency)
        self.boiler_efficiency_basis = boiler_efficiency_basis
        self.T_emissions = T_emissions or 400  # default to 400K if not given
        self.satisfy_system_electricity_demand = satisfy_system_electricity_demand
        self.chp_nameplate_capacity = chp_nameplate_capacity
        self.electricity_without_natural_gas = 0
        self.Digester_unit = Digester_unit
        self.water_temperature = water_temperature or 25  # default to 25C if not given
        self.Cp_H2O = Cp_H2O or 4.184  # kJ/kg K
        self.cap_factor = cap_factor

        if natural_gas_price is not None:
            self.natural_gas_price = natural_gas_price

    @property
    def steam(self):
        return self.outs[1]

    @property
    def water(self):
        return self.ins[1]

    @property
    def natural_gas_price(self):
        return bst.stream_utility_prices['Natural gas']

    @natural_gas_price.setter
    def natural_gas_price(self, new_price):
        bst.stream_utility_prices['Natural gas'] = new_price


    def _design(self):
        feed_gas, water_input = self.ins
        emissions, steam = self.outs
        chemicals = self.chemicals
        Design = self.design_results

        # Set emissions stream properties
        emissions = self.outs[0]
        emissions.T = self.T_emissions
        emissions.P = 101325
        emissions.phase = 'g'
        emissions.mol[:] = 0

        combustion_rxns = chemicals.get_combustion_reactions()
        if feed_gas.isempty():
            non_empty_feeds = []
        else:
            non_empty_feeds = [feed_gas]

        H_combustion = 0

        for feed in non_empty_feeds:
            emissions.mol[:] += feed.mol
            if self.boiler_efficiency_basis == 'LHV':
                H_combustion += feed.imass['CH4'] * 50000  # kJ/hr
            elif self.boiler_efficiency_basis == 'HHV':
                H_combustion += feed.imass['CH4'] * 55500  # kJ/hr
            else:
                raise ValueError(f"Invalid basis: {self.boiler_efficiency_basis}")

        combustion_rxns.force_reaction(emissions.mol)
        emissions.imol['O2'] = 0

        #Capacity of unit
        self.chp_nameplate_capacity = (H_combustion * 24) / ((3600 * 24) / 0.315) # Capacity of the CHP unit (kW)  # kW

        #Calculating amount of steam
        Q_steam = H_combustion * self.thermal_efficiency #kJ/hr - This is the amount of energy that will be used to produce steam.
        #Enthalpy of vaporization of water coming in at 25C and 1 atm
        # Calculate energy used for steam
        #Q_steam = H_combustion * self.boiler_efficiency  # kJ/hr
        deltah_sensible = self.Cp_H2O * (100-self.water_temperature) # kJ/kg
        deltah_vap = 2256.4  # kJ/kg water at 100°C
        
        #H_vap = 2442.5  #kJ/kg - This is the enthalpy of vaporization of water at 25C and 1 atm. This is used to calculate the amount of steam produced. Source: Pauline Doran Appendix D
        
        #H_sensible to heat from 25C to 100C and H_vap is for phase change
        h = deltah_sensible + deltah_vap # kJ/kg
        steam_flow = Q_steam / h  #kg/hr - This is the amount of steam produced by the boiler. This is calculated by taking the energy used to produce steam and dividing it by the enthalpy of vaporization of water at 25C and 1 atm.

        water_input = bst.Stream('CHP_water', T=298.15, P=101325)
        water_input = self.ins[1]  # Water input stream
        water_input.phase = 'l'  # Set phase to liquid
        water_input.imol['7732-18-5'] = (steam_flow) / 18.01528  # Convert kg/hr to kmoles/hr
                
        Q_to_digester = self.Digester_unit.design_results['Duty']  # kJ/hr - This is the amount of energy that will be used to heat the digester
        Q_net = Q_steam - Q_to_digester  # kJ/hr - This is the net energy available for steam production after accounting for the energy used to heat the digester
        steam = bst.Stream('CHP_steam', T=self.T_emissions, P=101325, phase='g')
        steam = self.outs[1]  # Steam output stream
        if Q_net > 0:
            flow_steam_net = (Q_net / h) # kg/hr
            steam.imol['7732-18-5'] = (flow_steam_net)/18.01528  # kmol/hr - This is the amount of steam produced by the boiler after accounting for the energy used to heat the digester. This is calculated by taking the net energy available for steam production and dividing it by the enthalpy of vaporization of water at 25C and 1 atm.
            steam.price = 0 #Not getting any profit from steam
            flow_needed = 0
        else:
            flow_needed = (-Q_net / h)  # kg/hr - flow extra needed to heat the digester
            flow_steam_net = 0  # kg/hr - No steam produced left, all steam is used to heat the digester
            steam.imol['7732-18-5'] = 0  # kg/hr - No steam produced left, all steam is used to heat the digester
            steam.price = 0

        #Water and steam flowrate
        self.design_results['Water inlet flow rate'] = steam_flow #kg/hr
        self.design_results['Steam outlet flow rate'] = steam_flow #kg/hr
        self.design_results['Steam outlet duty'] = steam_flow*h #kJ/hr
        self.design_results['Digester heating duty'] = Q_to_digester #kJ/hr
        self.design_results['Steam left after Digester heating'] = flow_steam_net #kg/hr
        self.design_results['Steam extra needed for Digester'] = flow_needed #kJ/hr



        #Electricity production
        Q_electric = H_combustion * self.electric_efficiency  #kJ/hr - This is the amount of energy released as electricity. This is calculated by taking the total energy produced by combustion and multiplying it by the electric efficiency of the CHP unit.
        Electricity = Q_electric / 3600  #kW - This is the amount of electricity produced by the CHP unit. This is calculated by taking the total energy released as electricity and dividing it by 3600 to convert from kJ/hr to kW.
        self.design_results['Electricity produced'] = Electricity #kW per 1 hour then kWh
        self.chp_nameplate_capacity = Electricity  # Capacity of the CHP unit (kW)  # kW
        self.design_results['CHP capacity'] = self.chp_nameplate_capacity  # kW
        annual_electricity = Electricity * 24 * (365*self.cap_factor)/1000  # MWh/yr
        self.design_results['Annual electricity'] = annual_electricity # MWh/yr

        # Cooling duty is the excess heat that needs to be removed
        self.cooling_duty = H_combustion * (1 - self.CHP_efficiency) # A CHP unit will remove excess heat with compressed air


        if Q_net < 0:
            hu = bst.HeatUtility()
            hu(-Q_net, T_in=steam.T)
            self.heat_utilities.append(hu)
        
        
        
        self.electricity_without_natural_gas = Electricity

        if self.satisfy_system_electricity_demand:
            boiler = self.cost_items['Boiler']
            rate_boiler = boiler.kW * steam_flow / boiler.S
            Design['Work'] = Electricity - rate_boiler  # adjust for system electricity demand

    def _cost(self):
        self.power_utility.production = self.design_results['Electricity produced']

        baseline_costs = 4111200
        base_capacity_chp = 5240
        scaling_exponent_chp = 0.6

        Purchase_cost = (
            baseline_costs *
            (self.chp_nameplate_capacity / base_capacity_chp) ** scaling_exponent_chp
        )*(CEPCI/CEPCI2014)

        self.baseline_purchase_costs['CHP'] = Purchase_cost * (1 + dir_installation + dir_instrumentation + dir_piping + dir_electrical + dir_building_2 + dir_yard_improvement + indirect_factor)

    def _run(self):
        pass    



class BoilerUnit(bst.Facility):
    _N_ins = 2
    _N_outs = 2
    _units = {'Flow rate': 'kg/hr',
              'Natural gas used': 'kg/hr',}
    network_priority = 0

    def __init__(self, ID='', ins=None, outs=('emissions', 'steam'), thermo=None, *,
                 CHP_efficiency=0.685,
                 electric_efficiency=0.35,
                 boiler_efficiency=0.95,
                 boiler_efficiency_basis='HHV',
                 T_emissions=None,
                 satisfy_system_electricity_demand=False,
                 chp_nameplate_capacity=None,
                 T_steam=383.15,
                 natural_gas_price=None,
                 water_price=None,
                 water_temperature=None,
                 Cp_H2O=None,
                 Digester_unit=None):
        super().__init__(ID, ins, outs, thermo)

        self.CHP_efficiency = CHP_efficiency
        self.electric_efficiency = electric_efficiency
        self.boiler_efficiency = boiler_efficiency
        self.T_steam = T_steam
        self.boiler_efficiency_basis = boiler_efficiency_basis
        self.T_emissions = T_emissions or 400  # default to 400K if not given
        self.satisfy_system_electricity_demand = satisfy_system_electricity_demand
        self.chp_nameplate_capacity = chp_nameplate_capacity
        self.electricity_without_natural_gas = 0
        self.water_temperature = water_temperature or 25  # default to 25C if not given
        self.Cp_H2O = Cp_H2O or 4.184  # kJ/kg K
        self.Digester_unit = Digester_unit

        if natural_gas_price is not None:
            self.natural_gas_price = natural_gas_price
        if water_price is not None:
            self.water_price = water_price

    @property
    def natural_gas(self):
        return self.ins[0]

    @property
    def water(self):
        return self.ins[1]

    @property
    def steam(self):
        return self.outs[1]

    @property
    def emissions(self):
        return self.outs[0]
    
    @property
    def natural_gas_price(self):
        return bst.stream_utility_prices['Natural gas']
    
    @natural_gas_price.setter
    def natural_gas_price(self, price):
        bst.stream_utility_prices['Natural gas'] = price


    def _load_utility_agents(self):
        """Load heat utility agents from all other units in the system."""
        self.steam_utilities = {
            hu for u in self.system.units
               for hu in u.heat_utilities
        }

    def _design(self):

        Q_to_digester = self.Digester_unit.design_results['Duty']

        # Calculate energy input from CH4
        if self.boiler_efficiency_basis == 'HHV':
            H_combustion = Q_to_digester/ self.boiler_efficiency
            mass_CH4 = H_combustion / 55500  # kg/hr
        elif self.boiler_efficiency_basis == 'LHV':
            H_combustion = Q_to_digester / self.boiler_efficiency
            mass_CH4 = H_combustion / 50000
        else:
            raise ValueError("Invalid boiler efficiency basis")
        
        natural_gas_agent = self.ins[0]
        self.ins[0].imass['CH4'] = mass_CH4
        natural_gas_agent.price = self.natural_gas_price  # Set natural gas price

        # Set emissions stream properties
        emissions = self.outs[0]
        emissions.T = self.T_emissions
        emissions.P = 101325
        emissions.phase = 'g'
        emissions.mol[:] = self.ins[0].mol
        chemicals = self.chemicals
        combustion_rxns = chemicals.get_combustion_reactions()
        combustion_rxns.force_reaction(emissions.mol)
        emissions.imol['O2'] = 0

        # Calculate energy used for steam
        deltah_sensible = self.Cp_H2O * (100 - self.water_temperature) # kJ/kg
        deltah_vap = 2256.4  # kJ/kg water at 100°C

        #H_sensible to heat from 25C to 100C and H_vap is for phase change
        h = deltah_sensible + deltah_vap # kJ/kg

        steam_flow = Q_to_digester/h # kg/h

        self.steam_flow = steam_flow /1000 #ton/hr

        water_input = bst.Stream('Boiler_water', T=298.15, P=101325)
        water_input = self.ins[1]
        steam = bst.Stream('Steam', phase='g')
        steam = self.outs[1]
        water_input.imol['7732-18-5'] = steam.imol['7732-18-5'] = steam_flow / 18.01528
        water_input.price = self.water_price
        steam.imol['7732-18-5'] = steam_flow / 18.01528
        steam.T = self.T_steam
        steam.P = 101325
        steam.phase = 'g'
        steam.price = 0

        Utility_cost = self.natural_gas_price * mass_CH4  # USD/hr
        Utility_cost_kW = Utility_cost / bst.settings.electricity_price  # Convert OPEX into Utility so BioSTEAM considers it in the design results
        self.power_utility(Utility_cost_kW)

        self.design_results['Flow rate'] = steam_flow # kg/hr
        self.design_results['Natural gas used'] = mass_CH4 #kg/h
        

    def _cost(self):
        baseline_costs = 10000 
        base_capacity = 0.5  
        Purchase_cost = baseline_costs * ((self.steam_flow / base_capacity) ** 0.6)*(CEPCI/CEPCI)

        self.baseline_purchase_costs['Boiler'] = Purchase_cost * (1 + dir_installation + dir_instrumentation + dir_piping + dir_electrical + dir_building_1 + dir_yard_improvement + indirect_factor)

    def _run(self):
        pass


class IsentropicCompressor(bst.Unit):

    _N_ins = 1
    _N_outs = 1

    _units = {'Methane inlet flow rate': 'Nm3/h',
              'RNG inlet flow rate': 'Nm3/h',
              'Initial pressure': 'Pa',
              'Outlet pressure': 'Pa',
              'Power': 'kW',
              'Power requirement': 'HP',}

    def __init__(self, ID='', ins=None, outs=(), P=None, eta=0.75, vle=False):
        super().__init__(ID, ins, outs)
        self.P = P or 1.379e6  # Default pressure in Pa 7 bar
        self.eta = eta
        self.vle = vle

    def _run(self):
        
        feed = self.ins[0]
        compressed_biogas = self.outs[0]
        
        compressed_biogas.copy_like(feed)
        compressed_biogas.P = self.P

    def _design(self):
        R = 8.3145 #J / mol K
        molar_mass_CH4 = 16.04 #g/mol
        molar_mass_CO2 = 44.01 #g/mol
        mass_CH4 = self.ins[0].imass['CH4']
        mass_CO2 = self.ins[0].imass['CO2']
        moles_CO2 = (mass_CO2*1000)/molar_mass_CO2 #moles/h
        moles_CH4 = (mass_CH4*1000)/molar_mass_CH4 #moles/h
        moles_total = moles_CH4 + moles_CO2 #moles/h
        self.ins[0].get_property('P', 'Pa')
        self.ins[0].get_property('T', 'K')
        P_normal = 101325 #Pa
        P_in = self.ins[0].P
        T_normal = 0+273.15 #K Assuming normal conditions for biogas to measure
        T_in = self.ins[0].T

        metric_flow = (moles_total * R * T_normal)/P_normal # Metric flow of RNG Nm3/h
        CH4_metric_flow_inlet = (moles_CH4 * R * T_normal)/P_normal #Nm3/hr

        self.design_results['Methane inlet flow rate'] = CH4_metric_flow_inlet
        self.design_results['RNG inlet flow rate'] = metric_flow
        self.design_results['Initial pressure'] = P_in
        self.design_results['Outlet pressure'] = self.P

        # Power requirement for the compressor

        k = 1.304 # Taking it as pure methane
        moles_total_s = moles_total/3600 # moles/s
        Work = (k/(k-1))*(moles_total_s * R * T_in) * (((self.P / P_in)**((k-1)/k))-1) #J/s or W
        Work_actual = (Work/self.eta)/1000 #Efficiency of 75%  in kW. x1 hour then in kWh

        self.Power = Work_actual * 1.341 # Convert from kW to HP

        self.design_results['Power'] = Work_actual #kWh
        self.design_results['Power requirement'] = self.Power
        self.power_utility(Work_actual)

    def _cost(self):
        baseline_costs = 9099
        base_capacity = 10 # HP horse power
        scaling_exponent = 0.6
        
        Purchase_cost = (baseline_costs*((self.Power/base_capacity)**scaling_exponent))*(CEPCI/CEPCI)

        self.baseline_purchase_costs['Compressor'] = Purchase_cost * (1 + dir_installation + dir_instrumentation + dir_piping + dir_electrical + dir_building_1 + dir_yard_improvement + indirect_factor)
                
