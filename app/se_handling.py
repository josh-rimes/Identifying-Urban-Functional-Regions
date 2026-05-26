import pyproj
import pandas as pd


# Function clean_se_data takes the the data we need from the DataFrame and transforms coordinates to latitude and longitude
def clean_se_data(df):
    transformer = pyproj.Transformer.from_crs('EPSG:27700', 'EPSG:4326') # The transformer allows for BNG(27700) coordinates to be converted to Lat/Long(4326) coordinates
    df.rename(columns = {'centroid_x': 'latitude', 'centroid_y': 'longitude'}, inplace=True)
    for i in range(0, len(df.index)):
        if df.at[i, 'census_geography'] != 'msoa':
            df.drop([i], axis = 0, inplace = True) # Removes rows that aren't middle super output areas
            continue

        lat, lon = transformer.transform(df.at[i, 'latitude'], df.at[i, 'longitude']) # Transforms the coordinates using a pyproj transformer
        df.at[i, 'longitude'] = lon
        df.at[i, 'latitude'] = lat      

        print('Uploaded ' + str(i) + '/' + str(len(df.index)) + ' rows', end = '\r') # Sends a message to th terminal to show how quickly the rows are being cleaned

    print('Uploaded ' + str(i + 1) + '/' + str(len(df.index)) + ' rows', end = '\n')
    return df


# Function get_layers returns a list of layers from the se_data DataFrame to be used as options in a dropdown
def get_layers(df):
    layers = ['None'] # Sets layers to 'None' initially so that the dropdown resets instead of appending to old 
    values = list(df.columns.values)
    non_layers = ['area_code', 'area_name', 'census_geography', 'latitude', 'longitude'] # List of column values that aren't layer data values

    for val in values:
        if val not in non_layers:
            layers.append(val)
    
    return layers
