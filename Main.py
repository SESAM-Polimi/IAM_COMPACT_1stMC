#%% Importing Dependences
import mario
import pandas as pd
import os
from copy import deepcopy as dc
import pandas as pd
from Models_Link import (
    main_models_results,
    trades_results,
    )
from Shocks_building import(
    sceMARIOs_definition,
    var_to_function_assignment,
    get_shock_templates,
    fill_shock_templates,
    get_shock_clusters,
    EY_update,
    )

user = "LR"
studies = {
    'Study 4': ['GCAM'] # 'TIAM'
    }
sN = slice(None)
paths = 'Paths.xlsx'

study = 'Study 4'

#%% Reading IAMs models results
sets_selection = {
    "Scenarios": {"GCAM": "Selection 1", "PROMETHEUS": "Selection 1", "TIAM": "Selection 1", "MUSE": "Selection 1"},
    "Regions": {"GCAM": "Selection 1", "PROMETHEUS": "Selection 1", "TIAM": "Selection 1", "MUSE": "Selection 1"},
    "Variables": {"GCAM": "Selection 1", "PROMETHEUS": "Selection 1", "TIAM": "Selection 1", "MUSE": "Selection 1"},
    "Years": {"GCAM": "Selection 1", "PROMETHEUS": "Selection 1", "TIAM": "Selection 1", "MUSE": "Selection 1"},
    }

models_results, models_sets = main_models_results(
    paths_file = paths,
    user = user,
    models = studies[study], 
    sets_selection = sets_selection,
    study = study,
    )

#%% Importing each baseline SUTs
worlds = {}
for model in studies[study]:
    worlds[model] = mario.parse_from_txt(r"\\".join(os.getcwd().split("\\"))+f"\\{study}\\Baseline SUT\\{model}\\flows", table='SUT', mode='flows')

#%% Reading Information to map models variables with baseline SUT sets and to automatically implement shocks
mapping_info = {}
for model in studies[study]:
    mapping_info[model] = pd.read_excel(os.getcwd()+f"\\{study}\\Models_link\\Mapping\\Map_{model}.xlsx", sheet_name=None, index_col=[0])

#%% creating inputs to fill shocks templates
shock_inputs = {}
for model in studies[study]:
    print(model)
    shock_inputs[model] = var_to_function_assignment(
        shock_map = mapping_info[model]['shock_map'],
        models_results = models_results,
        models_sets = models_sets,
        mario_db = worlds[model],
        paths = paths,
        user = user,
        model = model
        )

#%% getting shock excel templates for each model and scemario
for model in studies[study]:
    get_shock_templates(
        paths, 
        worlds[model], 
        user, 
        model,
        study,
        )

#%% filling shock excel templates and saving shock files for each scemario
for model in studies[study]:
    print(model)
    mapping_info[model]['shock_map'].reset_index(inplace=True)
    mapping_info[model]['shock_map'].set_index(['Variables', 'Function', 'Functions clustering'], inplace=True)
    fill_shock_templates(
        paths_file = paths,
        model_sets = models_sets[model],
        SI = shock_inputs[model],
        model = model,
        mapping_info = mapping_info[model],
        user = user,
        study = study,
        worlds = worlds,
        )

#%%
for model in studies[study]:
    print(model)
    mapping_info[model]['shock_map'].reset_index(inplace=True)
    mapping_info[model]['shock_map'].set_index(['Variables', 'Function', 'Functions clustering'], inplace=True)

    for scemario in models_sets[model]['SceMARIOs']:
        print(scemario)
        clusters = get_shock_clusters(mapping_info[model], worlds[model])
        worlds[model].shock_calc(
            io = os.getcwd()+f"\\{study}\\Shocks\\{model}\\{scemario}.xlsx",
            Y = True,
            z = True,
            scenario = scemario,
            **clusters
            )
        
    # EY_update(
    #     model_sets = models_sets[model],
    #     shock_inputs = shock_inputs[model],
    #     mapping_info = mapping_info[model],
    #     mario_db = worlds[model]
    #     )
        
#%%



