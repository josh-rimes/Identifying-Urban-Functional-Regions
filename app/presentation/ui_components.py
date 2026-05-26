from dash import html, dash_table


def data_display(df, filename):
    return html.Div([
        html.H5(children=filename, style={'margin-top': '50px'}),

        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            page_size=25
        ),

        html.Hr(),
    ])
