# -*- coding: utf-8 -*-
"""
Created on Fri Mar 17 13:29:33 2023

@author: 
    Lorenzo Rinaldi, Department of Energy, Politecnico di Milano
    Nicolò Golinucci, Department of Energy, Politecnico di Milano
"""

import pandas as pd
import mario
from openpyxl import load_workbook
from copy import deepcopy as dc
import math
import numpy as np
import os

from Models_Link import (
    mapping_shocks,
    )

mat_map =  {
    "s": {
        'sheet': "z",
        'row_level': "Activity",
        'col_level': "Commodity",
        },
    "u": {
        'sheet': "z",
        'row_level': "Commodity",
        'col_level': "Activity",
        },
    "Y": {
        'sheet': "Y",
        'row_level': "Commodity",
        }
    }

#%%
def sceMARIOs_definition(
        model_sets,
        method,
        ):
    
    model_sets['SceMARIOs'] = []
    for m1 in model_sets[method[0]]:
        for m2 in model_sets[method[1]]:
            model_sets['SceMARIOs'] += [f"{m1} - {m2}"] 
    
    return model_sets
        
#%%
def var_to_function_assignment(
        shock_map,
        models_results,
        models_sets,
        mario_db,
        paths,
        user,
        model,
        sceMARIOs_method = ("Scenarios","Years"),
        ):
    
    shock_map.reset_index(inplace=True)
    shock_map.set_index(['Variables', 'Function', 'Functions clustering'], inplace=True)
    
    for m in models_sets.keys():
        models_sets[m] = sceMARIOs_definition(models_sets[m], sceMARIOs_method)
    
    functions = list(set(shock_map.index.get_level_values('Function')))
    
    shock_inputs = {}
    for function in functions:
        try:
            vars_selection = shock_map.loc[(slice(None), function),:]
            exec(f"shock_inputs['{function}'] = {function}(vars_selection, models_results, models_sets, sceMARIOs_method, mario_db, paths, user, model)")
            print(f"Information about '{function}' shocks collected")
        except:
            print(f"{function} not passed")
            pass
    return shock_inputs

#%%
def electricity_consumption_mix_update(
        shock_map,
        models_results,        
        models_sets,
        sceMARIOs_method,
        mario_db,
        paths,
        user,
        model,
        ):

    
    variables = list(shock_map.index.get_level_values(0))
    commodities = list(set(shock_map['Commodity'])) 
    var_com_map = {var:com for (var,com) in zip(variables,shock_map['Commodity'])}
    matrix = list(set(shock_map['Matrix']))[0] 

    model_result = dc(models_results[model])
    results_ind_names = list(model_result.index.names)
    model_result.reset_index(inplace=True)
    model_result = model_result.query("Variable==@variables")
    
    model_result['Variable'] = model_result['Variable'].map(var_com_map)  
    model_result.set_index(results_ind_names, inplace=True)

    ee_total_prod = model_result.groupby(['Model','Scenario','Region','Unit']).sum()
    
    sN = slice(None)
    for scenario in list(set(model_result.index.get_level_values('Scenario'))):
        for region in list(set(model_result.index.get_level_values('Region'))):
            model_result.loc[(sN,scenario,region,sN,sN),:] /= ee_total_prod.loc[(sN,scenario,region,sN),:].values

    model_result = model_result.groupby(results_ind_names).sum()

    
    shock_input = {}

    for cluster in set(shock_map.index.get_level_values("Functions clustering")):
        var_cluster = shock_map.loc[(slice(None), slice(None), cluster),:] 
        shock_input[cluster] = {}

        if sceMARIOs_method == ("Scenarios","Years"):
                
            for var in set(var_cluster.index.get_level_values('Variables')):
                shock_input[cluster][var] = {}
                
                for region in models_sets[model]['Regions']:
                    shock_input[cluster][var][region] = {}
                    
                    if matrix == 'u':
                        try:
                            sut_slice = mario_db.u.loc[(region,'Commodity',commodities),:]
                        except:
                            sut_slice = mario_db.u.loc[(region,'Commodity',commodities),:].to_frame()
                    elif matrix == 'Y':                        
                        try:
                            sut_slice = mario_db.Y.loc[(region,'Commodity',commodities),:]
                        except:
                            sut_slice = mario_db.Y.loc[(region,'Commodity',commodities),:].to_frame()
                    
                    for scemario in models_sets[model]['SceMARIOs']:
                        scenario = scemario.split(' - ')[0]
                        year = scemario.split(' - ')[1]
                        ee_mix = model_result.loc[(sN,scenario,'EU27',sN,sN),year].to_frame().values
                        
                        res_df = pd.DataFrame()
                        for commodity in commodities:
                            res_df = pd.concat([res_df,dc(sut_slice).sum(0).to_frame().T],axis=0)
                        res_df.index = sut_slice.index
                        
                        shock_input[cluster][var][region][scemario] = res_df* ee_mix

    return shock_input
    

