from core.coordinate_utils import create_bng_transformer


def clean_se_data(df):
    transformer = create_bng_transformer()
    df.rename(columns={'centroid_x': 'latitude', 'centroid_y': 'longitude'}, inplace=True)
    for i in range(0, len(df.index)):
        if df.at[i, 'census_geography'] != 'msoa':
            df.drop([i], axis=0, inplace=True)
            continue

        lat, lon = transformer.transform(df.at[i, 'latitude'], df.at[i, 'longitude'])
        df.at[i, 'longitude'] = lon
        df.at[i, 'latitude'] = lat

        print('Uploaded ' + str(i) + '/' + str(len(df.index)) + ' rows', end='\r')

    print('Uploaded ' + str(i + 1) + '/' + str(len(df.index)) + ' rows', end='\n')
    return df


def get_layers(df):
    layers = ['None']
    values = list(df.columns.values)
    non_layers = ['area_code', 'area_name', 'census_geography', 'latitude', 'longitude']

    for val in values:
        if val not in non_layers:
            layers.append(val)

    return layers
