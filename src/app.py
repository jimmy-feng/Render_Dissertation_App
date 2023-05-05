from dash import Dash, dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_datetimepicker
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import dash_reusable_components as drc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime as dt
from datetime import timedelta
import pandas as pd
import geopandas as gpd
import movingpandas as mpd
import re
import json
import numpy as np

# Plotly mapbox API token
import config_mapbox
mapbox_accesstoken = config_mapbox.key

#############################################################################################
# Load and preprocess data:

# Grocery Stores scraped from Google Maps
stores = pd.read_csv('../Data/All_Food_Stores_Features.csv', index_col=0)
# Only keep important columns for display
stores.rename(columns = {
    'Descript': 'Description',
    'G_MAP_URL': 'Google Maps URL',
    }, inplace=True)

specific_store_type = stores['Type'].copy()
stores.insert(4, 'Specific Type', specific_store_type)

# Google Maps POI Type; use ['Store_Type'] for greater simplification of store type (Grocery, Convenience, and Wholesale)
all_options = list(stores['Type'].unique())
# Dictionary of POI types for filtering in dashboard
dictOfOptions = dict(zip(all_options, all_options))
dictOfOptions = [{key : value} for key, value in dictOfOptions.items()]

stores_table_columns = ['Name', 'Rating', 'Price', 'Type', 'Specific Type', 'Convenience', 'Customer Service and Checkout Process', 'Employees',	'Food Departments and Quality',	'Food Selection and Variety', 'Shop_Store', 'Shop_Online', 'Delivery', 'Pickup_Curbside', 'Pickup_Store', 'Drive_Thru', 'Delivery_No_Contact', 'Delivery_Same_Day', 'Masks_Required', 'Great_Service', 'Wheelchair_Accessible', 'Quick_Visit', 'Organic_Food', 'Prepared_Food', 'Pay_Checks', 'Pay_Debit_Cards', 'Pay_NFC_Mobile', 'Pay_SNAP_EBT', 'Pay_Credit_Cards', 'Restroom', 'LGBTQ_Friendly', 'Family_Friendly', 'Longitude', 'Latitude', 'Address', 'PlusCode']

stores[stores_table_columns[5:10]] = stores[stores_table_columns[5:10]].round(2)
stores = stores.replace({np.nan: None})

# Condense store types
stores['Type'].replace({'Asian grocery store': 'Ethnic grocery store',
                        'Butcher shop': 'Specialty food store',
                        'Cafe': 'Ethnic grocery store',
                        'Dollar store': 'Discount store',
                        'Discount supermarket': 'Discount store',
                        'Furniture store': 'Specialty food store',
                        'Gas station': 'Convenience store',
                        'Gourmet grocery store': 'Ethnic grocery store',
                        'Health food store': 'Grocery store',
                        'Lunch restaurant': 'Specialty food store',
                        'Market': 'Convenience store',
                        'Mexican grocery store': 'Ethnic grocery store',
                        'Mexican restaurant': 'Ethnic grocery store',
                        'Produce market': 'Specialty food store',
                        'Store': 'Convenience store', # Weigel's Farm Stores only
                        'Supermarket': 'Grocery store',
                        'Warehouse club': 'Warehouse store'
                        }, inplace=True)

# Determine online options
def get_online_stores(df):
    stores_online = df[df['Delivery'] == 'Yes'][['Name', 'PlusCode', 'Delivery']].copy()
    
    for i_online, r_online in stores_online.iterrows():
        if 'Publix' in r_online['Name']:
            stores_online.loc[i_online, 'Name'] = 'Publix Super Market'
        if 'Walmart' in r_online['Name']:
            stores_online.loc[i_online, 'Name'] = 'Walmart'
        if 'Kroger' in r_online['Name']:
            stores_online.loc[i_online, 'Name'] = 'Kroger'
        if 'Target' in r_online['Name']:
            stores_online.loc[i_online, 'Name'] = 'Target'
        if 'Food City' in r_online['Name']:
            stores_online.loc[i_online, 'Name'] = 'Food City'
        if 'BreadBox' in r_online['Name'] or 'Bread Box' in r_online['Name']:
            stores_online.loc[i_online, 'Name'] = 'BreadBox'
        if 'Ingles' in r_online['Name']:
            stores_online.loc[i_online, 'Name'] = 'Ingles'
            
    #stores_online.drop_duplicates(['Name'], inplace=True, ignore_index=True)
    
    return stores_online

stores_online = get_online_stores(stores)

# Travel times between stops in people's trajectories and stores
od = pd.read_csv('../Data/OD_v2.csv', index_col=0)
od['free_time_start'] = pd.to_datetime(od['free_time_start'])#.dt.tz_localize('US/Eastern')
od['free_time_end'] = pd.to_datetime(od['free_time_end'])#.dt.tz_localize('US/Eastern')

# Individuals' information
individuals = pd.read_csv('../Data/People_Synthetic_Data.csv')
individuals.description = individuals.description.str.wrap(30)
individuals.description = individuals.description.apply(lambda x: x.replace('\n', '<br>'))
# Assume all virtual locations are available to a person from the start
physical_opp = od[od['can_visit_spacetime']].groupby('person_id')['store_PlusCode'].nunique().reset_index().rename({'store_PlusCode':'PhysicalOpp'}, axis=1)
individuals[individuals['digitallit'].isin(od['person_id'].unique())]

## IDENTIFY HYBRID OPTIONS
# OD rows where people can physically reach opportunities in space-time
od_visit_spacetime = od['can_visit_spacetime']
# OD rows for people who are digitally literate
od_digitallit = od['person_id'].isin(individuals[individuals['digitallit'] == 'yes']['person_id'].values)
# OD rows where the store has online shopping option
od_shop_online = od['store_PlusCode'].isin(stores[stores['Shop_Online'] == True]['PlusCode'].values)

# od[od_visit_spacetime & od_digitallit & od_shop_online].groupby('person_id')['store_PlusCode'].nunique().reset_index().rename({'store_PlusCode':'HybridOpp'}, axis=1)
physical_opp['PhysicalOpp'] = physical_opp['PhysicalOpp'].fillna(0)

individuals = pd.merge(individuals, physical_opp, left_on='person_id', right_on='person_id', how='left')
individuals['VirtualOpp'] = [len(stores_online) if indiv_r['digitallit'] == 'yes' else 0 for indiv_i, indiv_r in individuals.iterrows()]   
individuals['PhysicalOpp'] = individuals['PhysicalOpp'].replace(np.nan, 0)
individuals['VirtualOpp'] = individuals['VirtualOpp'].replace(np.nan, 0)

# hybrid_pluscode = od[od_visit_spacetime & od_digitallit & od_shop_online]['store_PlusCode'].drop_duplicates().values
# physical_pluscode = od[~od['store_PlusCode'].isin(hybrid_pluscode) & od_visit_spacetime]['store_PlusCode'].drop_duplicates().values
# virtual_pluscode = get_online_stores(stores[stores['PlusCode'].isin(od[~(od['store_PlusCode'].isin(hybrid_pluscode)) & ~(od['store_PlusCode'].isin(physical_pluscode))]['store_PlusCode'].drop_duplicates().values) & stores['Shop_Online']])['PlusCode'].values

# physical_opp_total_all = len(physical_pluscode)
# virtual_opp_total_all = len(virtual_pluscode)
# hybrid_opp_total_all = len(hybrid_pluscode)

# Main trajectory stops
#traj_simple = pd.read_csv('./Data/Scenarios_Synthetic_Data.csv')

# Main and travel trajectory stops (inclusive of every street)
traj = pd.read_csv('../Data/Scenarios_Synthetic_Data_Trajectories.csv', index_col=0)
traj.drop(columns=['time'], inplace=True)
traj['person_id'] = traj['person_id'].astype(int)

# Create TrajectoryCollection object
collection = mpd.TrajectoryCollection(traj, 'person_id', t='datetime', x='longitude', y='latitude')

# Trajectories
trajectories = gpd.GeoDataFrame()

i = 0

for trajectory in collection.trajectories:
    # Calculate speed
    trajectory.add_speed(overwrite=True)
    
    # Determine direction of movement
    trajectory.add_direction(overwrite=True)
    
    # Parse time component (as datetime)
    trajectory.df["daytime"] = pd.to_datetime(trajectory.df.index)
    
    # Add to container
    trajectories = trajectories.append(trajectory.df)
    
    i+=1

# Reorder the data based on timestamp
trajectories = trajectories.sort_values(by="daytime").reset_index(drop=True)

# Add longitude and latitude back into data frame
trajectories["longitude"] = trajectories["geometry"].x
trajectories["latitude"] = trajectories["geometry"].y
# Sort trajectories by numerical order of person_id
trajectories.sort_values(by=['person_id', 'daytime'], inplace=True)

# Merge trajectories and individuals dataset so people's information can be visualized when hovered over in plots
trajectories = pd.merge(trajectories, individuals, left_on='person_id', right_on='person_id')

# Local counties layer
# Retrieve all points in the polygon of Knox County

# Load County Boundary GeoJSON
with open('../Data/Local_Counties_v2.geojson') as f:
    knox = json.load(f)

pts = []

# For each feature (e.g., county), retrieve all pairwise lon, lat of each point along the perimeter
# Store in pts list
for feature in knox['features']:
    pts.extend(feature['geometry']['coordinates'][0])    
    pts.append([None, None]) # Mark the end of a polygon   

# Separate into two different lists
knox_X, knox_Y = zip(*pts)
knox_Z = []
# Psuedo z-column
knox_Z += len(knox_X) * [dt(2022, 3, 10, 23, 59, 59)]