#%%
def final_demand_percentage(
        shock_map,
        models_results,        
        models_sets,
        sceMARIOs_method,
        mario_db,
        paths,
        user,
        model,
        ):
    
    shock_input = {}
    
    for cluster in set(shock_map.index.get_level_values("Functions clustering")):
        var_cluster = shock_map.loc[(slice(None), slice(None), cluster),:] 
        shock_input[cluster] = {}
        
        if list(set([shock_map.loc[var_cluster.index[i],'Method'] for i in range(shock_map.shape[0])]))[0] == 'Yearly growth rate':

            if sceMARIOs_method == ("Scenarios","Years"):
                    
                for var in set(var_cluster.index.get_level_values('Variables')):
                    shock_input[cluster][var] = {}
                    
                    for region in models_sets[model]['Regions']:
                        shock_input[cluster][var][region] = pd.DataFrame()  
                        
                        for scemario in models_sets[model]['SceMARIOs']:
                            try:
                                g_rate = models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), int(scemario.split(' - ')[1])] /  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), 2010]
                            except:
                                g_rate =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), str(scemario.split(' - ')[1])] /  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), str(2010)]
                            g_rate = g_rate.values[0]
                            shock_input[cluster][var][region] = pd.concat([
                                shock_input[cluster][var][region], 
                                pd.DataFrame(g_rate, index=[scemario.split(' - ')[0]], columns=[scemario.split(' - ')[1]]),
                                ], axis=1
                                )
                        
                        shock_input[cluster][var][region] = shock_input[cluster][var][region].fillna(0)
                        shock_input[cluster][var][region] = shock_input[cluster][var][region].groupby(level=[0], axis=1, sort=True).sum()
    
    return shock_input
                                        
#%%                                        
def final_demand_update(
        shock_map,
        models_results,        
        models_sets,
        sceMARIOs_method,
        mario_db,
        paths,
        user,
        model,
        ):

    shock_input = {}
    
    for cluster in set(shock_map.index.get_level_values("Functions clustering")):
        var_cluster = shock_map.loc[(slice(None), slice(None), cluster),:] 
        shock_input[cluster] = {}
        
        if sceMARIOs_method == ("Scenarios","Years"):
                
            for var in set(var_cluster.index.get_level_values('Variables')):
                shock_input[cluster][var] = {}
                
                for region in models_sets[model]['Regions']:
                    shock_input[cluster][var][region] = pd.DataFrame()  
                    
                    for scemario in models_sets[model]['SceMARIOs']:
                        try:
                            Y_update =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), int(scemario.split(' - ')[1])]
                        except:
                            Y_update =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), str(scemario.split(' - ')[1])]

                        Y_update = Y_update.values[0] * var_cluster.loc[(var,slice(None),cluster),"Unit conversion factors"].values[0]
                        shock_input[cluster][var][region] = pd.concat([
                            shock_input[cluster][var][region], 
                            pd.DataFrame(Y_update, index=[scemario.split(' - ')[0]], columns=[scemario.split(' - ')[1]]),
                            ], axis=1
                            )
                        
                    shock_input[cluster][var][region] = shock_input[cluster][var][region].fillna(0)
                    shock_input[cluster][var][region] = shock_input[cluster][var][region].groupby(level=[0], axis=1, sort=True).sum()
            
    return shock_input
            
