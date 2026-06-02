from core.coordinate_utils import create_bng_transformer
from classification import classify_data
from core import clustering as _clustering


index_bin = []


def clean_POI_data(df):
    global index_bin
    index_bin = []
    transformer = create_bng_transformer()

    df.rename(columns={'A': 'unique reference number', 'B': 'name', 'C': 'pointX classification code', 'D': 'lon', 'E': 'lat'}, inplace=True)
    df['group'] = None
    df['category'] = None
    df['class'] = None

    for i in range(0, len(df.index)):
        line = df.at[i, 'unique reference number']
        data_list = line.split('|')

        if len(data_list) < 6:
            index_bin.append(i)
            df.drop([i], axis=0, inplace=True)
            continue

        df.at[i, 'unique reference number'] = data_list[0]
        df.at[i, 'name'] = data_list[1]
        df.at[i, 'pointX classification code'] = data_list[2]

        lat, lon = transformer.transform(data_list[3], data_list[4])
        print('Uploaded ' + str(i) + '/' + str(len(df.index)) + ' rows', end='\r')

        df.at[i, 'lon'] = lon
        df.at[i, 'lat'] = lat
        df.at[i, 'group'] = classify_data(1, data_list[2])
        df.at[i, 'category'] = classify_data(2, data_list[2])
        df.at[i, 'class'] = classify_data(3, data_list[2])

    print('Uploaded ' + str(i + 1 - len(index_bin)) + '/' + str(len(df.index)) + ' rows', end='\n')

    return df


def add_cluster_ids(df, level, slider_value, on_progress=None, selected_groups=None, min_samples=10):
    from classification import groups, categories, classes

    df['cluster id'] = None
    num_clusters = 0

    try:
        if level == 1:
            classification_dict = groups
        elif level == 2:
            classification_dict = categories
        elif level == 3:
            classification_dict = classes

        cluster_ids = []
        classification_list = list(classification_dict)
        for idx, classification in enumerate(classification_list):
            if on_progress:
                on_progress(f'Clustering {idx + 1}/{len(classification_list)}...')
            coord_array = []
            index_array = []

            for i in range(0, len(df.index)):
                if (i not in index_bin) and (classification_dict[classification] == classify_data(level, df.at[i, 'pointX classification code'])):
                    if selected_groups is not None and 'All' not in selected_groups:
                        poi_group = classify_data(1, df.at[i, 'pointX classification code'])
                        if poi_group not in selected_groups:
                            continue
                    coord_array.append([float(df.at[i, 'lat']), float(df.at[i, 'lon'])])
                    index_array.append(i)

            if not coord_array:
                continue

            temp_cluster_ids = _clustering.DBSCAN(coord_array, slider_value, min_samples)

            offset = num_clusters
            num_clusters += len([x for x in set(temp_cluster_ids) if x != -1])

            for i in range(0, len(index_array)):
                if temp_cluster_ids[i] != -1:
                    temp_cluster_ids[i] += offset
                    cluster_ids.append(temp_cluster_ids[i])

                df.at[index_array[i], 'cluster id'] = temp_cluster_ids[i]

            print('Classification id(' + classification + ') clustered', end='\r')

        print('Classification id(' + '10' + ') clustered', end='\n')

        if on_progress:
            on_progress('Generating cluster shapes...')
        lon, lat, colors = _clustering.create_cluster_data(df, set(cluster_ids), index_bin)
        cluster_data = [lon, lat, colors]

        return df, cluster_data

    except Exception as e:
        import traceback
        traceback.print_exc()

        return df