knox_bg = gpd.read_file('../Data/Knox_County_BG_Census.shp')

# Scale percentage values between 0 - 100
knox_bg_columns=['Unemply',
                 'NHSDplm',
                 'Ag65Old',
                 'Ag17Yng',
                 'DisblHH',
                 'SinglHH',
                 'Minorty',
                 'PrEngls',
                 'MltUnts',
                 'MobilHm',
                 'Crowdng',
                 'NoVehcl',
                 'GropQrt',
                 'SNAPBnf',
                 'NoCmptr',
                 'NIntrnt']

for c in knox_bg_columns:
    knox_bg[c] = knox_bg[c] * 100

knox_bg.rename(columns={'TotlPpE': 'Population',
                        'Incm_ME': 'Median Income $', 
                        'Unemply': 'Unemployment %',
                        'NHSDplm': 'No High School Diploma %',
                        'Ag65Old': 'Age 65 or Older %',
                        'Ag17Yng': 'Age 17 or Younger %',
                        'DisblHH': 'Households with Disabled Person(s) %',
                        'SinglHH': 'Households with Single Parent %',
                        'Minorty': 'Non-White Population %',
                        'PrEngls': 'Speaks English Less than well %',
                        'MltUnts': 'Multi-Unit Housing %',
                        'MobilHm': 'Mobile Home Housing %',
                        'Crowdng': 'Crowded Housing %',
                        'NoVehcl': 'Households without Vehicles %',
                        'GropQrt': 'People Living in Group Quarters %',
                        'SNAPBnf': 'People with SNAP Benefits %',
                        'NoCmptr': 'People without Computers %',
                        'NIntrnt': 'People without Internet %'},
                        inplace=True
              )



# Retrieve columns of Census data that users can select to visualize in a choropleth map
# Also add space-time prisms to 2-D Map
prisms = gpd.read_file('../Data/Scenario_Flexible_Space_Time_Prisms.shp', index_col=0)
prisms['free_time_start'] = pd.to_datetime(prisms['free_time_'])
prisms['free_time_end'] = pd.to_datetime(prisms['free_tim_1'])


knox_bg_cols = ['Select Block Group Choropleth Layer']
for i_bg, col_bg in enumerate(knox_bg.columns.values):
    if col_bg not in ['GEOID', 'NAME', 'geometry']:
        knox_bg_cols.append(col_bg)
knox_bg_cols.append('Space Time Prisms')


# Description and GitHub Code
with open("../Code/metadata.md", "r") as f:
    md = f.read()

modal_overlay = dbc.Modal(
    [
        dbc.ModalBody(html.Div([dcc.Markdown(md)], id="md")),
        dbc.ModalFooter(dbc.Button("Close", id="howto-close", className="howto-bn")),
    ],
    id="modal",
    size="lg",
)

button_howto = dbc.Button(
    "Learn more",
    id="howto-open",
    outline=True,
    color="info",
    # Turn off lowercase transformation for class .button in stylesheet
    style={"textTransform": "none"},
)

button_github = dbc.Button(
    "View Code on GitHub",
    outline=True,
    color="primary",
    href="https://github.com/jimmy-feng/Dissertation_App/tree/heroku",
    id="gh-link",
    style={"text-transform": "none"},
)

#############################################################################################
# FUNCTIONS FOR CREATING MAPS AND NETWORK DASHBOARD COMPONENTS
############################################################################################

# Establish color map for individuals
n_colors = len(sorted(individuals['person_id'].values))
colors = px.colors.sample_colorscale("turbo", [n/(n_colors -1) for n in range(n_colors)])
indiv_colors = dict(zip(sorted(individuals['person_id'].values), colors))
store_colors = {'Grocery store': '#4daf4a',
                'Discount store': '#ffff33',
                'Convenience store': '#984ea3',
                'Department store': '#377eb8', 
                'Ethnic grocery store':'#e41a1c',
                'Specialty food store': '#ff7f00',
                'Warehouse store': '#a65628'
                }

def rgb_to_hex(rgb_list: list):
    '''
    Convert list of strings of RGB values into list of strings of HEX codes
    '''
    # Compile regex pattern to extract the RGB values
    import re
    rgb_re = re.compile('\d{1,}')
    
    hexcolors = []
    # For each RGB string
    for n in rgb_list:
        # Find the corresponding R, G, and B values
        rgb_nums = rgb_re.findall(n)
        # Convert into HEX code
        hexcolors.append(f'#{int(rgb_nums[0]):02x}{int(rgb_nums[1]):02x}{int(rgb_nums[2]):02x}')
    return hexcolors

colors_hex = rgb_to_hex(colors)

def create_2d_map(choropleth_z, individuals_df, trajectories_df, stores_df, prisms_df): 
    ## 2-D MAP
    
    # Instantiate Map object built off of Plotly.graph_objects
    map_2 = go.Figure(go.Scattermapbox())
    #map_2 = leafmap.Map(center=(35.9875, -83.9420), zoom=8, basemap="open-street-map")
    map_2.update_layout(
        font=dict(family="Roboto"),
        mapbox_center=go.layout.mapbox.Center(lat=35.9875, lon=-83.9420),
        mapbox_zoom=8,
        #basemap='open-street-map'
    )
    # Add Choropleth layer
    if choropleth_z != 'Select Block Group Choropleth Layer':
        
        choro_gj = None
        choro_locs = None
        choro_z = None
        
        if choropleth_z == 'Space Time Prisms':
            choro_gj = json.loads(prisms_df.drop(['free_time_start', 'free_time_end'], axis=1).to_json())
            choro_locs = prisms_df.index
            choro_z = prisms_df['StoreOpps']
        else:
            choro_gj = json.loads(knox_bg.to_json())
            choro_locs = knox_bg.index
            choro_z = knox_bg[choropleth_z]
            
        map_2.add_trace(go.Choroplethmapbox(
                        geojson=choro_gj,
                        locations=choro_locs,
                        z=choro_z,
                        #customdata=
                        #colorbar_title=map_2d_dropdown_value,
                        colorbar_orientation='h',
                        colorbar_len=0.5,
                        colorbar_tickfont_color='black',
                        colorbar_thickness=10,
                        colorbar_tickfont_family='Roboto',
                        colorbar_y = 0,
                        colorbar_x = 0.3,
                        name=choropleth_z,
                        marker_opacity=0.5
                        #hovertemplate = '<br><b> ST-Prism:</b><extra></extra>%{text}',
        ))
        #map_2.set_layer_opacity(choropleth_z, opacity = 0.5)
        
    # Set layout parameters
    map_2.update_layout(
        mapbox_style = 'open-street-map',
        font=dict(size=12),
        mapbox_zoom = 9,
        mapbox_center = {'lat':35.99, 'lon':-83.9650},
    )       
    
    # Add activated trajectories in given timerange onto map
    for person in individuals_df['person_id'].unique():
        map_2.add_trace(go.Scattermapbox(
            mode = 'markers+lines',
            lon = trajectories[trajectories['person_id'] == person]['longitude'],
            lat = trajectories[trajectories['person_id'] == person]['latitude'],
            marker = {'size': 4, 'color': indiv_colors[person]},
            name = 'Person ' + str(person)
        ))
    
    # Default weight is 1000 and so setting the weight of trajectories to be larger than that means future undefined traces (e.g., stores) will be brought above
    map_2.update_traces(legendrank=1001, selector=dict(type='scattermapbox'))
    
    # Create graph objects figure of a scatter mapbox of stores
    for store_type in stores_df['Type'].unique():
        stores_df_type = stores_df[stores_df['Type'] == store_type]
        map_2.add_trace(go.Scattermapbox(
                lon = stores_df_type.Longitude, 
                lat = stores_df_type.Latitude,
                mode = 'markers',
                marker_color = store_colors[store_type],
                marker_size = 20,
                #color = 'Type',
                name = store_type,
                #size_max = 60,
                #zoom = 8,
                hovertemplate = '<br><b> Food Store:</b><extra></extra>%{text}',
                text='<br><b> Name:</b> ' + stores_df_type.Name + '<br><b> Address:</b> ' + stores_df_type.Address + '<br><b> Rating:</b> ' + stores_df_type.Rating.astype(str) + '<br><b> Price:</b> ' + stores_df_type.Price.astype(str) + '<br><b> Type:</b> ' + stores_df_type.Type,
           ))
    
    # Add graph objects as traces to map
    #map_2.add_traces(list(map_stores_filter.select_traces()))
    
    # Disable clicking of items in legend
    map_2.update_layout(
        legend = dict(
            font = dict(
                family = "Roboto"),
            itemclick = False,
            itemdoubleclick = False
        ),
        autosize=True,
        height=450,
        margin=dict(l=4, r=5, t=0, b=10),
    )
    
    return map_2