#%%
def domestic_electricity_mix_update(
        shock_map,
        models_results,        
        models_sets,
        sceMARIOs_method,
        mario_db,
        paths,
        user,
        model,
        ):

    shock_input = {}
    
    sN = slice(None)
    
    for cluster in set(shock_map.index.get_level_values("Functions clustering")):
        var_cluster = shock_map.loc[(slice(None), slice(None), cluster),:] 
        shock_input[cluster] = {}
        
        if sceMARIOs_method == ("Scenarios","Years"):
            
            variables = list(set(var_cluster.index.get_level_values('Variables')))
            for var in variables:
                shock_input[cluster][var] = {}
                
                for region in models_sets[model]['Regions']:
                    shock_input[cluster][var][region] = pd.DataFrame()  
                    
                    other_regions = mario_db.get_index('Region')
                    other_regions.remove(region)
                    
                    for scemario in models_sets[model]['SceMARIOs']: 
                        try:
                            s_update =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, variables, slice(None)), int(scemario.split(' - ')[1])]
                        except:
                            s_update =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, variables, slice(None)), str(scemario.split(' - ')[1])]
                        s_update /= s_update.sum()
                        imported_ee = mario_db.s.loc[(other_regions,slice(None),slice(None)), (region,slice(None), var_cluster.loc[(var, slice(None), slice(None)),"Commodity"].values[0])].sum().values[0]
                        try:
                            s_update = s_update.loc[(slice(None), slice(None), slice(None), var, slice(None))].values[0]*(1-imported_ee)
                        except:
                            pass
                        
                        shock_input[cluster][var][region] = pd.concat([
                            shock_input[cluster][var][region], 
                            pd.DataFrame(s_update, index=[scemario.split(' - ')[0]], columns=[scemario.split(' - ')[1]]),
                            ], axis=1
                            )
                        
                    shock_input[cluster][var][region] = shock_input[cluster][var][region].fillna(0)
                    shock_input[cluster][var][region] = shock_input[cluster][var][region].groupby(level=[0], axis=1, sort=True).sum()
            
    return shock_input

#%%
def gas_imports(
        shock_map,
        models_results,        
        models_sets,
        sceMARIOs_method,
        mario_db,
        paths,
        user,
        model,
        ):
    
    shock_input = {}
    
    for cluster in set(shock_map.index.get_level_values("Functions clustering")):
        var_cluster = shock_map.loc[(slice(None), slice(None), cluster),:] 
        shock_input[cluster] = {}
        
        if sceMARIOs_method == ("Scenarios","Years"):
                
            for var in set(var_cluster.index.get_level_values('Variables')):
                shock_input[cluster][var] = {}
                
                region = 'EU27+UK'  ##############
                shock_input[cluster][var][region] = pd.DataFrame()  
                    
                for scemario in models_sets[model]['SceMARIOs']:  
                    if model == 'GCAM':
                        try:
                            DomGas =  models_results[model].loc[(slice(None), scemario.split(' - ')[0], region, 'Primary Energy|Gas', slice(None)), int(scemario.split(' - ')[1])].values[0]
                            NetImpGas =  models_results[model].loc[(slice(None), scemario.split(' - ')[0], region, var, slice(None)), int(scemario.split(' - ')[1])].values[0]
                        except:
                            DomGas =  models_results[model].loc[(slice(None), scemario.split(' - ')[0], region, 'Primary Energy|Gas', slice(None)), str(scemario.split(' - ')[1])].values[0]
                            NetImpGas =  models_results[model].loc[(slice(None), scemario.split(' - ')[0], region, var, slice(None)), str(scemario.split(' - ')[1])].values[0]
                    else:
                        if scemario.split(' - ')[0] ==  'NDC_NoRus_Eff':
                            scen = 'NDC_noRusGas_Eff'
                        elif scemario.split(' - ')[0] ==  'NDC_NoRus':
                            scen = 'NDC_noRusGas'
                        elif scemario.split(' - ')[0] ==  'NDC_NoRus_Dom':
                            scen = 'NDC_noRusGas_Dom'
                        elif scemario.split(' - ')[0] ==  'NDC_Default':
                            scen = 'NDC_Default'
                        elif scemario.split(' - ')[0] ==  'NDC_NoRus_Imp':
                            scen = 'NDC_noRusGas_Imp'
                        else:
                            scen = 'CP_Default'
                            
                        DomGas =  models_results['GCAM'].loc[(slice(None), scen, region, 'Primary Energy|Gas', slice(None)), int(scemario.split(' - ')[1])].values[0]
                        NetImpGas =  models_results['GCAM'].loc[(slice(None), scen, region, var, slice(None)), int(scemario.split(' - ')[1])].values[0]
                        
                    if NetImpGas >=0:
                        if DomGas >= 0:
                            s_update = NetImpGas/(DomGas+NetImpGas)
                        else:
                            s_update = 1
                    else:
                        s_update = 0
                        
                    shock_input[cluster][var][region] = pd.concat([
                        shock_input[cluster][var][region], 
                        pd.DataFrame(s_update, index=[scemario.split(' - ')[0]], columns=[scemario.split(' - ')[1]]),
                        ], axis=1
                        )
                           
                shock_input[cluster][var][region] = shock_input[cluster][var][region].fillna(0)
                shock_input[cluster][var][region] = shock_input[cluster][var][region].groupby(level=[0], axis=1, sort=True).sum()
    
    return shock_input


