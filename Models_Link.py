# -*- coding: utf-8 -*-
"""
Created on Tue Feb 20 10:15:51 2023

@author: 
    Lorenzo Rinaldi, Department of Energy, Politecnico di Milano
    Nicolò Golinucci, Department of Energy, Politecnico di Milano
"""

import pandas as pd
from copy import deepcopy as dc
import os

def main_models_results(
        paths_file, 
        user, 
        models, 
        sets_selection, 
        study,
        load_sets=True, 
        save_sets=False):

    """parsing models results""" 
    model_results = {}
    for model in models:
        model_results[model] = pd.read_excel(os.getcwd()+f"\\_from other models\\{model}\\{study}.xlsx")
        try:
            model_results[model].set_index(["Model","Scenario","Region","Variable","Unit"], inplace=True)
        except:
            model_results[model].set_index(["model","scenario","region","Variable","Unit"], inplace=True)        
        model_results[model].index.names = ["Model", "Scenario", "Region", "Variable", "Unit"]

    """defining sets and filtering results"""
    sets = {}
    for model in models:
        sets[model] = {
            "Scenarios": list(set(model_results[model].index.get_level_values('Scenario'))),
            "Regions": list(set(model_results[model].index.get_level_values('Region'))),
            "Variables": list(set(model_results[model].index.get_level_values('Variable'))),
            "Years": list(model_results[model].columns)
            }
    
    """Saving sets for each model"""
    sets_directory = os.getcwd()+f"\\{study}\\Models_link\\Sets"
    
    if save_sets:
        for s in sets[model].keys():
            writer = pd.ExcelWriter(f"{sets_directory}\{s}.xlsx", engine='openpyxl')
            for model in models:
                set_df = pd.DataFrame(index=sets[model][s])
                set_df.to_excel(writer, sheet_name=model)
            writer.close()

    """Parsing model results according to sets selection"""
    sets_sel = {}
    
    if load_sets:
        for model in models:
            sets_sel[model] = {}
           
            sets_sel[model]["Scenarios"] = pd.read_excel(f"{sets_directory}\Scenarios.xlsx", sheet_name=model, index_col=[0]).loc[:, sets_selection["Scenarios"][model]].to_frame()  
            sets_sel[model]["Scenarios"] = sets_sel[model]["Scenarios"][sets_sel[model]["Scenarios"][sets_selection["Scenarios"][model]].str.contains("unused") != True]
            sets_sel[model]["Scenarios"].index.names = ['Raw']
            sets_sel[model]["Scenarios"].reset_index(inplace=True)
            sets_sel[model]["Scenarios"].set_index(list(sets_sel[model]["Scenarios"].columns), inplace=True)
            sets_sel[model]["Scenarios"] = list(set(sets_sel[model]["Scenarios"].index))
            
            sets_sel[model]["Regions"] = pd.read_excel(f"{sets_directory}\Regions.xlsx", sheet_name=model, index_col=[0]).loc[:, sets_selection["Regions"][model]].to_frame()    
            sets_sel[model]["Regions"] = sets_sel[model]["Regions"][sets_sel[model]["Regions"][sets_selection["Regions"][model]].str.contains("unused") != True]
            sets_sel[model]["Regions"].index.names = ['Raw']
            sets_sel[model]["Regions"].reset_index(inplace=True)
            sets_sel[model]["Regions"].set_index(list(sets_sel[model]["Regions"].columns), inplace=True)
            sets_sel[model]["Regions"] = list(set(sets_sel[model]["Regions"].index))
            
            sets_sel[model]["Variables"] = pd.read_excel(f"{sets_directory}\Variables.xlsx", sheet_name=model, index_col=[0]).loc[:, sets_selection["Variables"][model]].to_frame()    
            sets_sel[model]["Variables"] = sets_sel[model]["Variables"][sets_sel[model]["Variables"][sets_selection["Variables"][model]].str.contains("unused") != True]
            sets_sel[model]["Variables"].index.names = ['Raw']
            sets_sel[model]["Variables"].reset_index(inplace=True)
            sets_sel[model]["Variables"].set_index(list(sets_sel[model]["Variables"].columns), inplace=True)
            sets_sel[model]["Variables"] = list(set(sets_sel[model]["Variables"].index))
        
            sets_sel[model]["Years"] = pd.read_excel(f"{sets_directory}\Years.xlsx", sheet_name=model, index_col=[0]).loc[:, sets_selection["Years"][model]].to_frame()    
            try:
                sets_sel[model]["Years"] = sets_sel[model]["Years"][sets_sel[model]["Years"][sets_selection["Years"][model]].str.contains("unused") != True]
            except:
                pass
            sets_sel[model]["Years"].index.names = ['Raw']
            sets_sel[model]["Years"].reset_index(inplace=True)
            sets_sel[model]["Years"].set_index(list(sets_sel[model]["Years"].columns), inplace=True)
            sets_sel[model]["Years"] = list(set(sets_sel[model]["Years"].index))
        

        "Preparing new indices"
        for model in models:
            new_indices = {}
            new_indices['Scenarios'] = list(dc(model_results[model].index.get_level_values('Scenario')))
            for item in sets_sel[model]['Scenarios']:
                new_indices['Scenarios'] = [x if x!=item[0] else item[1] for x in new_indices['Scenarios']]

            new_indices['Regions'] = list(dc(model_results[model].index.get_level_values('Region')))
            for item in sets_sel[model]['Regions']:
                new_indices['Regions'] = [x if x!=item[0] else item[1] for x in new_indices['Regions']]
                    
            new_indices['Variables'] = list(dc(model_results[model].index.get_level_values('Variable')))
            for item in sets_sel[model]['Variables']:
                new_indices['Variables'] = [x if x!=item[0] else item[1] for x in new_indices['Variables']]

            new_indices['Years'] = list(dc(model_results[model].columns))
            for item in sets_sel[model]['Years']:
                new_indices['Years'] = [x if x!=item[0] else item[1] for x in new_indices['Years']]
            
            model_results[model].index = pd.MultiIndex.from_arrays([
                model_results[model].index.get_level_values('Model'),
                new_indices['Scenarios'],
                new_indices['Regions'],
                new_indices['Variables'],
                model_results[model].index.get_level_values('Unit'),
                ])
            model_results[model].columns = new_indices['Years']
            
            model_results[model].index.names = ["Model", "Scenario", "Region", "Variable", "Unit"]
            
            model_results[model] = model_results[model].groupby(
                level = list(model_results[model].index.names),
                axis = 0,
                ).sum()        
        
        sets_sel2 = dc(sets_sel)
        for model in models:
            for i in sets_sel[model].keys():
                sets_sel2[model][i] = []
                for v in sets_sel[model][i]:
                    sets_sel2[model][i] += [v[1]]
                sets_sel2[model][i] = sorted(list(set(sets_sel2[model][i])))
            
    return model_results, sets_sel2

