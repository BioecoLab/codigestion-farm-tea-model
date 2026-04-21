
'TEA'

import biosteam as bst

class AD_TEA(bst.TEA):
    def __init__(self,
                 system,
                 IRR,
                 duration,
                 depreciation,
                 income_tax,
                 operating_days,
                 construction_schedule,
                 WC_over_FCI,
                 investment_tax_credit,
                 upgrading_cost,
                 km_to_pipeline,
                 Grant_assistance,
                 Grant_percentage,):

        'COST FRACTIONS' #Added indvidually to each unit in Units_g.py
        #DIRECT COST FRACTIONS (all relative to purchased equipment cost)
        self.dir_installation      = 0.39
        self.dir_instrumentation   = 0.15
        self.dir_piping            = 0.15
        self.dir_electrical        = 0.10
        self.dir_building          = 0.156
        self.dir_yard_improvement  = 0.05
        self.dir_service_facility  = 0.00  # farm already has its own service facility
        

        self.direct_factor = 1 + sum([
            self.dir_installation,
            self.dir_instrumentation,
            self.dir_piping,
            self.dir_electrical,
            self.dir_building,
            self.dir_yard_improvement,
            self.dir_service_facility
        ]) #1.996 total

        #INDIRECT COST FRACTIONS (relative to purchased equipment cost)
        # note: we exclude working capital here because BioSTEAM handles that via WC_over_FCI
        self.indir_engineering      = 0.20
        self.indir_construction     = 0.30
        self.indir_legal            = 0.02
        self.indir_contractor_fees  = 0.15
        self.indir_contingency      = 0.15

        self.indirect_factor = sum([
            self.indir_engineering,
            self.indir_construction,
            self.indir_legal,
            self.indir_contractor_fees,
            self.indir_contingency
        ]) #0.82 total


        Labor_rate = 19.07 #USD/hr
        Labor_hours_per_day = 6 #hrs/day
        Labor_cost_farmer = Labor_rate * Labor_hours_per_day * 365 # The digester does not stop


        #OPEX‐related parameters for CHP plant
        if upgrading_cost:
            self.labor_cost          = Labor_cost_farmer
            self.property_tax        = 0.02 # 2% of FCI
            self.property_insurance  = 0.0035 # 1% of FCI
            self.supplies            = 500 # $500 per year
            self.maintenance         = 0.018 # 1% of FCI changed
            self.administration      = 0.0009 # 0.9% of FCI
        else:
            self.labor_cost          = Labor_cost_farmer 
            self.property_tax        = 0 # 2% of FCI
            self.property_insurance  = 0.0035 # 1% of FCI
            self.supplies            = 500 # $500 per year
            self.maintenance         = 0.018 # 2% of FCI 
            self.administration      = 0 # 0.9% of FCI

        #One‐time pipeline injection cost (added to DPI)
        Pipeline_material_and_labor     = 625000 #USD
        Pipeline_interconnection_fee    = 560000
        Engineering                     = 200000
        Online_gas_monitoring_equipment = 250000
        CPUC_Rebate                     = 0.5 #50% of total cost
        
        pipeline_interconnection = ((Pipeline_material_and_labor*km_to_pipeline)
                                        + Pipeline_interconnection_fee 
                                        + Engineering 
                                        + Online_gas_monitoring_equipment)#* (1-CPUC_Rebate)
        
        if upgrading_cost:
            self.pipeline_injection_cost = pipeline_interconnection
        else:
            self.pipeline_injection_cost = 0
        
        #Investment tax credit (added to incentives)
        self.investment_tax_credit = investment_tax_credit
        self.Grant_assistance = Grant_assistance
        self.Grant_percentage = Grant_percentage

        if Grant_assistance:
            self.direct_cost_multiplier = (1 - self.Grant_percentage)
        else:
            self.direct_cost_multiplier = 1

        super().__init__(
            system=system,
            IRR=IRR,
            duration=duration,
            depreciation=depreciation,
            income_tax=income_tax,
            operating_days=operating_days,
            construction_schedule=construction_schedule,
            lang_factor =1.0,
            # startup and financing all zero for Huang et al.
            startup_months=0,
            startup_FOCfrac=0,
            startup_VOCfrac=0,
            startup_salesfrac=0,
            finance_interest=0,
            finance_years=0,
            finance_fraction=0,
            WC_over_FCI=WC_over_FCI
        )


    def _DPI(self, installed_equipment_cost):
        """
        Direct Permanent Investment:
          = installed equipment cost (purchase × direct_factor)
          + pipeline injection cost
        """
        #Direct_cost = (installed_equipment_cost*self.direct_factor)
        Direct_cost = installed_equipment_cost

        return Direct_cost + self.pipeline_injection_cost

    def _TDC(self, DPI):
        """
        Total Depreciable Capital = DPI (Huang et al. assume equal)
        """
        return DPI

    def _FCI(self, TDC):
        """
        Fixed Capital Investment:
          = TDC + TIC 
        TIC = Total Indirect Cost
        """
        #TIC = self.installed_equipment_cost
        return (TDC)*self.direct_cost_multiplier

    def _FOC(self, FCI):
        """
        Fixed Operating Cost:
          property taxes, insurance, maintenance, administration
          plus labor × (1 + fringe + supplies)
        """
        return (
            FCI * (self.property_insurance
                   + self.maintenance
                   + self.administration)
            + self.labor_cost + self.supplies
        )