#%%                                        
def hh_emissions(
        shock_map,
        models_results,        
        models_sets,
        sceMARIOs_method,
        mario_db,
        paths,
        user,
        model,
        ):

    shock_input = {}
    
    for cluster in set(shock_map.index.get_level_values("Functions clustering")):
        var_cluster = shock_map.loc[(slice(None), slice(None), cluster),:] 
        shock_input[cluster] = {}
        
        if sceMARIOs_method == ("Scenarios","Years"):
                
            for var in set(var_cluster.index.get_level_values('Variables')):
                shock_input[cluster][var] = {}
                
                for region in models_sets[model]['Regions']:
                    shock_input[cluster][var][region] = pd.DataFrame()  
                    
                    for scemario in models_sets[model]['SceMARIOs']:
                        try:
                            EY_update =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), int(scemario.split(' - ')[1])].values[0]
                        except:
                            EY_update =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), str(scemario.split(' - ')[1])].values[0]

                        shock_input[cluster][var][region] = pd.concat([
                            shock_input[cluster][var][region], 
                            pd.DataFrame(EY_update, index=[scemario.split(' - ')[0]], columns=[scemario.split(' - ')[1]]),
                            ], axis=1
                            )
                        
                    shock_input[cluster][var][region] = shock_input[cluster][var][region].fillna(0)
                    shock_input[cluster][var][region] = shock_input[cluster][var][region].groupby(level=[0], axis=1, sort=True).sum()
            
    return shock_input


