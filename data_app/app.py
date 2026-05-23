# INFO: UPDATE DOCUMENTATION
# BUG: CHANGE MIN_SAMPLES (THIS MIGHT CHANGE THE WHOLE LANDSCAPE OF THE ANALYSIS)
from dash import Dash, html, dcc, callback, Input, Output, State, no_update
import io
import threading
import pandas as pd
import data_utilities
import spatial_utilities
import map_handling
import poi_handling
import se_handling

app = Dash(__name__, suppress_callback_exceptions = True)

layers = ['None']


class _ProcessingState:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_processing = False
        self.status = ''
        self.result = None   # Tuple of (data_output_children, options) when done
        self.error = None
        self.generation = 0  # Incremented on each new request; used to discard stale results


_state = _ProcessingState()


def _run_processing(poi_df, index_bin, level, slider, display_checklist, cluster_dropdown, se_df, layer_dropdown, filename, options, generation, min_samples=10):
    """Run clustering and map creation in a background thread."""
    def on_progress(msg):
        with _state.lock:
            if _state.generation == generation:
                _state.status = msg

    try:
        poi_handling.index_bin = index_bin
        poi_df_result, cluster_data = poi_handling.add_cluster_ids(
            poi_df, level, slider, on_progress=on_progress, selected_groups=cluster_dropdown, min_samples=min_samples)

        on_progress('Creating map...')
        map_children = map_handling.create_map(poi_df_result, cluster_data, display_checklist, cluster_dropdown, se_df, layer_dropdown, filename)
        table_children = data_utilities.data_display(poi_df_result, filename)

        with _state.lock:
            if _state.generation == generation:
                _state.result = (map_children, table_children, options)
                _state.is_processing = False

    except Exception as e:
        import traceback
        traceback.print_exc()
        with _state.lock:
            if _state.generation == generation:
                _state.error = str(e)
                _state.is_processing = False

app.layout = html.Div([

    # LEFT SIDEBAR
    html.Div([
        html.Div([
            html.Div(className='title-dot'),
            html.H1([
                html.Span('Urban', className='title-urban'),
                html.Span(' Cluster', className='title-cluster'),
            ]),
        ], className='sidebar-header'),

        html.Div([
            dcc.Upload(id='poi_file_input',
                children=html.Button('Upload POI File', className='upload-button')),
            dcc.Upload(id='se_file_input',
                children=html.Button('Upload SE File', className='upload-button')),
        ], className='sidebar-section'),

        html.Div([
            html.Span('CATEGORIES', className='section-label'),
            dcc.Dropdown(
                ['All', 'Accommodation, eating and drinking', 'Commercial services',
                 'Attractions', 'Sport and entertainment', 'Education and health',
                 'Public Infrastructure', 'Manufacturing and production', 'Retail', 'Transport'],
                'All', multi=True, id='cluster_dropdown', className='sidebar-dropdown'),
        ], className='sidebar-section'),

        html.Div([
            html.Span('ALGORITHM', className='section-label'),
            html.Div([
                html.Span('Epsilon (km)', className='slider-label-text'),
                dcc.Slider(0.0005, 0.005, 0.0005,
                    value=0.002, marks=None, id='slider',
                    tooltip={'placement': 'bottom', 'always_visible': True}),
            ], className='slider-container'),
            html.Div([
                html.Span('Min samples', className='slider-label-text'),
                dcc.Slider(1, 50, 1,
                    value=10, marks=None, id='min_samples_slider',
                    tooltip={'placement': 'bottom', 'always_visible': True}),
            ], className='slider-container'),
        ], className='sidebar-section'),

        html.Div([
            html.Span('MAP LAYER', className='section-label'),
            dcc.Checklist(
                id='display_checklist',
                options=[
                    {'label': 'Hide clusters', 'value': 'clusters'},
                    {'label': 'Hide layer', 'value': 'layer'},
                ],
                value=[],
                className='display-checklist'),
            html.Label('Socio-economic layer:', className='control-label', style={'marginTop': '12px'}),
            dcc.Dropdown(options=['None'], value='None', multi=False,
                id='layer_dropdown', className='sidebar-dropdown'),
        ], className='sidebar-section'),

        html.Div([
            html.Label('Classification Level', className='control-label'),
            dcc.Dropdown(options=['1', '2', '3'], value='1', multi=False,
                id='level_dropdown', className='sidebar-dropdown'),
        ], className='sidebar-section'),

        html.Div([
            html.Span('CORRELATION', className='section-label'),
            dcc.Input(placeholder='Enter a cluster id...', type='text', value='',
                id='cluster_id_input', className='sidebar-input'),
            dcc.Input(placeholder='Enter a msoa id...', type='text', value='',
                id='msoa_id_input', className='sidebar-input'),
            html.Button('Compute correlation', id='compute_button', className='compute-button'),
        ], className='sidebar-section'),

    ], className='left-sidebar'),

    # CENTER MAP + TABLE
    html.Div([
        html.Div(id='map_output'),
        html.Button(
            ['TABLE  ', html.Span('▼', id='table-toggle-arrow')],
            id='table-toggle-banner',
            className='table-toggle-banner',
            n_clicks=0,
        ),
        html.Div(id='table_output', className='table-content'),
    ], className='map-area'),

    # RIGHT SIDEBAR
    html.Div(className='right-sidebar'),

    dcc.Interval(id='progress-interval', interval=500, n_intervals=0, disabled=True),
    html.Div([
        html.Div(className='spinner'),
        html.P('Processing...', id='loading-status-text')
    ], id='loading-overlay', className='loading-overlay', style={'display': 'none'}),
    dcc.Store(id='poi-cleaned-store', storage_type='local'),

], className='app-container')

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
    Output('map_output', 'children'),
    Output('table_output', 'children'),
    Output('layer_dropdown', 'options'),
    Output('loading-overlay', 'style'),
    Output('progress-interval', 'disabled'),
    Input('poi-cleaned-store', 'data'),
    Input('se_file_input', 'contents'),
    Input('display_checklist', 'value'),
    Input('cluster_dropdown', 'value'),
    Input('layer_dropdown', 'value'),
    Input('level_dropdown', 'value'),
    Input('slider', 'value'),
    Input('min_samples_slider', 'value'),
    Input('cluster_id_input', 'value'),
    Input('msoa_id_input', 'value'),
    Input('compute_button', 'value'))

