# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 09:04:17 2023

@author: loren
"""

import mario
import numpy as np

model = 'GCAM'

#%%
path = f'{model}\\flows'
world = mario.parse_from_txt(path, 'SUT', 'flows')

#%%
sectors_steel = world.search('Activity','steel')
sectors_steel.remove('Re-processing of secondary steel into new steel')
sectors_h2 = world.search('Activity','hydrogen')

commodities_steel = world.search('Commodity','steel')[0]
commodities_h2 = world.search('Commodity','hydrogen')

#%% check supply
sN = slice(None)
s_steel = world.s.loc[(sN,'Activity',sectors_steel),(sN,'Commodity',commodities_steel)]#.sum(0).to_frame().T

s_h2 = world.s.loc[(sN,'Activity',sectors_h2),(sN,'Commodity',commodities_h2)]#.sum(0).to_frame().T

#%%
u_steel = world.u.loc[:,('EU27','Activity',sectors_steel)]#.sum(0).to_frame().T

#%% check footprints
f_steel = world.f.loc['CO2',(sN,'Commodity',commodities_steel)].to_frame().T

f_steel = world.f.loc['CO2',(sN,'Activity',sectors_steel)].to_frame().T


f_steel_exp = np.diag(world.e.loc['CO2',:]) @ world.w
f_steel_exp.index = f_steel_exp.columns
f_steel_exp = f_steel_exp.loc[:,(sN,'Activity',sectors_steel)]

#%% shock to fix supply side of steel and h2
world.get_shock_excel(f'{model}\\shock_supply.xlsx')


#%%