#%%                                        
def industry_electrification(
        shock_map,
        models_results,        
        models_sets,
        sceMARIOs_method,
        mario_db,
        paths,
        user,
        model,
        ):

    shock_input = {}
    
    for cluster in set(shock_map.index.get_level_values("Functions clustering")):
        var_cluster = shock_map.loc[(slice(None), slice(None), cluster),:] 
        shock_input[cluster] = {}
        
        if sceMARIOs_method == ("Scenarios","Years"):
            
            variables =  list(set(var_cluster.index.get_level_values('Variables')))
            var = 'Final Energy|Industry|Electricity'
            shock_input[cluster][var] = {}
            
            for region in models_sets[model]['Regions']:
                shock_input[cluster][var][region] = {}
                
                for scemario in models_sets[model]['SceMARIOs']:
                    print(scemario)
                    shock_input[cluster][var][region][scemario] = {}

                    industries = get_shock_clusters(mapping_shocks(model,paths,user),mario_db)['Activity']['Industries']
                    encomms = [get_shock_clusters(mapping_shocks(model,paths,user),mario_db)['Commodity']['Final Energy|Industry|Gases'] + get_shock_clusters(mapping_shocks(model,paths,user),mario_db)['Commodity']['Final Energy|Industry|Liquids'] + get_shock_clusters(mapping_shocks(model,paths,user),mario_db)['Commodity']['Final Energy|Industry|Solids']][0]
                    encomms += shock_map.loc[:,"Commodity"].values.tolist()
                    encomms_only = dc(encomms)
                    for v in variables:
                        if v in encomms_only:
                            encomms_only.remove(v)    
                    LHV = list(set(shock_map.loc[:,'Unit conversion factors'].values.tolist()))[0]
                    lhvs = pd.read_excel(f"{pd.read_excel(paths, index_col=[0]).loc[LHV,user]}", index_col=[0,1,2])
                    lhvs.sort_index(level=0, inplace=True)    
                    try:
                        fuel_cons =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), int(scemario.split(' - ')[1])].sum().sum()
                        fuel_tot_cons =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, variables, slice(None)), int(scemario.split(' - ')[1])].sum().sum()
                    except:
                        fuel_cons =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, var, slice(None)), str(scemario.split(' - ')[1])].sum().sum()
                        fuel_tot_cons =  models_results[model].loc[(slice(None),scemario.split(' - ')[0], region, variables, slice(None)), str(scemario.split(' - ')[1])].sum().sum()

                    fuel_cons_share = fuel_cons/fuel_tot_cons
                    
                    uen_units = mario_db.u.loc[(region,slice(None),encomms), (region,slice(None),industries)]
                    uen_units.sort_index(level=2, inplace=True)
                    lhvs_filtered = lhvs.loc[(uen_units.index.get_level_values(-1),slice(None),slice(None)),:]

                    uen_TJ = uen_units * lhvs_filtered.values
                                      
                    uen_shares = uen_TJ / uen_TJ.sum(0)
                    
                    non_ee_vars = dc(encomms_only)
                    non_ee_vars.remove(shock_map.loc[(var,slice(None),slice(None)),'Commodity'].values[0])
                    
                    uen_shock = dc(uen_shares)
                    for i in uen_shares.columns:
                        starting_ee_rate = uen_shares.loc[(slice(None),slice(None),shock_map.loc[(var,slice(None),slice(None)),'Commodity']),i].values[0]
                        if starting_ee_rate != 0 and starting_ee_rate < fuel_cons_share:                                                     
                            uen_shock.loc[(slice(None),slice(None),shock_map.loc[(var,slice(None),slice(None)),'Commodity']),i] = fuel_cons_share
                            uen_shock.loc[(slice(None),slice(None),non_ee_vars),i] *= (1-(fuel_cons_share-starting_ee_rate))
                    
                    uen_shares_new = uen_shock / uen_shock.sum(0)                    
                    uen_TJ_new = uen_TJ.sum(0)*uen_shares_new
                    uen_units_new = uen_TJ_new / lhvs_filtered.values
                      
                    for i in industries:
                        shock_input[cluster][var][region][scemario][i] = {}
                        for c in encomms_only:
                            shock_input[cluster][var][region][scemario][i][c] = uen_units_new.loc[(region,slice(None),c),(region,slice(None),i)].values[0,0]
                    
    return shock_input
            
                           
#%%
def get_shock_templates(
        paths_file,
        mario_db,
        user,
        model,
        study,
        sceMARIOs_method = ("Scenarios","Years"),
        ):
    
    mario_db.get_shock_excel(os.getcwd()+f"\\{study}\\Shocks\\_template_{model}.xlsx")
    
