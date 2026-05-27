import os
import json
from dash import html, dcc
import plotly.express as px
import plotly.graph_objects as go
from classification import color_map


_geojson_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'data',
    'Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V7_-4346226057264668960.geojson'
)
with open(_geojson_path) as _response:
    msoas = json.load(_response)


def create_map(poi_data, cluster_data, checklist_value, cluster_value, se_data, layer_value, filename):
    fig = px.scatter_map(poi_data,
                         lat='lat',
                         lon='lon',
                         color='group',
                         hover_name='name',
                         hover_data={'lat': False, 'lon': False, 'group': True, 'category': True, 'class': True},
                         color_discrete_map=color_map,
                         zoom=13,
                         height=600)
    fig.update_layout(map_style='open-street-map')
    fig.update_layout(margin={'r': 0, 't': 0, 'l': 0, 'b': 0}, paper_bgcolor='rgba(0,0,0,0)', legend=dict(
        x=1, y=1,
        xanchor='right', yanchor='top',
        bgcolor='#1a2234',
        bordercolor='#2d3a50',
        borderwidth=1,
        title=''
    ))

    if 'clusters' not in checklist_value:
        lons, lats, colors = cluster_data
        for longitude, latitude, color in zip(lons, lats, colors):
            group = list(color_map.keys())[list(color_map.values()).index(color)]
            if ('All' in cluster_value) or (group in cluster_value):
                fig.add_trace(
                    go.Scattermap(
                        mode='lines',
                        fill='toself',
                        line={'color': color},
                        lon=longitude,
                        lat=latitude,
                        showlegend=False)
                )
                fig.update_traces(hoverinfo='skip')

    if (not se_data.empty) and (layer_value != 'None') and ('layer' not in checklist_value):
        fig.add_trace(
            go.Choroplethmap(
                geojson=msoas,
                locations=se_data.area_code,
                z=se_data[layer_value].astype(float),
                featureidkey='properties.MSOA21CD',
                colorscale='Blues',
                showlegend=False,
                colorbar=dict(x=-0.15)
            )
        )
        fig.update_traces(marker_opacity=0.6, hoverinfo='skip')
        fig.update_layout(coloraxis_colorbar=dict(yanchor='top', y=1, x=0, ticks='outside'))

    return html.Div([
        dcc.Graph(figure=fig),
    ])
