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
from Results_exports import export_footprints, export_linkages
from Plots import plot_footprints

user = "LR"
studies = {
    'Study 2': ['EnergyPLAN'],
    'Study 3': ['GCAM'], # 'TIAM'
    'Study 4': ['GCAM'], # 'TIAM'    
    }
sN = slice(None)
paths = 'Paths.xlsx'

study = 'Study 3'

#%% Reading IAMs models results
sets_selection = {
    "Scenarios": {"GCAM": "Selection 1", "PROMETHEUS": "Selection 1", "TIAM": "Selection 1", "MUSE": "Selection 1","EnergyPLAN": "Selection 1"},
    "Regions": {"GCAM": "Selection 1", "PROMETHEUS": "Selection 1", "TIAM": "Selection 1", "MUSE": "Selection 1","EnergyPLAN": "Selection 1"},
    "Variables": {"GCAM": "Selection 1", "PROMETHEUS": "Selection 1", "TIAM": "Selection 1", "MUSE": "Selection 1","EnergyPLAN": "Selection 1"},
    "Years": {"GCAM": "Selection 1", "PROMETHEUS": "Selection 1", "TIAM": "Selection 1", "MUSE": "Selection 1","EnergyPLAN": "Selection 1"},
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

        

#%% Exporting tables
for model in studies[study]:
    for scenarios in worlds[model].scenarios:
        folder_name = os.getcwd()+f"\\{study}\\Results\\{model}\\SUTs\\{scenarios}"
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)
        worlds[model].to_txt(folder_name, scenario=scenarios)

#%% exporting results
for model in studies[study]:
#     export_footprints(
#         mario_db = worlds[model],
#         sat_accounts = [
#             'CO2',
#             'CH4 - combustion - air',
#             'N2O - combustion - air',
#             ],
#         activities = [
#                 'Production of photovoltaic plants',
#                 'Production of onshore wind plants',
#                 'Production of offshore wind plants',
#                 'Production of electricity by Geothermal',
#                 'Production of electricity by biomass and waste',
#                 'Production of electricity by coal',
#                 'Production of electricity by gas',
#                 'Production of electricity by hydro',
#                 'Production of electricity by nuclear',
#                 'Production of electricity by petroleum and other oil derivatives',
#                 'Production of electricity by solar photovoltaic',
#                 'Production of electricity by solar thermal',
#                 'Production of electricity by tide, wave, ocean',
#                 'Production of electricity by wind',
#                 'Production of electricity nec',
#            ],
#         regions = ['EU27'],
#         path = os.getcwd()+f"\\{study}\\Results\\{model}\\Footprints_Monetary",
#         ghgs = {
#             'CO2 - combustion - air': 1,
#             'CH4 - combustion - air': 26,
#             'N2O - combustion - air': 298,
#             },
#         )
    
    export_linkages(
        mario_db = worlds[model],
        method = 'D',
        path_linkages = os.getcwd()+f"\\{study}\\Results\\{model}\\Linkages",
        path_wiliam = os.getcwd()+f"\\{study}\\Results\\{model}\\WILIAM",
        save_wiliam = True,
        )
    
#%% reimporting 2050 tables and applying re/off shoring shocks
# scenarios = ['NDC_LTT_CBAM - 2050','NDC_LTT_INDEPENDENCE - 2050','NDC_LTT - 2050']
# shocks = ['New steel sectors_2050_imp','New steel sectors_2050_prod']

# worlds = {}

# for model in studies[study]:
#     worlds[model] = {}
#     for scenario in scenarios:
#         folder_name = os.getcwd()+f"\\{study}\\Results\\{model}\\SUTs\\{scenario}\\flows"
#         worlds[model][scenario] = mario.parse_from_txt(folder_name,table='SUT',mode='flows') 
#         for shock in shocks:
#             worlds[model][scenario].shock_calc(os.getcwd()+f"\\{study}\\Shocks\\{model}\\{shock}.xlsx",z=True,e=True,scenario=shock)
            
