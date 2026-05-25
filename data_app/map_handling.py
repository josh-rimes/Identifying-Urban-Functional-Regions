from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go
import json
from classification import color_map
from data_utilities import classify_data

global msoas
with open('Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V7_-4346226057264668960.geojson') as response:
            msoas = json.load(response)
            response.close()


# Function create_map creates a map figure with the POI data overlaid 
def create_map(poi_data, cluster_data, checklist_value, cluster_value, se_data, layer_value, filename):
    # Use of scatter_map takes in data, column headings, as well as other styling, formatting parameters
    fig = px.scatter_map(poi_data, 
                         lat = 'lat', 
                         lon = 'lon', 
                         color = 'group', 
                         hover_name = 'name', 
                         hover_data = {'lat': False, 'lon': False, 'group': True, 'category': True, 'class': True}, 
                         color_discrete_map = color_map, 
                         zoom = 13, 
                         height = 600)
    fig.update_layout(map_style = 'open-street-map') # The map figure uses the open street map base style
    fig.update_layout(margin = {'r':0,'t':0,'l':0,'b':0}, paper_bgcolor='rgba(0,0,0,0)', legend=dict(
        x=1, y=1,
        xanchor='right', yanchor='top',
        bgcolor='#1a2234',
        bordercolor='#2d3a50',
        borderwidth=1,
        title=''
    ))

    # Checks if the hide clusters checkbox is ticked
    if 'clusters' not in checklist_value:
        lons, lats, colors = cluster_data # Expands and assigns values from the cluster data
        for longitude, latitude, color in zip(lons, lats, colors):
            group = list(color_map.keys())[list(color_map.values()).index(color)]
            if ('All' in cluster_value) or (group in cluster_value):
                # Using add_trace allows multiple layers on the map
                fig.add_trace(
                    # go.scattermap is different from px.scatter_map, don't ask how, but go has the capability to draw and fill lines
                    go.Scattermap(
                        mode = 'lines', 
                        fill = 'toself', 
                        line = {'color': color}, 
                        lon = longitude, 
                        lat = latitude, 
                        showlegend = False) # Show legend is set to false so that the hover data for clusters is at a minimum
                )
                fig.update_traces(hoverinfo = 'skip')

    # Makes sure a layer of socio-economic data has been selected
    if (not se_data.empty) and (layer_value != 'None') and ('layer' not in checklist_value):
        fig.add_trace(
            # go.Choroplethmap shows a heat map type map with geographical regions
            go.Choroplethmap(
                geojson = msoas, # Uses the msoa polygons
                locations = se_data.area_code,
                z = se_data[layer_value].astype(float), # Sets the data that is assigned a color 
                featureidkey = 'properties.MSOA21CD', # We want to match the data to the polygons using the correct id key
                colorscale = 'Blues',
                showlegend = False,
                colorbar=dict(x=-0.15)
            )
        )
        fig.update_traces(marker_opacity = 0.6, hoverinfo = 'skip')
        fig.update_layout(coloraxis_colorbar = dict(yanchor = 'top', y = 1, x = 0, ticks = 'outside'))

    # Throughput html elements that display the map
    return html.Div([
        dcc.Graph(figure = fig),
        html.Hr(),  # Horizontal line
    ])