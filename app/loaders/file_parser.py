import io
import base64
import pandas as pd
from dash import html


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    try:
        decoded = base64.b64decode(content_string)
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'json' in filename:
            df = pd.read_json(io.StringIO(decoded.decode('utf-8')))
        else:
            return html.Div(['There was an error processing this file.'])
    except Exception as e:
        print(e)
        return html.Div(['There was an error processing this file.'])

    return df
