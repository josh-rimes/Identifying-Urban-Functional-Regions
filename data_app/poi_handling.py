import pyproj
import spatial_utilities
import data_utilities


# Function clean_POI_data takes the the data we need from the DataFrame (df)
def clean_POI_data(df):
    global index_bin
    index_bin = [] # Bin for indexes that hold incomplete data, and therefore need to be removed
    transformer = pyproj.Transformer.from_crs('EPSG:27700', 'EPSG:4326') # The transformer allows for BNG(27700) coordinates to be converted to Lat/Long(4326) coordinates

    df.rename(columns = {'A': 'unique reference number', 'B': 'name', 'C': 'pointX classification code', 'D': 'lon', 'E': 'lat'}, inplace = True)
    df['group'] = None # Add sixth column needed
    df['category'] = None
    df['class'] = None

    for i in range(0, len(df.index)):
        line = df.at[i, 'unique reference number'] # Create a String variable of the data in row i of the DataFrame
        data_list = line.split('|') # Splits the row data into sections that we can store individually
        
        # This statement checks that all the necessary columns are present 
        if len(data_list) < 6:
            index_bin.append(i)
            df.drop([i], axis = 0, inplace = True) # Removes row with incomplete data
            continue

        df.at[i, 'unique reference number'] = data_list[0]
        df.at[i, 'name'] = data_list[1]
        df.at[i, 'pointX classification code'] = data_list[2]

        lat, lon = transformer.transform(data_list[3], data_list[4])
        print('Uploaded ' + str(i) + '/' + str(len(df.index)) + ' rows', end = '\r') # Sends a message to th terminal to show how quickly the rows are being cleaned

        df.at[i, 'lon'] = lon
        df.at[i, 'lat'] = lat
        df.at[i, 'group'] = data_utilities.classify_data(1, data_list[2])
        df.at[i, 'category'] = data_utilities.classify_data(2, data_list[2])
        df.at[i, 'class'] = data_utilities.classify_data(3, data_list[2])


    print('Uploaded ' + str(i + 1 - len(index_bin)) + '/' + str(len(df.index)) + ' rows', end = '\n')

    return df


# Function add_cluster_ids makes an array of POI coordinates, passes them through the DBSCAN algorithm, and adds the resulting cluster ids to the data table
def add_cluster_ids(df, level, slider_value, on_progress=None, selected_groups=None, min_samples=10):
    from classification import groups, categories, classes

    df['cluster id'] = None # Makes a new column in the dataframe to hold the cluster ids
    num_clusters = 0 # The reason for num_clusters is that I need a way to differentiate between the clusters made in each group

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
            coord_array = [] # List of coordinates that'll be inputted into the DBSCAN cluster
            index_array = [] # List that holds the indexes of all POIs that need updating

            for i in range(0, len(df.index)):
                # This if statement finds any POIs that are within the classification of the group (and not in th index bin), and adds the necessary data to the arrays ready for clustering
                if (i not in index_bin) and (classification_dict[classification] == data_utilities.classify_data(level, df.at[i, 'pointX classification code'])):
                    # Skip POIs whose group is not in the selected visible groups
                    if selected_groups is not None and 'All' not in selected_groups:
                        poi_group = data_utilities.classify_data(1, df.at[i, 'pointX classification code'])
                        if poi_group not in selected_groups:
                            continue
                    coord_array.append([float(df.at[i, 'lat']), float(df.at[i, 'lon'])]) # Adds the lat and long coordinate pair to the coords array
                    index_array.append(i)

            if not coord_array: # Skip classifications with no matching POIs
                continue

            temp_cluster_ids = spatial_utilities.DBSCAN(coord_array, slider_value, min_samples)

            num_clusters += len(set(temp_cluster_ids))
            # This if statement eliminates the possibility of -1 counting as a cluster instead the tag for outliers
            if -1 in cluster_ids:
                num_clusters -= 1

            for i in range(0, len(index_array) - 1):
                if temp_cluster_ids[i] != -1:
                    temp_cluster_ids[i] += num_clusters
                    cluster_ids.append(temp_cluster_ids[i])
                
                df.at[index_array[i], 'cluster id'] = temp_cluster_ids[i] # Updates the DataFrame to give the POI a cluster id

            print('Classification id(' + classification + ') clustered', end = '\r')
        
        print('Classification id(' + '10' + ') clustered', end = '\n')

        # Assigns values from the cluster data - lon, lat are 2D arrays that hold the coordinates for square clusters, colors holds a list of cluster colors
        if on_progress:
            on_progress('Generating cluster shapes...')
        lon, lat, colors = spatial_utilities.create_cluster_data(df, set(cluster_ids), index_bin)
        cluster_data = [lon, lat, colors] # Zips the variables for the sake of cleanliness

        return df, cluster_data


    except Exception as e:
        import traceback
        traceback.print_exc()

        return df