def create_3d_map(trajectories_df, stores_df, individuals_df_filter, individuals_df_unfilter):
    ## 3-D Plot
    map_3 = px.line_3d(trajectories_df,
                       x="longitude", y="latitude", z="daytime",
                       color='person_id', color_discrete_map=indiv_colors,                 
                       custom_data=['person_id',
                                    'age',
                                    'sex',
                                    'raceethnic',
                                    'incomeyear',
                                    'language',
                                    'dietarypref',
                                    'digitallit',
                                    'job',
                                    'housing',
                                    'housesize',
                                    'kidsathome',
                                    'marital',
                                    'travelmode',
                                    'physical',
                                    'snapbenefit',
                                    'cost_pref',
                                    'other_pref',
                                    'description'],
                       labels={'person_id': 'Person ID'}
    )
    # Edit trajectories
    map_3.update_traces(line=dict(width=5),
                        hovertemplate = 
                            "<br><b>Personal Description:</b>" + "<br>%{customdata[18]}"
                            # "<br><b>Person ID:</b> " + "%{customdata[0]}" +
                            # "<br><b>Age:</b> " + "%{customdata[1]}" +
                            # "<br><b>Sex:</b> " + "%{customdata[2]}" +
                            # "<br><b>Race/Ethnicity:</b> " + "%{customdata[3]}" +
                            # "<br><b>Annual Income:</b> " + "%{customdata[4]}" +
                            # "<br><b>Language:</b> " + "%{customdata[5]}" +
                            # "<br><b>Dietary Preferences:</b> " + "%{customdata[6]}" +
                            # "<br><b>Digital Literacy:</b> " + "%{customdata[7]}" +
                            # "<br><b>Job:</b> " + "%{customdata[8]}" +
                            # "<br><b>Housing:</b> " + "%{customdata[9]}" +
                            # "<br><b>Household Size:</b> " + "%{customdata[10]}" +
                            # "<br><b>Kids at home:</b> " + "%{customdata[11]}" +
                            # "<br><b>Marital Status:</b> " + "%{customdata[12]}" +
                            # "<br><b>Travel Mode:</b> " + "%{customdata[13]}" +
                            # "<br><b>Physical Disability:</b> " + "%{customdata[14]}" +
                            # "<br><b>SNAP Benefits:</b> " + "%{customdata[15]}" +
                            # "<br><b>Cost Preference:</b> " + "%{customdata[16]}" +
                            # "<br><b>Other Preferences:</b> " + "%{customdata[17]}"
                        )
    map_3.update_layout(
        hoverlabel=dict(
            font_family="Roboto",
            font_color="black"
        )
    # title_font_family="Times New Roman",
    # title_font_color="red",
    # legend_title_font_color="green"
)
    # Add county boundaries
    map_3.add_scatter3d(x=knox_X,
                      y=knox_Y,
                      z=knox_Z,
                      hovertemplate='County Boundary<extra></extra>',
                      mode='lines',
                      line_color='#999999',
                      line_width=1.5,
                      showlegend=False) 
    
    # Create psuedo z-field for stores
    stores_Z = list(len(stores_df) * [dt(2022, 3, 10, 23, 59, 59)])
    
    # Add stores to plot
    for store_type in stores_df['Type'].unique():
        stores_df_type = stores_df[stores_df.Type == store_type]
        map_3.add_trace(go.Scatter3d(
            x=stores_df_type['Longitude'],
            y=stores_df_type['Latitude'],
            z=stores_Z[0:len(stores_df_type)],
            mode='markers',
            marker_color=store_colors[store_type],
            hovertemplate = '<br><b> Food Store:</b><extra></extra>%{text}',
            text='<br><b> Name:</b> ' + stores_df_type.Name + '<br><b> Address:</b> ' + stores_df_type.Address + '<br><b> Rating:</b> ' + stores_df_type.Rating.astype(str) + '<br><b> Price:</b> ' + stores_df_type.Price.astype(str) + '<br><b> Type:</b> ' + stores_df_type.Type,
            showlegend = False
        ))
    # map_3.add_scatter3d(
    #     x = stores_df['Longitude'],
    #     y = stores_df['Latitude'],
    #     z = stores_Z,
    #     mode = 'markers',
    #     marker = dict(color=stores_df['Type'], color_discrete_map=store_colors,
    #     hovertemplate = '<br><b> Food Store:</b><extra></extra>%{text}',
    #     text='<br><b> Name:</b> ' + stores_df.Name + '<br><b> Address:</b> ' + stores_df.Address + '<br><b> Rating:</b> ' + stores_df.Rating.astype(str) + '<br><b> Price:</b> ' + stores_df.Price.astype(str) + '<br><b> Type:</b> ' + stores_df.Type,
    #     showlegend = False
    # )
    
    # Update layout
    map_3.update_layout(legend_traceorder='normal',
                      font=dict(family="Roboto"),
                      template = 'simple_white',
                      margin=dict(l=4, r=5, t=0, b=4),
                      autosize=True,
                      #width = 600,
                      height = 470
                     )    

    # Synchronize table and 3d plot
    # Users can both click/unclick individual legend traces AND query the table
    for idx_trace, r_trace in enumerate(map_3.data):
        if (idx_trace+1 not in individuals_df_filter['person_id'].unique()) & (idx_trace < len(individuals_df_unfilter['person_id'].unique())):
            r_trace.visible = 'legendonly'
            
    return map_3


# https://medium.com/plotly/introducing-dash-cytoscape-ce96cac824e4
#https://github.com/plotly/dash-cytoscape/blob/master/usage-stylesheet.py
def network_data(od_df, individuals_df, stores_df, stores_online_df):

    od_shop_mode = []

    # Only retain stores that can be visited and participated in given an individual's space-time constraints
    od_df_st = od_df[od_df['can_visit_spacetime']]    
    # Remove duplicate person - store entries
    od_condensed = od_df_st[['person_id', 'store_PlusCode', 'can_visit_spacetime']].drop_duplicates(['person_id', 'store_PlusCode'])
    
    # Dictionary of individuals and accessible physical, virtual, and hybrid options
    pvh_opps = {i:[0,0,0] for i in range(1,53)}
    
    stores_physical_pluscode = []
    stores_virtual_pluscode = []
    stores_hybrid_pluscode = []
    
    stores_modality = []
    
    # For every OD pair
    for i, r in od_condensed.iterrows():
        # If the person is digitally literate
        if (individuals.loc[r['person_id'] - 1, 'digitallit'] == 'yes'):
            # If the store has online services
            if (stores_df[stores_df['Shop_Online']]['PlusCode'] == r['store_PlusCode']).any():
                # The person can shop either in person or online, so we'll assign a hybrid mode
                od_shop_mode.append('Hybrid')
                
                # Add to hybrid counter for that person
                pvh_opps[r['person_id']][2] += 1
                
                # Add the Store PlusCode to a list which we'll use to track total number of accessible opportunities by shopping modality
                if (r['store_PlusCode'] not in stores_hybrid_pluscode): 
                    stores_hybrid_pluscode.append(r['store_PlusCode'])
                    if (r['store_PlusCode'] in stores_physical_pluscode):
                        stores_physical_pluscode.remove(r['store_PlusCode'])
                    
            # Otherwise, that person can only access in-person
            else:
                if (r['store_PlusCode'] not in stores_hybrid_pluscode) & (r['store_PlusCode'] not in stores_physical_pluscode):
                    stores_physical_pluscode.append(r['store_PlusCode'])
                
                # Assign a physical mode
                od_shop_mode.append('Physical')
                # Add to physical counter for that person
                pvh_opps[r['person_id']][0] += 1
                
                # if [r['store_PlusCode'], 'Hybrid'] not in store_modality:
                #     store_modality.append([r['store_PlusCode'], 'Hybrid'])
        # The person is not digitally literate so they definitely cannot access online
        else:
            od_shop_mode.append('Physical')
            pvh_opps[r['person_id']][0] += 1

            if (r['store_PlusCode'] not in stores_hybrid_pluscode) & (r['store_PlusCode'] not in stores_physical_pluscode):
                stores_physical_pluscode.append(r['store_PlusCode'])

    # Add the shopping mode back to the data frame
    od_condensed['Shop_Mode'] = od_shop_mode

    edges_temp = []

    # Identify virtual access-only options

    # For everyone who is digitally literate
    for i_pers, r_pers in individuals_df[individuals_df['digitallit'] == 'yes'].iterrows():
        # For every online store
        for so in stores_online_df['PlusCode']:
            # If there isn't an entry already in the od_condensed edge list of person_id, store_PlusCode, and Shop_Mode
            # We'll add a virtual connection to that store for that person
            if len(od_condensed[(od_condensed['person_id'] == r_pers['person_id']) & (od_condensed['store_PlusCode'] == so)]) == 0:
                edges_temp.append({'person_id':r_pers['person_id'], 'store_PlusCode': so, 'Shop_Mode': 'Virtual'})
                pvh_opps[r_pers['person_id']][1] += 1
                
                # If the Store PlusCode for a virtual shopping option isn't already in the physical, hybrid, or virtual lists, add it to the virtual list
                if (so not in stores_hybrid_pluscode) & (so not in stores_physical_pluscode) & (so not in stores_virtual_pluscode):
                    stores_virtual_pluscode.append(so)
            else:
                next

    edges_temp_df = pd.DataFrame(edges_temp)
    od_condensed = pd.concat([od_condensed, edges_temp_df], ignore_index=True)
    #od_condensed = od_condensed.sort_values(by=['person_id']).reset_index(drop=True)

    od_p_p = [{'person_id': 1, 'store_PlusCode': 18, 'Shop_Mode': 'Hybrid'},
              {'person_id': 18, 'store_PlusCode': 19, 'Shop_Mode': 'Hybrid'},
              {'person_id': 1, 'store_PlusCode': 44, 'Shop_Mode': 'Hybrid'},
              {'person_id': 44, 'store_PlusCode': 19, 'Shop_Mode': 'Hybrid'},
              {'person_id': 17, 'store_PlusCode': 35, 'Shop_Mode': 'Hybrid'},
              {'person_id': 16, 'store_PlusCode': 35, 'Shop_Mode': 'Hybrid'},
              {'person_id': 16, 'store_PlusCode': 17, 'Shop_Mode': 'Hybrid'}]
    
    # If an individual in the current individuals_df (after filtering) isn't in the person to person list of dicts, remove their OD flow since we're not examining that individual
    od_p_p = [lst for lst in od_p_p for pid in individuals_df['person_id'].unique() if pid in lst.values()]
    # Remove duplicates
    od_p_p = [dict(t) for t in {tuple(d.items()) for d in od_p_p}]      
    
    od_condensed = pd.concat([od_condensed, pd.DataFrame(od_p_p)], ignore_index=True).sort_values(by=['person_id']).reset_index(drop=True)
    
    nodes = set()
    cy_edges = []
    cy_nodes = []

    pvh_opps_df = pd.DataFrame.from_dict(pvh_opps, orient='index', columns=['PhysicalOpp', 'VirtualOpp', 'HybridOpp'])
    pvh_opps_df['TotalOpps'] = pvh_opps_df.sum(axis=1)
    
    for i, r in od_condensed.iterrows():
        
        # If the node ID is not in the nodes set
        if str(r['person_id']) not in nodes:
            
            # Add the node to nodes set
            nodes.add(str(r['person_id']))
        
            node_size = int(np.sqrt(1 + pvh_opps_df[pvh_opps_df.index == r['person_id']]['TotalOpps'].values[0]) * 2)
            id_label = f"Person {r['person_id']}"
            cy_nodes.append({'data': {'id': str(r['person_id']),
                                      'label': id_label,
                                      'node_size': node_size},
                             'classes': 'person'
                            }) 
        
        # If the node is a store and not already in the nodes set
        if (str(r['store_PlusCode']) not in nodes) & (str(r['store_PlusCode']).isdigit() == False):
            
            # Add the store node to the nodes set
            nodes.add(str(r['store_PlusCode']))
            people_to_store = od_condensed[od_condensed['store_PlusCode'] == r['store_PlusCode']]['person_id'].nunique()
            node_size = int(np.sqrt(1 + people_to_store) * 3)
            id_label = f"{r['store_PlusCode']}" # if r['store_PlusCode'].isdigit() else f"{r['store_PlusCode']}"
            cy_nodes.append({'data': {'id': str(r['store_PlusCode']), 'label': stores[stores['PlusCode'] == r['store_PlusCode']]['Name'].values[0] + ' - ' + r['store_PlusCode'], 'node_size': node_size}, 'classes': 'store'})
                        
        class_color = 'self'
        
        if r['Shop_Mode'] == 'Hybrid':
            class_color = 'hybrid'
        elif r['Shop_Mode'] == 'Physical':
            class_color = 'physical'
        elif r['Shop_Mode'] == 'Virtual':
            class_color = 'virtual'
            
        cy_edges.append({
            'data': {
                'source': str(r['person_id']),
                'target': str(r['store_PlusCode'])
            },
            'classes': class_color
        })
      
    for p in individuals['person_id'].unique():
        if not any(n['data']['id'] == str(p) for n in cy_nodes):
            id_label = 'Person ' + str(p)
            cy_nodes.append({'data': {'id': str(p), 'label': id_label, 'node_size': 1}, 'classes': 'person'})

    for s in stores['PlusCode'].unique():
        if not any(n['data']['id'] == str(s) for n in cy_nodes):
            if s.isdigit():
                cy_nodes.append({'data': {'id': str(s), 'label': f'Person {str(p)}', 'node_size': 1}, 'classes': 'store'})
            else:
                id_label = stores[stores['PlusCode'] == s]['Name'].values[0] + ' - ' + str(s)
                cy_nodes.append({'data': {'id': str(s), 'label': id_label, 'node_size': 1}, 'classes': 'store'})   
            
    return cy_edges, cy_nodes, pvh_opps, set(stores_physical_pluscode), set(stores_virtual_pluscode), set(stores_hybrid_pluscode)

