# -*- coding: utf-8 -*-
"""
Created on Tue Dec 12 21:33:20 2023

@author: loren
"""

import mario

path = 'greentechs - domestic'
mode = 'coefficients'

world = mario.parse_from_txt(f"{path}\\database\\baseline\\{mode}", "SUT", mode)

#%%
# world.get_aggregation_excel(f"{path}\\aggregation.xlsx")
world.aggregate(f"{path}\\aggregation.xlsx",ignore_nan=True)

#%%
path_commodities = f"{path}\\add_sectors\\add_commodities.xlsx"
new_comms = [
    "NCA batteries",
    "NMC batteries",
    "LFP batteries",
    'Photovoltaic plants',
    'Onshore wind plants',
    'Offshore wind plants',
    'Neodymium',
    'Dysprosium',
    'Raw silicon'
    ]

path_activities = f"{path}\\add_sectors\\add_activities.xlsx"
new_acts = [
    "Manufacture of NCA batteries",
    "Manufacture of NMC batteries",
    "Manufacture of LFP batteries",
    'Production of photovoltaic plants',
    'Production of onshore wind plants',
    'Production of offshore wind plants'
    ]

# world.get_add_sectors_excel(path=path_commodities, new_sectors=new_comms, regions= ['EU27'], item= 'Commodity')
# world.get_add_sectors_excel(path=path_activities, new_sectors=new_acts, regions= ['EU27'], item= 'Activity')

#%%
world.add_sectors(io=path_commodities, new_sectors=new_comms, regions= ['EU27'], item= 'Commodity', inplace=True)
world.add_sectors(io=path_activities,  new_sectors=new_acts,  regions= ['EU27'], item= 'Activity',  inplace=True)

#%%
world.shock_calc(f"{path}\\Shock_add_CRMs.xlsx",z=True,Y=True,scenario='crms')
#%%
world.to_txt(f"{path}\\database\\crms",flows=False,coefficients=True,scenario='crms')

world = mario.parse_from_txt(f"{path}\\database\\crms\\{mode}", 'SUT', mode)
world.shock_calc(f"{path}\\baseline.xlsx",z=True,Y=True,scenario='fix')

world.to_txt(r"C:\Users\loren\Documents\GitHub\SESAM\IAM_COMPACT_1stMC\Study 3\Baseline SUT\GCAM",flows=True,scenario='fix')