#%%
def mapping_shocks(study,model):
    df = pd.read_excel(os.getcwd()+f"\\{study}\\Models_link\\Mapping\\Map_{model}.xlsx", sheet_name=None, index_col=[0])
    return df

#%%
def trades_results(
        paths_file, 
        user, 
        model_results,
        model,
        sets_selection,
        load_sets=True,):

    """parsing models results""" 
    try:
        trade_results = pd.read_excel(pd.read_excel(paths_file, index_col=[0]).loc[f"{model}_trades",user])
        trade_results.set_index(["Model", "Scenario", "Region", "Variable", "Unit", "Year"], inplace=True)
        trade_results = trade_results.unstack(level='Year')
        trade_results.columns = trade_results.columns.get_level_values(-1)

        sets_sel = {}
        sets_directory = pd.read_excel(paths_file, index_col=[0]).loc["Models_Sets",user]
    
        if load_sets:
            sets_sel[model] = {}
                       
            sets_sel[model]["Regions"] = pd.read_excel(f"{sets_directory}\Regions.xlsx", sheet_name=model, index_col=[0]).loc[:, sets_selection["Regions"][model]].to_frame()    
            sets_sel[model]["Regions"] = sets_sel[model]["Regions"][sets_sel[model]["Regions"][sets_selection["Regions"][model]].str.contains("unused") != True]
            sets_sel[model]["Regions"].index.names = ['Raw']
            sets_sel[model]["Regions"].reset_index(inplace=True)
            sets_sel[model]["Regions"].set_index(list(sets_sel[model]["Regions"].columns), inplace=True)
            sets_sel[model]["Regions"] = list(set(sets_sel[model]["Regions"].index))

            new_indices = {}
            new_indices['Regions'] = list(dc(trade_results.index.get_level_values('Region')))
            for item in sets_sel[model]['Regions']:
                new_indices['Regions'] = ['EU27+UK' for i in new_indices['Regions']]
            
            trade_results.index = pd.MultiIndex.from_arrays([
                trade_results.index.get_level_values('Model'),
                trade_results.index.get_level_values('Scenario'),
                new_indices['Regions'],
                trade_results.index.get_level_values('Variable'),
                trade_results.index.get_level_values('Unit'),
                ])
            
            trade_results.index.names = ["Model", "Scenario", "Region", "Variable", "Unit"]
            
            trade_results = trade_results.groupby(
                level = list(trade_results.index.names),
                axis = 0,
                ).sum()        
        
        model_results = pd.concat([model_results, trade_results], axis=0)
    except:
        pass
    
    return(model_results)


