############################################################################################
# Create 2D and 3D Map and network data
#map_2d = create_2d_map('Select Block Group Choropleth Layer', individuals, trajectories, stores) 

map_2d = create_2d_map('Select Block Group Choropleth Layer', individuals, trajectories, stores, prisms) 
map_3d = create_3d_map(trajectories, stores, individuals, individuals)
cy_edges, cy_nodes, all_opps, stores_physical_pluscode, stores_virtual_pluscode, stores_hybrid_pluscode = network_data(od, individuals, stores, stores_online)

# Total accessible opportunities by shopping modality
physical_opp_total_all = len(stores_physical_pluscode)
virtual_opp_total_all = len(stores_virtual_pluscode)
hybrid_opp_total_all = len(stores_hybrid_pluscode)

# Join actual opportunities by modality to individuals data-frame
all_opps_df = pd.DataFrame.from_dict(all_opps, orient='index', columns=['PhysicalOpp', 'VirtualOpp', 'HybridOpp'])
individuals = pd.merge(individuals.drop(columns=['PhysicalOpp', 'VirtualOpp']), all_opps_df, left_on='person_id', right_on=all_opps_df.index, how='left')
#############################################################################################

#############################################################################################
# Set up parameters for dashboard

# CSS Stylesheet for the Dashboard HTML
external_stylesheets = ['https://use.fontawesome.com/releases/v6.0.0/css/all.css', dbc.themes.ZEPHYR]#, 'https://fonts.googleapis.com/css2?family=Playfair+Display&display=swap']#, 'https://codepen.io/chriddyp/pen/bWLwgP.css']

# Default Stylesheet for Network Graph
edge_colors = {'physical': '#5cb85c', 'virtual': '#0275d8', 'hybrid': 'yellow', 'self': 'grey'}
cytoscape_stylesheet = []
default_stylesheet = [
    {
        "selector": 'node',
        'style': {
            "opacity": 0.95,
            "width": "data(node_size)",
            "height": "data(node_size)"
        }
    },
    {
        "selector": 'edge',
        'style': {
            "curve-style": "bezier",
            "opacity": 0.65
        }
    },
    {
        'selector': '.hybrid',
        'style': {
            'background-color': 'yellow',
            'line-color': 'yellow'
        }
    },
    {
        'selector': '.physical',
        'style': {
            'background-color': '#5cb85c',
            'line-color': '#5cb85c'
        }
    },
    {
        'selector': '.virtual',
        'style': {
            'background-color': '#0275d8',
            'line-color': '#0275d8'
        }
    },
    {
        'selector': '.person',
        'style': {
            'shape': 'pentagon',
            "width": "data(node_size)",
            "height": "data(node_size)"
        }
    },  {
        'selector': '.store',
        'style': {
            'shape': 'ellipse',
            "width": "data(node_size)",
            "height": "data(node_size)"
        }    
    },  {
        'selector': '.self',
        'style': {
            'background-color': 'white',
            'line-color': 'white',
            "width": "data(node_size)",
            "height": "data(node_size)",
            "opacity": 0
        }    
    }
]
for n in cy_nodes:
    if n['classes'] == 'person':
        default_stylesheet.append({'selector': 'node[id = "{}"]'.format(n['data']['id']),
                                    'style': {
                                        'background-color': indiv_colors[int(n['data']['id'])],
                                        "opacity": 0.95,
                                        "width": "data(node_size)",
                                        "height": "data(node_size)"
                                    }   
                            })
    elif n['classes'] == 'store':
        default_stylesheet.append({'selector': 'node[id = "{}"]'.format(n['data']['id']),
                                    'style': {
                                        'background-color': store_colors[stores[stores['PlusCode'] == n['data']['id']]['Type'].values[0]],
                                        "opacity": 0.95,
                                        "width": "data(node_size)",
                                        "height": "data(node_size)"
                                    }   
                            })        

styles = {
    'json-output': {
        'overflow-y': 'scroll',
        'height': 'calc(50% - 25px)',
        'border': 'thin lightgrey solid'
    },
    'tab': {
        'height': 'calc(98vh - 105px)'
    }
}

# Table Tabs Styles
tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'margin': '3px',
#    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': '#c2fabe',
    'color': 'black',
    'padding': '6px',
    'margin': '3px',
}


# Create dashboard
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
#app.css.config.serve_locally = True
# Title of app
app.title = 'Prototype GIS for Access in a Physical-Virtual World'

PAGE_SIZE = 10

