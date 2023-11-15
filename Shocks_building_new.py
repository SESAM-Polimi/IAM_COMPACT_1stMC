# -*- coding: utf-8 -*-
"""
Created on Tue Nov 14 11:06:53 2023

@author: loren
"""

import pandas as pd
import mario

import os


def sceMARIOs_definition(
        model_sets,
        method = ['Scenario','Year'],
        ):
    
    model_sets['SceMARIOs'] = []
    for m1 in model_sets[method[0]]:
        for m2 in model_sets[method[1]]:
            model_sets['SceMARIOs'] += [f"{m1} - {m2}"] 
    
    return model_sets   
 

def electricity_consumption_mix_update(
        shock_map,
        SUT_db,
        template_path,
        model_result,
        ):
    
    shock_map = shock_map.query(f"Function=='electricity_consumption_mix_update'")
    variables = list(shock_map.index)
    var_com_map = {var:com for (var,com) in zip(list(shock_map.index),shock_map['Commodity'])}
    
    shocks = pd.read_excel(template_path,sheet_name=None)
    
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

    
    

    

    return
    
    