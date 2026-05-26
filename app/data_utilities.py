from dash import html, dash_table
import io
import base64
import pandas as pd

# Function parse_contents reads a file and strips it to leave the data we want to use
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    # Allow three file types to be uploaded
    try:
        decoded = base64.b64decode(content_string) # Decodes the data with base64
        if 'csv' in filename: # .csv format
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename: # .xls format
            df = pd.read_excel(io.BytesIO(decoded))
        elif 'json' in filename: # .json format
            df = pd.read_json(io.StringIO(decoded.decode('utf-8')))
        else:
            return html.Div(['There was an error processing this file.'])
    except Exception as e:
        print(e)
        return html.Div(['There was an error processing this file.'])
    
    return df # df is DataFrame https://pandas.pydata.org/docs/reference/frame.html


# Function data_table creates a visual data table to be displayed in the dash app
def data_display(df, filename):
    # Return a html <div> with the dash table nested
    return html.Div([
        html.H5(children = filename, style = {'margin-top':'50px'}),

        # Display DataFrame as a table of i columns
        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            page_size = 25
        ),

        html.Hr(), # horizontal line
    ])


# Function classify_data returns the classification of a POI using its pointX code and a chosen level of classification
def classify_data(level, pointX_code):
    from classification import groups, categories, classes

    # The 8 digit pointX code is broken down to find the name of the classification
    try:
        if level == 1:
            return groups[pointX_code[:2]]
        elif level == 2:
            return categories[pointX_code[2:4]]
        elif level == 3:
            return classes[pointX_code[4:]]
    except Exception as e:
        print(e)