app.layout = dbc.Container([
    
    dbc.Navbar(
        dbc.Container([
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                [
                                    html.H4(f'Multidimensional Multispace GIS for Access'),
                                ],
                                id='app-title',
                            )
                        ],
                        md=True,
                        align='center',
                    ),
                ],
                align='center'
            ),
            
            dbc.Row([
                    dbc.Col([
                            #dbc.CardHeader(html.H5(f"Total Food Stores | {len(stores) + virtual_opp_total_all}", style={'textAlign': 'center', 'margin-top': '10px'})),
                            dbc.CardGroup([
                                        dbc.Card(
                                            dbc.CardBody([
                                                    #html.Span(),
                                                    #html.P("Physical", className="card-title", style={'color': 'text-success'}),
                                                    #html.P(opps_phys, className="card-text",),
                                                    #html.I(className="fas fa-thin fa-store"),
                                                    dbc.Button(
                                                        [
                                                            "Total Food Stores",
                                                            dbc.Badge(
                                                                children=f"{len(stores) + virtual_opp_total_all}",
                                                                color="danger",
                                                                pill=True,
                                                                text_color="white",
                                                                className="position-absolute top-0 start-100 translate-middle",
                                                                id='total_counter',
                                                                style={'justifyContent': 'center'}
                                                            ),
                                                        ],
                                                        color="light",
                                                        disabled=True,
                                                        className = 'position-relative'
                                                    ),
                                                ],
                                                className = 'align-self-center'
                                            )
                                        ),                                
                                        dbc.Card(
                                            dbc.CardBody([
                                                    #html.Span(),
                                                    #html.P("Physical", className="card-title", style={'color': 'text-success'}),
                                                    #html.P(opps_phys, className="card-text",),
                                                    #html.I(className="fas fa-thin fa-store"),
                                                    dbc.Button(
                                                        [
                                                            "Physical",
                                                            dbc.Badge(
                                                                children=physical_opp_total_all,
                                                                color="danger",
                                                                pill=True,
                                                                text_color="white",
                                                                className="position-absolute top-0 start-100 translate-middle",
                                                                id='physical_counter',
                                                                style={'justifyContent': 'center'}
                                                            ),
                                                        ],
                                                        color="success",
                                                        disabled=True,
                                                        className = 'position-relative'
                                                    ),
                                                ],
                                                className = 'align-self-center'
                                            )
                                        ),
                                        dbc.Card(
                                            dbc.CardBody([
                                                    # html.P("Virtual", className="card-title", style={'color': 'text-primary'}),
                                                    # html.P(opps_virt, className="card-text",),
                                                    # html.I(className="fas fa-thin fa-store"),
                                                    dbc.Button(
                                                         [
                                                             "Virtual",
                                                             dbc.Badge(
                                                                 children=virtual_opp_total_all,
                                                                 color="danger",
                                                                 pill=True,
                                                                 text_color="white",
                                                                 className="position-absolute top-0 start-100 translate-middle",
                                                                 id='virtual_counter',
                                                                 style={'justifyContent': 'center'}
                                                             ),
                                                         ],
                                                         color="primary",
                                                         disabled=True,
                                                         className = 'position-relative'
                                                    ),
                                                ],
                                                className = 'align-self-center'
                                            )
                                        ),
                                        dbc.Card(
                                            dbc.CardBody([
                                                    #html.Span(),
                                                    #html.P("Physical", className="card-title", style={'color': 'text-success'}),
                                                    #html.P(opps_phys, className="card-text",),
                                                    #html.I(className="fas fa-thin fa-store"),
                                                    dbc.Button(
                                                        [
                                                            "Hybrid",
                                                            dbc.Badge(
                                                                children=hybrid_opp_total_all,
                                                                color="danger",
                                                                pill=True,
                                                                text_color="white",
                                                                className="position-absolute top-0 start-100 translate-middle",
                                                                id='hybrid_counter',
                                                                style={'justifyContent': 'center'}
                                                            ),
                                                        ],
                                                        color="warning",
                                                        disabled=True,
                                                        className = 'position-relative'
                                                    ),
                                                ],
                                                className = 'align-self-center'
                                            )
                                        ),
                                    ]
                                )
                        ]),
            ]),
            
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.NavbarToggler(id='navbar-toggler'),
                            dbc.Collapse(
                                dbc.Nav(
                                    [
                                        dbc.NavItem(button_howto, style={'whiteSpace': 'nowrap', 'margin-bottom':'7px'}),
                                        dbc.NavItem(button_github, style={'whiteSpace': 'nowrap'}),
                                    ],
                                    navbar=True,
                                    fill=True,
                                    vertical=True,
                                    
                                ),
                                id='navbar-collapse',
                                navbar=True,
                            ),
                            modal_overlay,
                        ],
                        md=2,
                    ),
                ],
                align='center',
            ),
        ],
        fluid=True,
        ),
        color='light',
        sticky='top',
    ),
    
    # dbc.Row([
        # dbc.Col([
        #     dbc.CardHeader(html.H5(f"Total Food Stores | {len(stores) + virtual_opp_total_all}", style={'textAlign': 'center', 'margin-top': '10px'})),
        #     dbc.CardGroup(
        #             [
        #                 dbc.Card(
        #                     dbc.CardBody(
        #                         [
        #                             #html.Span(),
        #                             #html.P("Physical", className="card-title", style={'color': 'text-success'}),
        #                             #html.P(opps_phys, className="card-text",),
        #                             #html.I(className="fas fa-thin fa-store"),
        #                             dbc.Button(
        #                                 [
        #                                     "Physical",
        #                                     dbc.Badge(
        #                                         children=physical_opp_total_all,
        #                                         color="danger",
        #                                         pill=True,
        #                                         text_color="white",
        #                                         className="position-absolute top-0 start-100 translate-middle",
        #                                         id='physical_counter',
        #                                         style={'justifyContent': 'center'}
        #                                     ),
        #                                 ],
        #                                 color="success",
        #                                 disabled=True,
        #                                 className = 'position-relative'
        #                             ),
        #                         ],
        #                         className = 'align-self-center'
        #                     )
        #                 ),
        #                 dbc.Card(
        #                     dbc.CardBody(
        #                         [
        #                             # html.P("Virtual", className="card-title", style={'color': 'text-primary'}),
        #                             # html.P(opps_virt, className="card-text",),
        #                             # html.I(className="fas fa-thin fa-store"),
        #                             dbc.Button(
        #                                  [
        #                                      "Virtual",
        #                                      dbc.Badge(
        #                                          children=virtual_opp_total_all,
        #                                          color="danger",
        #                                          pill=True,
        #                                          text_color="white",
        #                                          className="position-absolute top-0 start-100 translate-middle",
        #                                          id='virtual_counter',
        #                                          style={'justifyContent': 'center'}
        #                                      ),
        #                                  ],
        #                                  color="primary",
        #                                  disabled=True,
        #                                  className = 'position-relative'
        #                             ),
        #                         ],
        #                         className = 'align-self-center'
        #                     )
        #                 ),
        #                 dbc.Card(
        #                     dbc.CardBody(
        #                         [
        #                             #html.Span(),
        #                             #html.P("Physical", className="card-title", style={'color': 'text-success'}),
        #                             #html.P(opps_phys, className="card-text",),
        #                             #html.I(className="fas fa-thin fa-store"),
        #                             dbc.Button(
        #                                 [
        #                                     "Hybrid",
        #                                     dbc.Badge(
        #                                         children=hybrid_opp_total_all,
        #                                         color="danger",
        #                                         pill=True,
        #                                         text_color="white",
        #                                         className="position-absolute top-0 start-100 translate-middle",
        #                                         id='hybrid_counter',
        #                                         style={'justifyContent': 'center'}
        #                                     ),
        #                                 ],
        #                                 color="warning",
        #                                 disabled=True,
        #                                 className = 'position-relative'
        #                             ),
        #                         ],
        #                         className = 'align-self-center'
        #                     )
        #                 ),
        #             ]
        #         )
        # ], width = 4)
        # dbc.Col([
        #     html.I(className="fas fa-thin fa-store"),
        # ], width = 1),
        # dbc.Col([
        #     html.I(className="fas fa-shield-alt"),
        # ], width = 1),
    # ]),
    
    dbc.Row([
        dbc.Col([ # 3D Line Plot of Trajectories
            html.H5('2D Map of Food Stores and People', style={'textAlign': 'center', 'margin': '3px 0px 0px 0px'}),
            dcc.Graph(
                id = 'table-paging-with-map',
                style={'height': '51vh'},#'width': '100%', 'height': '100%'},
                figure = map_2d,
                config={"displaylogo": False},
                ),
            dbc.Row([
                dbc.Col([
                    dash_datetimepicker.DashDatetimepicker(
                        id = "input-range",
                        endDate = trajectories['daytime'].max(),
                        startDate = trajectories['daytime'].min(),
                        utc=False,
                        locale="en_US"),
                    
                    html.Div(id="output-range", style={'height': '1vh'}),
                ], style={'width': '60%'}), 
                dbc.Col([
                    dcc.Dropdown(
                        id='map_2d_dropdown',
                        options=[{'label': k, 'value': k} for k in knox_bg_cols],
                        optionHeight=70,
                        value=knox_bg_cols[0],
                        clearable=False,
                        style={'height': '1vh'},
                        ),
                    ], style={'width': '50%'})
                ], className="h-5")
            ],
            width = 6,
            style={'border': '1px solid', 'height': '60vh', 'display': 'inline-block'}),
        
        dbc.Col([
            html.H5('3D Space-Time Plot of Human Trajectories', style={'textAlign': 'center', 'margin': '3px 0px 0px 0px'}),
            dcc.Graph(
                id = 'map-3d',
                figure = map_3d,
                style={'height': '56vh'},
                config={"displaylogo": False},
                ),
            ],
            width = 6,
            style={'border': '1px solid', 'height': '60vh', 'display': 'inline-block'})    
        ]),

    #html.Hr(),    
    
    dbc.Row([
        dbc.Col([
            dbc.Col([
                html.H5('Food Network', style={'textAlign': 'center', 'margin': '3px 0px 0px 0px'}),
                cyto.Cytoscape(
                    id='cytoscape',
                    elements=cy_edges + cy_nodes,
                    style={'height': '53vh'}, #'width': '100%'
                ),
            ], width = 10, style={'display': 'inline-block', 'align-items': 'center', 'justify-content': 'center'}),
            dbc.Col([

                html.B('Layout', style={'textAlign': 'center', 'margin': '4px'}),
                dcc.Dropdown(
                    id='dropdown-layout',
                    options=drc.DropdownOptionsList(
                        'random',
                        'grid',
                        'circle',
                        'concentric',
                        'breadthfirst',
                        'cose'
                    ),
                    optionHeight=25,
                    value='concentric',
                    clearable=False,
                    style={'width': '8vw', 'height': '3vh', 'margin': '4px', 'align-items': 'center', 'justify-content': 'center'},
                    ),
                
                html.Hr(),
                
                html.B('Person Shape', style={'textAlign': 'center', 'margin': '4px', 'justify-content': 'center'}),
                dcc.Dropdown(
                    id='dropdown-person-shape',
                    options=drc.DropdownOptionsList(
                        'ellipse',
                        'triangle',
                        'rectangle',
                        'diamond',
                        'pentagon',
                        'hexagon',
                        'heptagon',
                        'octagon',
                        'star',
                        'polygon',
                    ),
                    optionHeight=25,
                    value='pentagon',
                    clearable=False,
                    style={'width': '8vw', 'height': '3vh', 'margin': '4px', 'align-items': 'center', 'justify-content': 'center'},
                    ),

                html.Hr(),                
              
                html.B('Store Shape', style={'textAlign': 'center', 'justify': 'center', 'margin': '4px'}),
                dcc.Dropdown(
                    id='dropdown-store-shape',
                    options=drc.DropdownOptionsList(
                        'ellipse',
                        'triangle',
                        'rectangle',
                        'diamond',
                        'pentagon',
                        'hexagon',
                        'heptagon',
                        'octagon',
                        'star',
                        'polygon',
                    ),
                    optionHeight=25,
                    value='ellipse',
                    clearable=False,
                    style={'width': '8vw', 'height': '3vh', 'margin': '4px', 'align-items': 'center', 'justify-content': 'center'},
                ),

                html.Hr(),                

                dbc.Button("Reset Network",
                           id='reset-network',
                           outline=True,
                           color="warning",
                           className="me-1",
                           style={'width': '7.5vw', 'margin': '4px', 'align-items': 'center', 'justify-content': 'center', 'textAlign': 'center', 'padding': '2px'},
                          ),

                html.Hr(),                

                html.B('Line Legend', style={'textAlign': 'center', 'justify-content': 'center', 'align': 'center', 'margin': '4px'}),
                html.P('Physical', style={'color': 'black', 'margin': '4px', 'textAlign': 'center', 'backgroundColor': '#5cb85c', 'width': '6vw', 'height': '2.5vh', 'justify-content': 'center', 'align': 'center'}),
                html.P('Virtual', style={'color': 'black', 'margin': '4px', 'textAlign': 'center','backgroundColor': '#0275d8', 'width': '6vw', 'height': '2.5vh', 'justify-content': 'center', 'align': 'center'}),
                html.P('Hybrid', style={'color': 'black', 'margin': '4px', 'textAlign': 'center', 'backgroundColor': 'yellow', 'width': '6vw', 'height': '2.5vh', 'justify-content': 'center', 'align': 'center'})

                
            ], width=2, style={'display': 'inline-block', 'align': 'start', 'justify-content': 'center'})
        ], width = 6, style={'border': '1px solid', 'height': '59vh', 'display': 'inline-block', 'align-items': 'center', 'justify-content': 'space-evenly'}),
        
        dbc.Col([
            html.H5('Socioeconomic, Demographic, and Perceived Data Tables', style={'textAlign': 'center', 'margin': '3px 0px 0px 0px'}),
            dcc.Tabs([
                dcc.Tab(label='Table: Individuals',
                        style=tab_style,
                        selected_style=tab_selected_style,
                        children=[
                    dash_table.DataTable(
                        id = 'individuals-sorting-filtering',
                        #columns = [{"name": i, "id": i} for i in sorted(individuals.columns)],
                        columns = 
                        [
                            {'name': 'Person ID', 'id': individuals.columns[0], 'type': 'numeric'},
                            {'name': 'Age', 'id': individuals.columns[1], 'type': 'numeric'},
                            {'name': 'Sex', 'id': individuals.columns[2], 'type': 'text'},
                            {'name': 'Race/Ethnicity', 'id': individuals.columns[3], 'type': 'text'},
                            {'name': 'Annual Income', 'id': individuals.columns[4], 'type': 'numeric'},
                            {'name': 'Language', 'id': individuals.columns[5], 'type': 'numeric'},
                            {'name': 'Dietary Preferences', 'id': individuals.columns[6], 'type': 'text'},
                            {'name': 'Digital Literacy', 'id': individuals.columns[7], 'type': 'text'},
                            {'name': 'Job', 'id': individuals.columns[8], 'type': 'text'},
                            {'name': 'Housing', 'id': individuals.columns[9], 'type': 'numeric'},
                            {'name': 'Household Size', 'id': individuals.columns[10], 'type': 'numeric'},
                            {'name': 'Kids at home', 'id': individuals.columns[11], 'type': 'numeric'},
                            {'name': 'Marital Status', 'id': individuals.columns[12], 'type': 'text'},
                            {'name': 'Travel Modes', 'id': individuals.columns[13], 'type': 'text'},
                            {'name': 'Physical Disability', 'id': individuals.columns[14], 'type': 'text'},
                            {'name': 'SNAP Benefits', 'id': individuals.columns[15], 'type': 'text'},
                            {'name': 'Cost Preference', 'id': individuals.columns[16], 'type': 'text'},
                            {'name': 'Other Preferences', 'id': individuals.columns[17], 'type': 'text'},
                            {'name': 'Dimensions', 'id': individuals.columns[18], 'type': 'text'},
                            {'name': 'Physical Opportunities', 'id': individuals.columns[20], 'type': 'numeric'},
                            {'name': 'Virtual Opportunities', 'id': individuals.columns[21], 'type': 'numeric'},
                            {'name': 'Hybrid Opportunities', 'id': individuals.columns[22], 'type': 'numeric'},                    

                        ],
                        style_header={'backgroundColor': '#25597f', 'color': 'white', "fontWeight": "bold",},
                        style_cell={'fontSize':14, 'font-family':'Roboto'},
                        style_as_list_view=True,
                        page_current = 0,
                        page_size = PAGE_SIZE,
                        page_action = 'custom',

                        filter_action = 'custom',
                        filter_query = '',

                        sort_action = 'custom',
                        sort_mode = 'multi',
                        sort_by = []
                        )
                ]),
                dcc.Tab(label='Table: Food Stores',
                        style=tab_style,
                        selected_style=tab_selected_style,
                        children=[
                    dash_table.DataTable(
                        id = 'table-sorting-filtering',
                        # or columns = [{"name": i, "id": i} for i in sorted(stores.columns)],
                        columns = 
                        [
                            {'name': 'Store Name', 'id': stores_table_columns[0], 'type': 'text'},
                            {'name': 'Rating', 'id': stores_table_columns[1], 'type': 'numeric'},
                            {'name': 'Price', 'id': stores_table_columns[2], 'type': 'text'},
                            {'name': 'Type', 'id': stores_table_columns[3], 'type': 'text'},
                            {'name': 'Specific Type', 'id': stores_table_columns[4], 'type': 'text'},
                            {'name': 'Convenience', 'id': stores_table_columns[5], 'type': 'numeric'},
                            {'name': 'Checkout Process', 'id': stores_table_columns[6], 'type': 'numeric'},
                            {'name': 'Employees', 'id': stores_table_columns[7], 'type': 'numeric'},
                            {'name': 'Food Quality', 'id': stores_table_columns[8], 'type': 'numeric'},
                            {'name': 'Food Variety', 'id': stores_table_columns[9], 'type': 'numeric'},
                            {'name': 'In-Store Shopping', 'id': stores_table_columns[10], 'type': 'text'},
                            {'name': 'Online Shopping', 'id': stores_table_columns[11], 'type': 'text'},
                            {'name': 'Delivery', 'id': stores_table_columns[12], 'type': 'text'},
                            {'name': 'Curbside Pickup', 'id': stores_table_columns[13], 'type': 'text'},
                            {'name': 'Store Pickup', 'id': stores_table_columns[14], 'type': 'text'},
                            {'name': 'Drive Thru', 'id': stores_table_columns[15], 'type': 'text'},
                            {'name': 'No-Contact Delivery', 'id': stores_table_columns[16], 'type': 'text'},
                            {'name': 'Same-Day Delivery', 'id': stores_table_columns[17], 'type': 'text'},
                            {'name': 'Masks Required', 'id': stores_table_columns[18], 'type': 'text'},
                            {'name': 'Great Service', 'id': stores_table_columns[19], 'type': 'text'},
                            {'name': 'Wheelchair Accessible', 'id': stores_table_columns[20], 'type': 'text'},
                            {'name': 'Good for Quick Visit', 'id': stores_table_columns[21], 'type': 'text'},
                            {'name': 'Organic Food', 'id': stores_table_columns[22], 'type': 'text'},
                            {'name': 'Prepared Food', 'id': stores_table_columns[23], 'type': 'text'},
                            {'name': 'Accepts Check', 'id': stores_table_columns[24], 'type': 'text'},
                            {'name': 'Accepts Debit Card', 'id': stores_table_columns[25], 'type': 'text'},
                            {'name': 'Accepts NFC Mobile Payment', 'id': stores_table_columns[26], 'type': 'text'},
                            {'name': 'Accepts SNAP/EBT', 'id': stores_table_columns[27], 'type': 'text'},
                            {'name': 'Accepts Credit Card', 'id': stores_table_columns[28], 'type': 'text'},
                            {'name': 'Restroom', 'id': stores_table_columns[29], 'type': 'text'},
                            {'name': 'LGBTQ+ Friendly', 'id': stores_table_columns[30], 'type': 'text'},
                            {'name': 'Family Friendly', 'id': stores_table_columns[31], 'type': 'text'},
                            {'name': 'Longitude', 'id': stores_table_columns[32], 'type': 'text'},
                            {'name': 'Latitude', 'id': stores_table_columns[33], 'type': 'text'},
                            {'name': 'Address', 'id': stores_table_columns[34], 'type': 'text'},
                            {'name': 'Plus Code', 'id': stores_table_columns[35], 'type': 'text'}
                        ],
                        #data = stores[stores_table_columns].to_dict('records'),
                        style_header={'backgroundColor': '#25597f', 'color': 'white', "fontWeight": "bold",},
                        style_cell={'fontSize':14, 'font-family':'Roboto'},
                        style_as_list_view=True,
                        page_current = 0,
                        page_size = PAGE_SIZE,
                        page_action = 'custom',

                        filter_action = 'custom',
                        filter_query = '',

                        sort_action = 'custom',
                        sort_mode = 'multi',
                        sort_by = []
                        )                            
                ]),
            ], style=tabs_styles),
        ], width = 6, style = {'height': '59vh', 'border': '1px solid', 'overflowY': 'scroll'})
    ]),
], fluid=True)


operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]

def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


keys = trajectories['person_id'].unique()
legend_tracker = dict(zip(keys, [True] * len(keys)))
keys_stores = stores['Type'].unique()
legend_tracker_stores = dict(zip(keys_stores, [True] * len(keys_stores)))


@app.callback(
    # Change output table, 2-D map, and 3-D line plot
    # return objects in the order each Output is listed
    Output('individuals-sorting-filtering', 'data'),
    Output('table-sorting-filtering', 'data'),
    Output('table-paging-with-map', 'figure'),
    Output('map-3d', 'figure'),
    Output('physical_counter', 'children'),
    Output('virtual_counter', 'children'),
    Output('hybrid_counter', 'children'),
    Output('cytoscape', 'elements'),
    Input('individuals-sorting-filtering', 'page_current'),
    Input('individuals-sorting-filtering', 'page_size'),
    Input('individuals-sorting-filtering', 'sort_by'),
    Input('individuals-sorting-filtering', 'filter_query'),
    Input('table-sorting-filtering', 'page_current'),
    Input('table-sorting-filtering', 'page_size'),
    Input('table-sorting-filtering', 'sort_by'),
    Input('table-sorting-filtering', 'filter_query'),
    Input('map_2d_dropdown', 'value'),
    Input('map-3d', 'restyleData'),
    Input('map-3d', 'clickData'),
    #Input('table-paging-with-map', 'restyleData'),
    Input('input-range', 'startDate'),
    Input('input-range', 'endDate'),
    # Input('table-toggle', 'n_clicks'),
    # Input('map-3d', 'clickData')
)
def update_table_map(page_current_ind, page_size_ind, sort_by_ind, filter_query_ind, page_current, page_size, sort_by, filter_query, map_2d_dropdown_value, restyleData3d, clickData3d, startDate, endDate):

    # if clickData:
    #     person_id = clickData['points'][0]['hovertext']
    #     unique_storeplus = list(od[(od['person_id'] == person_id) & (od['can_visit_spacetime'])]['store_PlusCode'].unique())
    #     stores_person = stores[stores['PlusCode'].isin(unique_storeplus)]
          
    
    # Track which person trajectories are activated in the 3d Plot
    # Users can click each trace in the legend to activate/deactivate them
    if restyleData3d is not None:
        edits, indices = restyleData3d
        try:
            # The length of indices is equal to one if we only select/unselect one trace
            if len(indices) == 1:
                for visible, index in zip(edits['visible'], indices):
                    if visible == 'legendonly':
                        # person_id starts from 1, not 0
                        legend_tracker[index+1] = False
                    else:
                        # person_id starts from 1, not 0
                        legend_tracker[index+1] = True
            # Otherwise, the length of indices will be all traces
            else:
                # edits['visible'] contains values for each trace key
                # values are either True or 'legendonly'
                # True means that the trace is activated
                # 'legendonly' means that the trace is not activated
                for position, item in enumerate(edits['visible'][:len(keys)]):
                    # If the trace is not activated
                    if item == 'legendonly':
                        # person_id starts from 1, not 0
                        # In the person_id legend tracker, set the person_id to False
                        legend_tracker[position+1] = False
                    elif item == True or item == 'True':
                        # person_id starts from 1, not 0
                        # Otherwise, the trace is activated so set the person_id to True
                        legend_tracker[position+1] = True
        except KeyError:
            pass    
        
    # Retrieve all unique person_id's of activated trajectories as a list we'll pass to the 'od' data-frame as well to the accompanying attribute table
    trajectories_on = [k for k,v in legend_tracker.items() if v == True]    

    
    
    # INDIVIDUALS TABLE
    # Enable filtering
    filtering_expressions_ind = filter_query_ind.split(' && ')
    individuals_filter = individuals.copy()
    individuals_filter = individuals_filter[individuals_filter['person_id'].isin(trajectories_on)]
    for filter_part in filtering_expressions_ind:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            individuals_filter = individuals_filter.loc[getattr(individuals_filter[col_name], operator)(filter_value)]
        elif operator == 'contains':
            individuals_filter = individuals_filter.loc[individuals_filter[col_name].str.contains(filter_value, na=False)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            individuals_filter = individuals_filter.loc[individuals_filter[col_name].str.startswith(filter_value, na=False)]

            
    if len(sort_by):
        individuals_filter = individuals_filter.sort_values(
            [col['column_id'] for col in sort_by_ind],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by_ind
            ],
            inplace=False
        )


    # Datetimepicker has some issues with setting UTC timezone
    # Convert all datetime objects from the timerange picker to be aligned in the same timezone with the times in the trajectories and stores data-frames
    if pd.to_datetime(startDate, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce').tz == None:
        startDate = pd.to_datetime(startDate, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce')
    else:
        startDate = pd.to_datetime(startDate, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce').tz_convert('US/Eastern').replace(tzinfo=None)

    
    if pd.to_datetime(endDate, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce').tz == None:
        endDate = pd.to_datetime(endDate, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce')
    else:
        endDate = pd.to_datetime(endDate, format = '%Y-%m-%d %H:%M:%S', errors = 'coerce') .tz_convert('US/Eastern').replace(tzinfo=None) 

    # Retrieve all store PlusCodes as a list if they can be reached by anyone in the activated trajectories given their space-time constraints & given the set time range
    # Condition 1: A person's beginning time availability has to be later than or equal to the start date of the timerange picker
    # Condition 2: A person's ending time availability has to be earlier than or equal to the end date of the timerange picker
    # Condition 3: A person has enough time for travel and activity to visit a specific store (i.e. they have enough time given their space-time constraints)
    # Condition 4: A person's trajectory has to be visible/activated in the 3d-plot
    unique_storeplus = list(od[(od['free_time_start'] >= startDate) & (od['free_time_end'] <= endDate) & (od['can_visit_spacetime']) & (od['person_id'].isin(individuals_filter['person_id'].unique()))]['store_PlusCode'].unique())

    # # Track which stores are activated in the 2d Map
    # # Users can click each type of store in the legend to activate/deactivate them
    # if restyleData2d is not None:
    #     edits_2d, indices_2d = restyleData2d
    #     try:
    #         # The length of indices is equal to one if we only select/unselect one trace
    #         if len(indices_2d) == 1:
    #             for visible_2d, index_2d in zip(edits_2d['visible'], indices_2d):
    #                 if visible_2d == 'legendonly':
    #                     legend_tracker_stores[list(legend_tracker_stores)[index_2d]] = False
    #                 else:
    #                     legend_tracker_stores[list(legend_tracker_stores)[index_2d]] = True
    #         # Otherwise, the length of indices will be all traces
    #         else:
    #             # edits_2d['visible'] contains values for each legend group
    #             # values are either True or 'legendonly'
    #             # True means that the legend group is activated
    #             # 'legendonly' means that the legend group is not activated
    #             for position, item in enumerate(edits_2d['visible'][:len(keys_stores)]):
    #                 # If the trace is not activated
    #                 if item == 'legendonly':
    #                     # In the person_id legend tracker, set the person_id to False
    #                     legend_tracker_stores[list(legend_tracker_stores)[position]] = False
    #                 elif item == True or item == 'True':
    #                     # Otherwise, the trace is activated so set the person_id to True
    #                     legend_tracker_stores[list(legend_tracker_stores)[position]] = True
    #     except KeyError:
    #         pass
    # # Retrieve all unique store types activated in the map as a list we'll pass to the accompanying attribute table
    # stores_on = [k for k,v in legend_tracker_stores.items() if v == True]

    
    ## STORES TABLE
                
    # Enable filtering for the table            
    filtering_expressions = filter_query.split(' && ')
    stores_filter = stores[(stores['PlusCode'].isin(unique_storeplus))].copy()
    stores_filter = stores_filter[stores_table_columns]
    stores_person = stores[stores_table_columns].copy()
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            stores_filter = stores_filter.loc[getattr(stores_filter[col_name], operator)(filter_value)]
            stores_person = stores_person.loc[getattr(stores_person[col_name], operator)(filter_value)]
        elif operator == 'contains':
            stores_filter = stores_filter.loc[stores_filter[col_name].str.contains(filter_value, na=False)]
            stores_person = stores_person.loc[stores_person[col_name].str.contains(filter_value, na=False)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            stores_filter = stores_filter.loc[stores_filter[col_name].str.startswith(filter_value, na=False)]
            stores_person = stores_person.loc[stores_person[col_name].str.startswith(filter_value, na=False)]
    if len(sort_by):
        stores_filter = stores_filter.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )      
        stores_person = stores_person.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )
        
    # If anyone is digitally literate, we'll add all stores that can be accessed online and are not already included in the filtered table
    stores_online = get_online_stores(stores_person)

    if 'yes' in individuals_filter['digitallit'].unique():
        for i_so, r_so in stores_online.iterrows():
            if r_so['PlusCode'] not in stores_filter['PlusCode']:
                stores_filter = stores_filter.append(stores[stores_table_columns][stores['PlusCode'] == r_so['PlusCode']])  


    # Update Network Data
    cy_edges, cy_nodes, all_opps, stores_physical_pluscode, stores_virtual_pluscode, stores_hybrid_pluscode = network_data(od[(od['free_time_start'] >= startDate) & (od['free_time_end'] <= endDate) & (od['can_visit_spacetime']) & (od['person_id'].isin(individuals_filter['person_id'].unique())) & (od['store_PlusCode'].isin(stores_filter['PlusCode'].unique()))], individuals_filter, stores_filter, stores_online)

    # Updated total accessible physical, virtual, and hybrid stores by all
    physical_opp_total = len(stores_physical_pluscode)
    virtual_opp_total = len(stores_virtual_pluscode)
    hybrid_opp_total = len(stores_hybrid_pluscode)
    
    # For every person, based on the available stores after all filtering, add up the total number of physical and virtual opportunities accessible to them and update the respective opportunity fields for each visible individual
    all_opps_df = pd.DataFrame.from_dict(all_opps, orient='index', columns=['PhysicalOpp', 'VirtualOpp', 'HybridOpp'])
    individuals_filter = pd.merge(individuals_filter.drop(columns=['PhysicalOpp', 'VirtualOpp', 'HybridOpp']), all_opps_df, left_on='person_id', right_on=all_opps_df.index, how='left')


    prisms_filter = prisms[(prisms['person_id'].isin(individuals_filter['person_id'])) & (prisms['free_time_start'] >= startDate) & (prisms['free_time_end'] <= endDate)]

    # Update 3D Map
    map_3d = create_3d_map(trajectories, stores_filter, individuals_filter, individuals)
    
    # Filter trajectories that are within the specified timerange
    trajectories_time = trajectories[(trajectories['daytime'] >= startDate) & (trajectories['daytime'] <= endDate)]
    
    # Update 2D Map
    map_2d = create_2d_map(map_2d_dropdown_value, individuals_filter, trajectories_time, stores_filter, prisms_filter) 
    
    # Hovering over a store point, county line, or trajectory line in the 3d map focuses the 2d map on that particular location 
    if clickData3d:
        map_2d.update_layout(
            mapbox_zoom = 14,
            mapbox_center = {'lat': [d['y'] for d in clickData3d['points']][0], 'lon':[d['x'] for d in clickData3d['points']][0]},
        )
        
    #map_toolbar = plotlymap.Canvas(map_2d).toolbar_widget

    return individuals_filter.to_dict('records'), stores_filter.to_dict('records'), map_2d, map_3d, physical_opp_total, virtual_opp_total, hybrid_opp_total, cy_edges + cy_nodes

    
# @app.callback(Output('tap-node-json-output', 'children'),
#               [Input('cytoscape', 'tapNode')])
# def display_tap_node(data):
#     return json.dumps(data, indent=2)

# @app.callback(Output('tap-edge-json-output', 'children'),
#               [Input('cytoscape', 'tapEdge')])
# def display_tap_edge(data):
#     return json.dumps(data, indent=2)
    
@app.callback(Output('cytoscape', 'layout'),
              [Input('dropdown-layout', 'value')])
def update_cytoscape_layout(layout):
    return {'name': layout}


@app.callback(Output('cytoscape', 'stylesheet'),
              Input('cytoscape', 'tapNode'),
              State('cytoscape', 'elements'),
#               Input('input-follower-color', 'value'),
#               Input('input-following-color', 'value'),
              Input('dropdown-person-shape', 'value'),
              Input('dropdown-store-shape', 'value'),
              Input('reset-network', 'n_clicks')
    )
def generate_stylesheet(node, elements, person_shape, store_shape, n_clicks): # follower_color, following_color,
    #print(json.dumps(node, indent = 2))
    #print(json.dumps(elements, indent = 2))

    if not node:
        return default_stylesheet
    
    stylesheet = [{
        'selector': '.person',
        'style': {
            'shape': person_shape,
            'opacity': 0.2,
        }
    },  {
        'selector': '.store',
        'style': {
            'shape': store_shape,
            'opacity': 0.2,
        }
    }, {
        'selector': 'edge',
        'style': {
            'opacity': 0.0,
            "curve-style": "bezier",
            'z-index': 1
        }
    }]
    
    global cytoscape_stylesheet
    
    # If reset network button is clicked, revert back to default state
    changed_id = [p['prop_id'] for p in callback_context.triggered][0]
    if 'reset-network' in changed_id:
        cytoscape_stylesheet = []
        return default_stylesheet
    
    else:        
        if node['classes'] == 'person':
            cytoscape_stylesheet.append({
                'selector': 'node[id = "{}"]'.format(node['data']['id']),
                'style': {
                    'background-color': indiv_colors[int(node['data']['id'])],
                    "border-color": "purple",
                    "border-width": 2,
                    "border-opacity": 1,
                    "opacity": 1,

                    'label': "data(label)",
                    "text-opacity": 1,
                    'font-family': 'Roboto',                    
                    "font-size": 40,
                    "width": "data(node_size)",
                    "height": "data(node_size)",
                    'z-index': 9999
                }
            })
            
        if node['classes'] == 'store':
            cytoscape_stylesheet = [style_dict for style_dict in cytoscape_stylesheet if not (style_dict['selector'] == 'node[id = "{}"]'.format(node['data']['id']))]
            cytoscape_stylesheet.append({
                'selector': 'node[id = "{}"]'.format(node['data']['id']),
                'style': {
                    'background-color': store_colors[stores[stores['PlusCode'] == node['data']['id']]['Type'].values[0]],
                    'border-color': '#D2F6D0',
                    'border-width': 2,
                    'border-opacity': 1,
                    'opacity': 1,

                    'label': 'data(label)',
                    'text-opacity': 1,
                    'font-family': 'Roboto',                    
                    'font-size': 40,
                    'color': 'black',
                    'z-index': 9999,
                    "width": "data(node_size)",
                    "height": "data(node_size)",
                }
            })
                
        
        for edge in node['edgesData']:

            # if you click person: you get edges to other stores (mainly); look at the target for all edge connections
            # if you click store: you get edges to other people (mainly); look at the source for all edge connections

            color_class = next((item['classes'] for i, item in enumerate(cy_edges) if (str(item['data']['source']) == str(edge['source'])) & (str(item['data']['target']) == str(edge['target']))), None)

            if (color_class is None) | (color_class == 'self'):
                # cytoscape_stylesheet.append({
                #     'selector': 'node[id = "{}"]'.format(edge['target']),
                #     'style': {
                #         'background-color': 'grey',
                #         'opacity': 0.0,
                #         "label": str(edge['target']),
                #         "color": "#B10DC9",
                #         "text-opacity": 1,
                #         "font-size": 30,
                #         'z-index': 9999
                #     }
                # })
                next
            else:    
                if node['classes'] == 'person':
                    # If the connected node is a person
                    if edge['target'].isdigit():
                        
                        # A person can also be a target when they're connected to another person, so find out which one the current person is; we want to label both connected nodes
                        connected_node = edge['source']
                        if node['data']['id'] == edge['source']:
                            connected_node = edge['target']                            
                            
                        cytoscape_stylesheet.append({
                            'selector': f"node[id = '{connected_node}']",
                            'style': {
                                'background-color': indiv_colors[int(connected_node)],
                                'opacity': 0.9,
                                "label": 'Person ' + connected_node,
                                "width": "data(node_size)",
                                "height": "data(node_size)",
                                "color": "black",
                                "text-opacity": 1,
                                'font-family': 'Roboto',                                
                                "font-size": 30,
                                'z-index': 9999
                            }
                        })
                    # Else, the connected node is a store    
                    else:
                        cytoscape_stylesheet.append({
                            'selector': 'node[id = "{}"]'.format(edge['target']),
                            'style': {
                                'background-color': store_colors[stores[stores['PlusCode'] == edge['target']]['Type'].values[0]],
                                'opacity': 0.9,
                                "label": f"{stores[stores['PlusCode'] == edge['target']]['Name'].values[0]} {edge['target']}",
                                "width": "data(node_size)",
                                "height": "data(node_size)",
                                "color": "black",
                                "text-opacity": 1,
                                'font-family': 'Roboto',                                
                                "font-size": 30,
                                'z-index': 9999
                            }
                        })

                elif node['classes'] == 'store':
                    cytoscape_stylesheet.append({
                        'selector': 'node[id = "{}"]'.format(edge['source']),
                        'style': {
                            'background-color': indiv_colors[int(edge['source'])],
                            'opacity': 0.9,
                            "label": 'Person ' + edge['source'],
                            "color": 'black',
                            "width": "data(node_size)",
                            "height": "data(node_size)",
                            "text-opacity": 1,
                            'font-family': 'Roboto',
                            "font-size": 30,
                            'z-index': 9999
                        }
                    })

                cytoscape_stylesheet.append({
                    "selector": 'edge[id= "{}"]'.format(edge['id']),
                    "style": {
                        "mid-target-arrow-color": edge_colors[color_class],
                        "mid-target-arrow-shape": "vee",
                        "line-color": edge_colors[color_class],
                        'opacity': 0.9,
                        'z-index': 9999
                    }
                })            

        return stylesheet + cytoscape_stylesheet
    
# From: https://github.com/plotly/dash-sample-apps/blob/f44f386e890c72846e39a871cde06a58f2367b5c/apps/dash-image-segmentation/app.py#L115    
# Callback for modal popup
@app.callback(
    Output("modal", "is_open"),
    [Input("howto-open", "n_clicks"), Input("howto-close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# we use a callback to toggle the collapse on small screens
@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
