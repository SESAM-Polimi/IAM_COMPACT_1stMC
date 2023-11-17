study_properties = {
    'Study 2': {
        'sat_accounts': [
            'CO2 - combustion - air', 
            'CH4 - combustion - air', 
            'N2O - combustion - air',
            ],

        'units': {
            'Satellite account': {
                'CO2 - combustion - air': {"raw": 'kg',"new": 'ton',"conv": 1/1000,}, 
                'CH4 - combustion - air': {"raw": 'kg',"new": 'ton',"conv": 1/1000,}, 
                'N2O - combustion - air': {"raw": 'kg',"new": 'ton',"conv": 1/1000,}, 
                'GHGs': {"raw": 'kg',"new": 'tonCO2eq',"conv": 1/1000,}, 
                },
            'Activity': {"Production of offshore wind plants": {"raw": 'EUR',"new": 'MW',"conv": 3.19e6,}, 
                "Production of onshore wind plants": {"raw": 'EUR',"new": 'MW',"conv": 1.44e6,}, 
                "Production of photovoltaic plants": {"raw": 'EUR',"new": 'MW',"conv": 1.81e6,}, 
                "Production of electricity by wind": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                "Production of electricity by solar photovoltaic": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                "Production of electricity by Geothermal": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                "Production of electricity by biomass and waste": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                "Production of electricity by coal": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                "Production of electricity by gas": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                "Production of electricity by hydro": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                "Production of electricity by nuclear": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                "Production of electricity by petroleum and other oil derivatives": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                # "Production of electricity by other RES": {"raw": 'EUR',"new": 'GWh',"conv": 'price',}, 
                },
            },

        'GWP': {
               "CO2 - combustion - air": 1,
               "CH4 - combustion - air": 29.8,
               "N2O - combustion - air": 273,
            },

        'regions_to': ['EU27+UK'],

        'activities_to': [
            'Production of photovoltaic plants',
            'Production of onshore wind plants',
            'Production of offshore wind plants',
            'Production of electricity by wind',
            'Production of electricity by solar photovoltaic'        
            ],
        
        'cf': {'PV': 0.16,'Onshore wind': 0.35,'Offshore wind': 0.4,}
                
        },
    }
    