#%%
def fill_shock_templates(
        paths_file,
        model_sets,
        SI,
        model,
        mapping_info,
        user,
        study,
        worlds,
        sceMARIOs_method = ("Scenarios","Years"),
        ):
    
    for scemario in model_sets['SceMARIOs']:
        print(scemario)
        scenario = scemario.split(' - ')[0]
        year = scemario.split(' - ')[1]
        
        workbook = load_workbook(os.getcwd()+f"\\{study}\\Shocks\\_template_{model}.xlsx")
        
        row_1 = 0
        row_2 = 0
        importing_regions = []
        imported_gas = 0

        if 'gas_imports' in mapping_info['shock_map'].index.get_level_values(1):
            workbook['z']['A'+str(row_1+2)] = 'all'
            workbook['z']['B'+str(row_1+2)] = 'Activity'
            workbook['z']['C'+str(row_1+2)] = 'all'
            workbook['z']['D'+str(row_1+2)] = 'EU27+UK'
            workbook['z']['E'+str(row_1+2)] = 'Commodity'
            workbook['z']['F'+str(row_1+2)] = 'Natural gas'
            workbook['z']['G'+str(row_1+2)] = 'Update'
            workbook['z']['H'+str(row_1+2)] = 0
            row_1 += 1
            
        for shock in mapping_info['shock_map'].index:
            if mapping_info['shock_map'].loc[shock, "Matrix"] != "EY":
                sheet = mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['sheet']
                row_level = mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['row_level']
                shock_type = mapping_info['shock_map'].loc[shock, "Type"]
            
            try:
                for region, values in SI[shock[1]][shock[2]][shock[0]].items():
                            
                    if shock[1] == 'domestic_electricity_mix_update':
                        workbook[sheet]['A'+str(row_1+2)] = region
                        workbook[sheet]['B'+str(row_1+2)] = row_level
                        workbook[sheet]['C'+str(row_1+2)] = mapping_info['shock_map'].loc[shock,row_level]
                        workbook[sheet]['D'+str(row_1+2)] = region
                        workbook[sheet]['E'+str(row_1+2)] = mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['col_level']
                        workbook[sheet]['F'+str(row_1+2)] = mapping_info['shock_map'].loc[shock,mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['col_level']]
                        workbook[sheet]['G'+str(row_1+2)] = shock_type
                        
                        if mapping_info['shock_map'].loc[:,"Activity"].dropna().to_list().count(mapping_info['shock_map'].loc[shock,"Activity"]) != 1:
                            cluster = mapping_info['shock_map'].loc[mapping_info['shock_map']['Activity']==mapping_info['shock_map'].loc[shock,"Activity"],:]    
                            value = 0
                            for i in cluster.index.get_level_values(0):
                                value += SI[shock[1]][shock[2]][i][region].loc[scenario,year]
                        else:
                            value = values.loc[scenario,year]
                        
                        workbook[sheet]['H'+str(row_1+2)] = value
                        row_1 += 1
                    
                    elif shock[1] == 'electricity_consumption_mix_update':
                        for (activity,region_to) in zip(values[scemario].columns.get_level_values(2),values[scemario].columns.get_level_values(0)):                        
                            workbook[sheet]['A'+str(row_1+2)] = region
                            workbook[sheet]['B'+str(row_1+2)] = row_level
                            workbook[sheet]['C'+str(row_1+2)] = mapping_info['shock_map'].loc[shock,row_level]
                            workbook[sheet]['D'+str(row_1+2)] = region_to
                            workbook[sheet]['E'+str(row_1+2)] = mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['col_level']
                            workbook[sheet]['F'+str(row_1+2)] = activity
                            workbook[sheet]['G'+str(row_1+2)] = shock_type
                            workbook[sheet]['H'+str(row_1+2)] = values[scemario].loc[(region,row_level,mapping_info['shock_map'].loc[shock,row_level]),(region_to,mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['col_level'],activity)]
                            row_1 += 1
                    
                    elif shock[1] == 'final_demand_percentage':
                        workbook[sheet]['A'+str(row_2+2)] = 'all'
                        workbook[sheet]['B'+str(row_2+2)] = row_level
                        workbook[sheet]['C'+str(row_2+2)] = mapping_info['shock_map'].loc[shock,row_level]
                        workbook[sheet]['D'+str(row_2+2)] = region
                        workbook[sheet]['E'+str(row_2+2)] = mapping_info['shock_map'].loc[shock,'Consumption category']
                        workbook[sheet]['F'+str(row_2+2)] = shock_type
                        workbook[sheet]['G'+str(row_2+2)] = values.loc[scenario, year]
                        row_2 += 1
                        
                    elif shock[1] == 'final_demand_update':
                        workbook[sheet]['A'+str(row_2+2)] = region
                        workbook[sheet]['B'+str(row_2+2)] = row_level
                        workbook[sheet]['C'+str(row_2+2)] = mapping_info['shock_map'].loc[shock,row_level]
                        workbook[sheet]['D'+str(row_2+2)] = region
                        workbook[sheet]['E'+str(row_2+2)] = mapping_info['shock_map'].loc[shock,'Consumption category']
                        workbook[sheet]['F'+str(row_2+2)] = shock_type
                        workbook[sheet]['G'+str(row_2+2)] = values.loc[scenario, year]
                        row_2 += 1
                        
                    elif shock[1] == 'gas_imports':
                        if shock[0] == "traded Afr_MidE pipeline gas":
                            workbook[sheet]['A'+str(row_1+2)] = 'RoW'
                            importing_regions += ['RoW']
                        if shock[0] == 'traded LNG':
                            workbook[sheet]['A'+str(row_1+2)] = 'USA'
                            importing_regions += ['USA']
                        if shock[0] == 'traded RUS pipeline gas':
                            workbook[sheet]['A'+str(row_1+2)] = 'Russia'
                            importing_regions += ['Russia']
                                                
                        workbook[sheet]['B'+str(row_1+2)] = row_level
                        workbook[sheet]['C'+str(row_1+2)] = mapping_info['shock_map'].loc[shock,row_level]
                        workbook[sheet]['D'+str(row_1+2)] = region
                        workbook[sheet]['E'+str(row_1+2)] = mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['col_level']
                        workbook[sheet]['F'+str(row_1+2)] = mapping_info['shock_map'].loc[shock,mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['col_level']]
                        workbook[sheet]['G'+str(row_1+2)] = shock_type
                        workbook[sheet]['H'+str(row_1+2)] = values.loc[scenario,year]
                        imported_gas += values.loc[scenario,year]
                        row_1 += 1

                    if shock[1] == 'industry_electrification':
                        if shock[0] == 'Final Energy|Industry|Electricity':
                            for ind,comms in values[scemario].items():
                                for comm,coeff in comms.items():
                                    workbook[sheet]['A'+str(row_1+2)] = region
                                    workbook[sheet]['B'+str(row_1+2)] = row_level
                                    workbook[sheet]['C'+str(row_1+2)] = comm
                                    workbook[sheet]['D'+str(row_1+2)] = region
                                    workbook[sheet]['E'+str(row_1+2)] = mat_map[mapping_info['shock_map'].loc[shock, "Matrix"]]['col_level']
                                    workbook[sheet]['F'+str(row_1+2)] = ind
                                    workbook[sheet]['G'+str(row_1+2)] = shock_type
                                    workbook[sheet]['H'+str(row_1+2)] = coeff
                                    row_1 += 1

            except:
                pass
    
    
            if 'gas_imports' in mapping_info['shock_map'].index.get_level_values(1):
                if model == 'GCAM':
                    other_regions = worlds[model].get_index('Region')
                else:
                    other_regions = worlds['GCAM'].get_index('Region')
                for r in importing_regions:
                    other_regions.remove(r)  
                for r in other_regions:
                    if r!='EU27+UK':
                        workbook['z']['A'+str(row_1+2)] = r
                        workbook['z']['B'+str(row_1+2)] = 'Activity'
                        workbook['z']['C'+str(row_1+2)] = 'Natural gas extraction'
                        workbook['z']['D'+str(row_1+2)] = 'EU27+UK'
                        workbook['z']['E'+str(row_1+2)] = 'Commodity'
                        workbook['z']['F'+str(row_1+2)] = 'Natural gas'
                        workbook['z']['G'+str(row_1+2)] = 'Update'
                        workbook['z']['H'+str(row_1+2)] = 0
                    else:
                        workbook['z']['A'+str(row_1+2)] = r
                        workbook['z']['B'+str(row_1+2)] = 'Activity'
                        workbook['z']['C'+str(row_1+2)] = 'Natural gas extraction'
                        workbook['z']['D'+str(row_1+2)] = 'EU27+UK'
                        workbook['z']['E'+str(row_1+2)] = 'Commodity'
                        workbook['z']['F'+str(row_1+2)] = 'Natural gas'
                        workbook['z']['G'+str(row_1+2)] = 'Update' 
                        workbook['z']['H'+str(row_1+2)] = 1- imported_gas
                    row_1 += 1
                    
        workbook.save(os.getcwd()+f"\\{study}\\Shocks\\{model}\\{scemario}.xlsx")


