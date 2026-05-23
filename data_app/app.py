# INFO: UPDATE DOCUMENTATION
# BUG: CHANGE MIN_SAMPLES (THIS MIGHT CHANGE THE WHOLE LANDSCAPE OF THE ANALYSIS)
from dash import Dash, html, dcc, callback, Input, Output, State, no_update
import io
import pandas as pd
import data_utilities
import spatial_utilities
import map_handling
import poi_handling
import se_handling

app = Dash(__name__, suppress_callback_exceptions = True)

layers = ['None']

app.layout = [
    html.H1(children = 'Interactive Urban Correlation Map'),

    # UPLOAD DIV
    html.Div([
        html.Div([
            dcc.Upload(id = 'poi_file_input', 
                       children = html.Button('Choose POI file / Drag & drop', 
                       className = 'upload-button')) # Opens pop-up for upload when clicked
        ], className = 'upload-button-div'),

        html.Div([
            dcc.Upload(id = 'se_file_input', 
                       children = html.Button('Choose Socio-Economic file / Drag & drop', 
                       className = 'upload-button')) # Opens pop-up for upload when clicked
        ], className = 'upload-button-div'),
    ], className = 'upload-div'),

    # TODO: Change minimum POIs for clusters
    # TOOLBAR DIV
    html.Div([
        html.Div([
            dcc.Checklist(id = 'display_checklist', 
                          options = [{'label': 'Hide clusters', 'value': 'clusters'},{'label': 'Hide layer', 'value': 'layer'},],
                          value = [], # Default checklist has Hide clusters left blank
                          inline = True),
        ], className = 'checklist-div'),

        html.Div([
            html.Label(children = 'Select which clusters are visible:', 
                       id = 'cluster_dropdown_label', 
                       style = {'textAlign':'centre', 'margin-bottom':'5px'}),
            dcc.Dropdown(['All', 'Accommodation, eating and drinking', 'Commercial services', 'Attractions', 'Sport and entertainment', 'Education and health', 'Public Infrastructure', 'Manufacturing and production', 'Retail', 'Transport'], 
                         'All', 
                         multi = True, 
                         id = 'cluster_dropdown'),
        ], className = 'dropdown-div'),
        
        html.Div([
            html.Label(children = 'Size of clusters:', 
                       id = 'slider_label', 
                       style = {'textAlign':'centre', 'margin-bottom':'5px'}),
            dcc.Slider(0.0005, 0.005, 0.0005, 
                       value = 0.001, 
                       marks = None, 
                       id = 'slider', 
                       className = 'slider',
                       tooltip = {'placement': 'bottom', 'always_visible': True}),
        ], className = 'slider-div'),

        html.Div([
            html.Label(children = 'Level of classification:', 
                       id = 'level_dropdown_label', 
                       style = {'textAlign':'centre', 'margin-bottom':'5px'}),
            dcc.Dropdown(options = ['1', '2', '3'], 
                         value = '1', 
                         multi = False, 
                         id = 'level_dropdown')
        ], className = 'dropdown-div'),

        html.Div([
            html.Label(children = 'Select socio-economic layer:', 
                       id = 'layer_dropdown_label', 
                       style = {'textAlign':'centre', 'margin-bottom':'5px'}),
            dcc.Dropdown(options = ['None'], 
                         value = 'None', 
                         multi = False, 
                         id = 'layer_dropdown')
        ], className = 'dropdown-div'),
    ], className = 'toolbar-div'),

    html.Div(id = 'data_output', className = 'data-div'), # Displays the data table

    # CORRELATION DIV
    html.Div([
        html.Div(
            dcc.Input(
            placeholder = 'Enter a cluster id...',
            type = 'text',
            value = '',
            id = 'cluster_id_input'),
            className = 'input-div'),
        html.Div(
            dcc.Input(
                placeholder = 'Enter a msoa id...',
                type = 'text',
                value = '',
                id = 'msoa_id_input'),
                className = ' input-div'),
        html.Button('Compute correlation', id = 'compute_button', className = 'compute-button')
    ], className = 'correlation-div'),

    html.H2(children = 'Made by Josh Rimes    2025'),
    dcc.Store(id='poi-cleaned-store', storage_type='local'),
]

@callback(
    Output('poi-cleaned-store', 'data'),
    Input('poi_file_input', 'contents'),
    State('poi_file_input', 'filename'),
    prevent_initial_call=True)
def cache_poi_data(poi_file_input, filename):
    if poi_file_input is None:
        return no_update
    poi_df = data_utilities.parse_contents(poi_file_input, filename)
    if not isinstance(poi_df, pd.DataFrame):
        return no_update
    poi_df = poi_handling.clean_POI_data(poi_df)
    poi_df = poi_df.reset_index(drop=True)  # Ensure sequential index after dropped invalid rows
    return {
        'filename': filename,
        'data': poi_df.to_json(date_format='iso', orient='split'),
        'index_bin': []  # All invalid rows already removed; no gaps remain
    }


@callback(
    Output('data_output', 'children'),
    Output('layer_dropdown', 'options'),
    Input('poi-cleaned-store', 'data'),
    Input('se_file_input', 'contents'),
    Input('display_checklist', 'value'),
    Input('cluster_dropdown', 'value'),
    Input('layer_dropdown', 'value'),
    Input('level_dropdown', 'value'),
    Input('slider', 'value'),
    Input('cluster_id_input', 'value'),
    Input('msoa_id_input', 'value'),
    Input('compute_button', 'value'))

def update_output(poi_store_data, se_file_input, display_checklist, cluster_dropdown, layer_dropdown, level_dropdown, slider, cluster_id_input, msoa_id_input, compute_button):
    data_output = None
    options = ['None']
    poi_df = None
    se_df = pd.DataFrame({'A' : []})

    print('\n\nUpdating output:')

    if poi_store_data is not None:
        poi_df = pd.read_json(io.StringIO(poi_store_data['data']), orient='split') # Load cleaned POI data from cache
        poi_handling.index_bin = poi_store_data['index_bin'] # Restore index bin used during cleaning
        # JSON round-trip converts numeric-string codes (e.g. '03170245') to integers; restore as zero-padded strings
        if pd.api.types.is_numeric_dtype(poi_df['pointX classification code']):
            poi_df['pointX classification code'] = poi_df['pointX classification code'].fillna(0).astype(int).astype(str).str.zfill(8)
        filename = poi_store_data['filename']
        poi_df, cluster_data = poi_handling.add_cluster_ids(poi_df, int(level_dropdown), slider) # Cluster POIs

        if se_file_input is not None:
            se_df = data_utilities.parse_contents(se_file_input, 'file.csv') # Parse the socio-economic data
            se_df = se_handling.clean_se_data(se_df) # Clean the socio-economic data
            options = se_handling.get_layers(se_df) # Set new dropdown list from socio-economic data

    if poi_df is not None:
        data_output = [map_handling.create_map(poi_df, cluster_data, display_checklist, cluster_dropdown, se_df, layer_dropdown, filename), 
                       data_utilities.data_display(poi_df, filename)]
    
    if compute_button == 'Click':
        spatial_utilities.compute_correlation(cluster_id_input, msoa_id_input)
    

    return data_output, options
    


if __name__ == '__main__':
    app.run(debug=True)
