import mario
from mario.tools.constants import _MASTER_INDEX as MI
import pandas as pd
import numpy as np
from openpyxl import load_workbook
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots


sN = slice(None)

def plot_footprints(
        path_results,
        path_physical,
        path_aggregation,
        path_plot,
        sat_accounts,
        units,
        GWP,
        regions_to,
        ee_prices,
        activities_to,
        scenario,
        load_ph_footprints = True,
        ):

    ss = sat_accounts[0]
    scemarios = [".".join(file.split(".")[:-1]) for file in os.listdir(f"{path_results}\\{ss}")]
    sN = slice(None)

    if load_ph_footprints == False:
        #% Reading and rearranging footprints results
        f = {}
        for sa in sat_accounts:
            f[sa] = pd.DataFrame()
            for scem in scemarios:
                f_sa_scen = pd.read_csv(f"{path_results}\\{sa}\\{scem}.csv", index_col=[0,1,2], header=[0,1,2], sep=',')#.loc[(sN,"Activity",sN),(sN,"Activity",sN)]
                f_sa_scen = f_sa_scen.stack(level=[0,1,2])
                f_sa_scen = f_sa_scen.to_frame()
                f_sa_scen.columns = ['Value']
                f_sa_scen["Account"] = sa
                f_sa_scen["Scenario"] = f"{scem}"
                f_sa_scen = f_sa_scen.droplevel(level=[1,4], axis=0)
                f_sa_scen.index.names = ["Region from", "Activity from", "Region to", "Activity to"]
                # f_sa_scen = f_sa_scen.loc[(sN,sN,regions_to,activities_to),:]
                f_sa_scen.reset_index(inplace=True)
                f[sa] = pd.concat([f[sa], f_sa_scen], axis=0)
            f[sa].set_index(["Region from", "Activity from", "Region to", "Activity to","Scenario","Account"], inplace=True)
            f[sa] = f[sa].groupby(level=f[sa].index.names).mean()
    
    
        # Conversions to pysical units
        
        for sa,footprint in f.items():
            
            # footprint['Year'] = [int(i.split(' - ')[1]) for i in footprint.index.get_level_values('Scenario')]
            # footprint.set_index('Year',append=True, inplace=True)
            
            for act in units['Activity']:
                    
                if units['Activity'][act]['conv'] == 'price':
                    footprint.loc[(sN,sN,sN,act,sN,sN),'Value'] *= units['Satellite account'][sa]['conv']*ee_prices.loc['EU27+UK','€/kWh']*1e6
                else:
                    footprint.loc[(sN,sN,sN,act,sN,sN),'Value'] *= units['Satellite account'][sa]['conv']*units['Activity'][act]['conv']
                        
    
        # Saving converted footprints
        for sa,footprint in f.items():
            footprint.to_csv(f"{path_physical}\\{sa}.csv")
    
    else:        
        # Read saved footprints in physical units
        f = {}
        for sa in sat_accounts:
            f[sa] = pd.read_csv(f"{path_physical}\\{sa}.csv", index_col=[0,1,2,3,4,5])
        
    # Calculation of total GHG emissions
    f['GHGs'] = pd.DataFrame()
    for sa,gwp in GWP.items():
        f['GHGs'] = pd.concat([f['GHGs'], f[sa]*gwp], axis=0)
    f['GHGs'] = f['GHGs'].groupby(level=["Region from","Activity from","Region to","Activity to","Scenario"]).sum()        
    
    # Export physical ghg footprint
    f['GHGs'].to_csv(f"{path_physical}\\GHGs.csv")
    
    # Split scemarios columns
    # f = {'GHGs': f['GHGs']}
    sN = slice(None)

    for sa,footprint in f.items():
        if 'Account' not in footprint.index.names:
            footprint.loc[:,'Account'] = sa        
        footprint.reset_index(inplace=True)
        footprint.set_index(['Region from', 'Activity from', 'Region to', 'Activity to', 'Scenario', 'Account'], inplace=True)
        f[sa] = footprint
        
    # Aggregating
    new_activities = pd.read_excel(path_aggregation, index_col=[0], sheet_name='Activity')
    new_regions = pd.read_excel(path_aggregation, index_col=[0], sheet_name='Region')
    
    for sa,v in f.items():
        v_index = v.index.names
        v.reset_index(inplace=True)
        v["Activity from"] = v["Activity from"].map(new_activities["New"])
        v["Region from"] = v["Region from"].map(new_regions["New"])
        v.set_index(list(v_index), inplace=True)
        v = v.groupby(list(v_index)).sum()#), as_index=False).sum()
        # v.set_index(list(v.columns[:-1]), inplace=True)
        f[sa] = v

    unitss = {
        "Production of offshore wind plants":"tonCO2eq/MW", 
        "Production of onshore wind plants":"tonCO2eq/MW", 
        "Production of photovoltaic plants":"tonCO2eq/MW", 
        "Production of electricity by wind":"tonCO2eq/GWh", 
        "Production of electricity by solar photovoltaic":"tonCO2eq/GWh", 
        "Production of electricity by Geothermal":"tonCO2eq/GWh", 
        "Production of electricity by biomass and waste":"tonCO2eq/GWh", 
        "Production of electricity by coal":"tonCO2eq/GWh", 
        "Production of electricity by gas":"tonCO2eq/GWh", 
        "Production of electricity by hydro":"tonCO2eq/GWh", 
        "Production of electricity by nuclear":"tonCO2eq/GWh", 
        "Production of electricity by petroleum and other oil derivatives":"tonCO2eq/GWh", 
        "Production of electricity by solar thermal":"tonCO2eq/GWh", 
        "Production of electricity by tide, wave, ocean":"tonCO2eq/GWh", 
        "Production of electricity nec":"tonCO2eq/GWh",
        }
    unitss = pd.DataFrame(list(unitss[i] for i in unitss.keys()), index=list(unitss.keys()))
    
    f['GHGs']["Unit"] = f['GHGs'].index.get_level_values('Activity to').map(unitss[0])
    f['GHGs'].set_index(['Unit'],append=True,inplace=True)

    # Rename activities
    activities_names = {
        'Production of photovoltaic plants': 'PV',
        'Production of onshore wind plants': 'Onshore wind',
        'Production of offshore wind plants': 'Offshore wind',
        'Production of electricity by wind': 'Electricity by wind',
        'Production of electricity by solar photovoltaic': 'Electricity by PV',        
        }

    for sa,v in f.items():
        index_names = list(v.index.names)
        v.reset_index(inplace=True)
        for old,new in activities_names.items():
            v = v.replace(old,new)
        v.set_index(index_names, inplace=True)
        v = v.groupby(level=index_names, axis=0).sum()
        f[sa] = v
    

    # Plot: ghgs footprints by region&commodity. Subplots by unit of measures
    names = list(f['GHGs'].index.names)
    f['GHGs'].reset_index(inplace=True)
    acts = [activities_names[i] for i in activities_names.keys()]
    f['GHGs'] = f['GHGs'].query("`Activity to`==@acts")
    f['GHGs'].set_index(names,inplace=True)

    colors = {
        'Agriculture & food': '#f94144',
        'Mining & quarrying': '#f8961e',
        'Metals': '#f9c74f',
        'Petrochemicals': '#d9ed92',
        'Other manufacturing': '#74c69d',
        'Electricity': '#048ba8',
        'Services': '#184e77',
        'Transport': '#815ac0',
        }

    patterns = {
        'EU27': "",
        'China': '/',
        'RoW': 'x',
        }

    query = f"Scenario=='{scenario}'"
    groupby = ["Region from", "Activity from", "Region to", "Activity to", "Unit"]
        
    f_ghg = f['GHGs'].reset_index().query(query)
    for region in list(set(f_ghg['Region from'])):
        if region not in ['EU27','China']:
            f_ghg = f_ghg.replace(region,'RoW')
    f_ghg = f_ghg.groupby(groupby).sum().reset_index()
    
    
    fig = make_subplots(rows=1, cols=len(set(f_ghg['Unit'])), subplot_titles=["<b>Electricity produced (tonCO2eq/GWh)<b>","<b>Capacity (tonCO2eq/MW)<b>"])

    # scatters
    sat = 'GHGs'
    col = 1
    
    # bars
    col = 1
    legend_labels = []
    for unit in sorted(list(set(f_ghg['Unit']))):   
        for activity in list(colors.keys())[::-1]:
            for region in ['RoW','China','EU27']:#sorted(list(set(f_ghg.query(f"Unit=='{unit}' & Commodity=='{commodity}'")['Region from']))):
                to_plot = f_ghg.query(f"Unit=='{unit}' & `Activity from`=='{activity}' & `Region from` == '{region}'")                                            
                name = f"{activity} - {region}"
                showlegend = False
                if name not in legend_labels:
                    legend_labels += [name]
                    showlegend = True
                
                fig.add_trace(go.Bar(
                    x = [f"<b>{i}<b>" for i in  to_plot['Activity to']],
                    y = to_plot['Value'],
                    name = name,
                    marker_color = colors[activity],
                    marker_pattern_shape = patterns[region],
                    marker_line_color = 'black',
                    marker_line_width = 0.75,
                    marker_pattern_size = 6, 
                    legendgroup = name,
                    showlegend = showlegend,
                    # opacity=0.7,
                    ),
                    row = 1,
                    col = col,
                    )
    
        col += 1

    fig.update_layout(
        barmode='stack',
        font_family='HelveticaNeue Light', 
        # font_size=10,
        title = f"<b>GHGs footprints of electricity produced and capacity of PV and wind technologies</b><br>Exiobase v3.8.2, refined with MARIO",
        template = 'plotly_white',
        legend_tracegroupgap = 0.1,
        legend_title = "<b>Breakdown by origin activity-region",
        legend_title_font_size = 13,
        legend_traceorder = 'reversed',
        xaxis1 = dict(
            showline=True,
            linecolor = 'black',
            linewidth = 1.4
            ),
        xaxis2 = dict(
            showline=True,
            linecolor = 'black',
            linewidth = 1.4
            ),
    
        )
    fig.update_annotations(font_size=13)
    fig.write_html(f'{path_plot}', auto_open=True)
    