def update_output(poi_store_data, se_file_input, display_checklist, cluster_dropdown, layer_dropdown, level_dropdown, slider, min_samples_slider, cluster_id_input, msoa_id_input, compute_button):
    if poi_store_data is None:
        return no_update, no_update, ['None'], {'display': 'none'}, True

    print('\n\nUpdating output:')

    poi_df = pd.read_json(io.StringIO(poi_store_data['data']), orient='split') # Load cleaned POI data from cache
    poi_handling.index_bin = poi_store_data['index_bin'] # Restore index bin used during cleaning
    # JSON round-trip converts numeric-string codes (e.g. '03170245') to integers; restore as zero-padded strings
    if pd.api.types.is_numeric_dtype(poi_df['pointX classification code']):
        poi_df['pointX classification code'] = poi_df['pointX classification code'].fillna(0).astype(int).astype(str).str.zfill(8)
    filename = poi_store_data['filename']
    index_bin = poi_store_data['index_bin']

    se_df = pd.DataFrame({'A': []})
    options = ['None']
    if se_file_input is not None:
        se_df = data_utilities.parse_contents(se_file_input, 'file.csv') # Parse the socio-economic data
        se_df = se_handling.clean_se_data(se_df) # Clean the socio-economic data
        options = se_handling.get_layers(se_df) # Set new dropdown list from socio-economic data

    if compute_button == 'Click':
        spatial_utilities.compute_correlation(cluster_id_input, msoa_id_input)

    with _state.lock:
        _state.generation += 1
        gen = _state.generation
        _state.is_processing = True
        _state.status = 'Clustering POIs...'
        _state.result = None
        _state.error = None

    thread = threading.Thread(
        target=_run_processing,
        args=(poi_df, index_bin, int(level_dropdown), slider, display_checklist, cluster_dropdown, se_df, layer_dropdown, filename, options, gen, min_samples_slider),
        daemon=True
    )
    thread.start()

    return no_update, no_update, no_update, {'display': 'flex'}, False


@callback(
    Output('map_output', 'children', allow_duplicate=True),
    Output('table_output', 'children', allow_duplicate=True),
    Output('layer_dropdown', 'options', allow_duplicate=True),
    Output('loading-status-text', 'children'),
    Output('loading-overlay', 'style', allow_duplicate=True),
    Output('progress-interval', 'disabled', allow_duplicate=True),
    Input('progress-interval', 'n_intervals'),
    prevent_initial_call=True)
def poll_progress(n_intervals):
    with _state.lock:
        if not _state.is_processing:
            if _state.result is not None:
                map_children, table_children, options = _state.result
                _state.result = None
                return map_children, table_children, options, 'Done!', {'display': 'none'}, True
            # Error or unexpected state — hide overlay
            return no_update, no_update, no_update, _state.error or '', {'display': 'none'}, True
        return no_update, no_update, no_update, _state.status, no_update, no_update


@callback(
    Output('table_output', 'style'),
    Output('table-toggle-arrow', 'children'),
    Input('table-toggle-banner', 'n_clicks'),
    prevent_initial_call=True)
def toggle_table(n_clicks):
    if n_clicks % 2 == 1:
        return {'display': 'none'}, '▶'
    return {}, '▼'


if __name__ == '__main__':
    app.run(debug=True)

