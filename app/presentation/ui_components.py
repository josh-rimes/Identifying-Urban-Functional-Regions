from dash import html, dash_table


def data_display(df, filename):
    return html.Div([
        html.H5(children=filename, style={'margin-top': '50px', 'text-align': 'center', 'font-size': '200%', 'color': '#94a3b8', 'font-family': '"Inter", "Segoe UI", Arial, sans-serif', 'font-weight': '600', 'letter-spacing': '0.3px'}),

        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            page_size=25,
            style_table={'overflowX': 'auto'},
        ),
    ])