#%%
def EY_update(
    model_sets,
    shock_inputs,
    mapping_info,
    mario_db,
    ):

    HH_emissions = {}
    for var,dicts in shock_inputs['hh_emissions']['HH emissions'].items():
        for region in dicts.keys():
            HH_emissions[region] = dc(dicts[region])*0

    for var,dicts in shock_inputs['hh_emissions']['HH emissions'].items():            
        for region,values in dicts.items():
            HH_emissions[region] += values
    
    HH_emissions_change = dc(HH_emissions)
    for region, emissions in HH_emissions.items():
        HH_emissions_change[region] = emissions / emissions.loc[:,emissions.columns[1]].to_frame().values
            
    for scemario in model_sets['SceMARIOs']:
        
        scenario = scemario.split(' - ')[0]
        year = scemario.split(' - ')[1]
        
        for region in HH_emissions_change.keys():
            
            sa = mapping_info['shock_map'].loc[(slice(None),slice(None),'HH emissions'),'Satellite account'].to_list()[0] 
            cc = mapping_info['shock_map'].loc[(slice(None),slice(None),'HH emissions'),'Consumption category'].to_list()[0]
            mario_db.matrices[scemario]['EY'].loc[sa, (region,slice(None),cc)] *= HH_emissions_change[region].loc[scenario,year]
             
          
