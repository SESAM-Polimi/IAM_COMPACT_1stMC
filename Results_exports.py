import mario
from mario.tools.constants import _MASTER_INDEX as MI
import pandas as pd
import numpy as np
from openpyxl import load_workbook
import os


def export_footprints(
        mario_db,
        sat_accounts,
        activities,
        regions,
        path,
        ghgs = None,
        ):
    
    f = {}
    sN = slice(None)
    
    for a in sat_accounts:
        f[a] = {}
        if ":" in a:
            name = a.replace(':'," -")
        else:
            name = a
        for s in mario_db.scenarios:
            e = mario_db.get_data(matrices=['e'], scenarios=[s])[s][0].loc[a]
            w = mario_db.get_data(matrices=['w'], scenarios=[s])[s][0]
            f[a][s] = np.diag(e) @ w
            f[a][s].index = f[a][s].columns
            f[a][s] = f[a][s].loc[(sN,'Activity',sN),(regions,sN,activities)]
        
        for k,v in f[a].items():
            subfolder = f"{path}\\{name}"
            if not os.path.exists(subfolder):
                os.mkdir(subfolder)
            v.to_csv(f"{subfolder}\\{k}.csv")

    if ghgs != None:
        f['GHGs'] = {}
        for s in mario_db.scenarios:
            f['GHGs'][s] = 0
            for ghg,gwp in ghgs.items():
                f['GHGs'][s] += f[ghg][s]*gwp
            subfolder = f"{path}\\{'GHGs'}"
            if not os.path.exists(subfolder):
                os.mkdir(subfolder)
            f['GHGs'][s].to_csv(f"{subfolder}\\{s}.csv")
            

def export_linkages(
        mario_db,
        method,
        path_linkages,
        path_wiliam,
        save_wiliam = False,
        ):
    
    linkages = {}
    linkages_df = pd.DataFrame()

    for scem in mario_db.scenarios:
        db = mario.Database(
            Z = mario_db.matrices[scem]['Z'],
            Y = mario_db.matrices[scem]['Y'],
            E = mario_db.matrices[scem]['E'],
            V = mario_db.matrices[scem]['V'],
            EY =mario_db.matrices[scem]['EY'],
            units = mario_db.units,
            table='SUT',
        )
        db.to_iot(method=method)
        linkages[f'{scem}'] = db.calc_linkages(multi_mode=True, normalized=False)
        linkages[f'{scem}'] = linkages[f'{scem}'].droplevel(1)
        new_columns = pd.MultiIndex.from_arrays(
            [[i[0].split(" ")[0] for i in list(linkages[f'{scem}'].columns)],
            [i[0].split(" ")[1] for i in list(linkages[f'{scem}'].columns)],
            [i[1] for i in list(linkages[f'{scem}'].columns)],],
            )
        linkages[f'{scem}'].columns = new_columns
        linkages[f'{scem}'].columns.names = ['Scope',"Direction","Origin"]
        linkages[f'{scem}'] = linkages[f'{scem}'].stack([0,1,2]).to_frame()
        linkages[f'{scem}'].columns = ['Value']
        linkages[f'{scem}']['Scenario'] = scem
        
        linkages_df = pd.concat([linkages_df, linkages[f'{scem}']], axis=0)
        
        folder_name = f"{path_wiliam}\\{scem}"
        if save_wiliam:
            if not os.path.exists(folder_name):
                os.mkdir(folder_name)
            db.to_txt(folder_name, flows=False, coefficients=True)

    linkages_df.reset_index(inplace=True)
    linkages_df.to_csv(f"{path_linkages}\\Linkages.csv", index=False)
    
    