#             db = mario.Database(
#                 Z = worlds[model][scenario].matrices[shock]['Z'],
#                 Y = worlds[model][scenario].matrices[shock]['Y'],
#                 E = worlds[model][scenario].matrices[shock]['E'],
#                 V = worlds[model][scenario].matrices[shock]['V'],
#                 EY =worlds[model][scenario].matrices[shock]['EY'],
#                 units = worlds[model][scenario].units,
#                 table='SUT',
#             )
#             db.to_iot(method='D') 
#             db.to_txt(os.getcwd()+f"\\{study}\\Results\\{model}\\WILIAM\\{scenario}_{shock.split('_')[-1]}",flows=False,coefficients=True)
        
        

#%% plotting results
# from _plot_properties import study_properties as sp

# for model in studies[study]:

#     plot_footprints(
#         sat_accounts = sp[study]['sat_accounts'], 
#         units = sp[study]['units'], 
#         GWP = sp[study]['GWP'], 
#         regions_to = sp[study]['regions_to'], 
#         activities_to = sp[study]['activities_to'], 
#         scenario = 'Baseline - 2050',
#         ee_prices = pd.read_excel('ee_prices.xlsx',sheet_name=model,index_col=[0]),
#         path_results=os.getcwd()+f"\\{study}\\Results\\{model}\\Footprints_Monetary",
#         path_physical=os.getcwd()+f"\\{study}\\Results\\{model}\\Footprints_Physical",
#         path_aggregation=os.getcwd()+f"\\{study}\\Results\\{model}\\Aggregation_plots.xlsx",
#         path_plot=os.getcwd()+f"\\{study}\\Results\\{model}\\Plots\\Footprints.html",
#         load_ph_footprints=False,
#         )
    
#%%   
sc = 'Domestic'
mats = {
    'Aluminium ores and concentrates': 'Aluminium',
    'Copper ores and concentrates': 'Copper',
    'Dysprosium': 'Dysprosium',
    'Iron ores': 'Iron',
    'Neodymium': 'Noedymium',
    'Nickel ores and concentrates': 'Nickel',
    'Raw silicon': 'Silicon',
    }

techs = {
    'Production of photovoltaic plants': 'PV',
    'Production of onshore wind plands': 'Onshore wind',
    'Production of offshore wind plants': 'Offshore wind',
    }

for model in studies[study]: 
    if study=='Study 3':
        
        path = f"{study}\Results\{model}\SUTs\{sc} supply chains"
        
        scems = os.listdir(path)
        scens = []
        years = []
        
        X_mat = {}
        X_techs = {}
        
        for scem in scems:
            s = scem.split(' - ')[0]
            y = scem.split(' - ')[-1]
            if s not in scens and s!='baseline':
                scens += [s]
            if y not in years:
                years += [y]
            
            X_mat[s] = pd.DataFrame()
            X_techs[s] = pd.DataFrame()

        for scem in scems:
            s = scem.split(' - ')[0]
            y = scem.split(' - ')[-1]
            
            world = mario.parse_from_txt(f"{path}\\{scem}\\flows", 'SUT', 'flows')
            
            X1 = world.X.loc[(slice(None),'Commodity',list(mats.keys())),:]
            X2 = world.X.loc[(slice(None),'Activity',list(techs.keys())),:]#.sum(1).to_frame()
            X1.columns = [y]
            X2.columns = [y]
            
            X_mat[s] = pd.concat([X_mat[s],X1],axis=1)
            X_techs[s] = pd.concat([X_techs[s],X2],axis=1)
        


#%%
path = r"C:\Users\loren\Documents\GitHub\SESAM\IAM_COMPACT_1stMC\Study 3\Results\GCAM\WILIAM\Domestic supply chains"
names = os.listdir(path)

Y = {}
z = {}
e = {}
v = {}
for name in names:
    world = mario.parse_from_txt(f"{path}\\{name}\\coefficients", 'IOT', 'coefficients')
    Y[name] = world.Y
    z[name] = world.z
    e[name] = world.e
    v[name] = world.v
    
yy = Y['CP_EI - 2005'] - Y['CP_EI - 2010']
zz = z['CP_EI - 2005'] - z['CP_EI - 2010']
ee = e['CP_EI - 2005'] - e['CP_EI - 2010']
vv = v['CP_EI - 2005'] - v['CP_EI - 2010']
            
            
            
        