#%%
def get_shock_clusters(
        mapping_info,
        mario_db
        ):

    clusters = {}
    
    for item in ['Commodity','Activity']:
        clusters[item] = {}
        
        elements = list(set(mapping_info['shock_map'].loc[:,item].to_list()))
        for e in list(set(elements) & set(mario_db.get_index(item))):
            elements.remove(e)
        
        if elements == []:
            pass
        else:
            for e in elements:
                for cluster in mapping_info[item].columns:
                    if e in mapping_info[item][cluster].to_list():
                        clusters[item][e] = list(mapping_info[item][cluster].dropna().index)
    
        for check_nan in clusters[item].keys():
            if clusters[item][check_nan] == []:
                clusters.pop(item)
                break
    
    if 'Commodity' not in clusters.keys():
        clusters['Commodity'] = {}
    if 'Activity' not in clusters.keys():
        clusters['Activity'] = {}
    if 'Region' not in clusters.keys():
        clusters['Region'] = {}
    if 'Consumption category' not in clusters.keys():
        clusters['Consumption category'] = {}
    if 'Factor of production' not in clusters.keys():
        clusters['Factor of production'] = {}
    
    clusters['Commodity']['all'] = mario_db.get_index('Commodity') 
    clusters['Activity']['all'] = mario_db.get_index('Activity') 
    clusters['Region']['all'] = mario_db.get_index('Region') 
    clusters['Consumption category']['all'] = mario_db.get_index('Consumption category') 
    clusters['Factor of production']['all'] = mario_db.get_index('Factor of production') 
            
    return clusters
           
        
#%%
# shock_map = mapping_info[model]['shock_map']
# model_results = models_results[model]
# model_sets = models_sets[model]
# mario_db = worlds[model]
# sceMARIOs_method = ("Scenarios","Years"),

# #%%  
# function = 'gas_imports'

# #%%
# shock_map = vars_selection

         
    
    
