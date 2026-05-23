import numpy as np
from scipy.spatial import ConvexHull
from scipy.stats import pearsonr
from math import radians
import sklearn as skl
import json
import matplotlib.pyplot as plt
from matplotlib.path import Path
import data_utilities
from classification import color_map



# Function haversine_distance measures the haversine distance between 2 sets of lat/long coordinates
def haversine_distance(acoords, bcoords):
    acoords_in_radians = [radians(_) for _ in acoords]
    bcoords_in_radians = [radians(_) for _ in bcoords]

    distance = skl.metrics.pairwise.haversine_distances([acoords_in_radians, bcoords_in_radians])
    distance = distance * 6371000/1000 # Pretty sure this just converts to kilometers

    return distance


# Function euclidean_distance measures the euclidean distance between 2 sets of lat/long coordinates
def euclidean_distance(acoords, bcoords):
    distance = skl.metrics.pairwise.euclidean_distances(acoords, bcoords)

    return distance


# Function cluster takes in an array of lat lon pairs and clusters them based on euclidean distance
def DBSCAN(data, size, min_samples=10):
    X = np.array(data)

    # DBSCAN info https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
    clustering = skl.cluster.DBSCAN(eps = size, min_samples = min_samples).fit(X) # There is no way to make a maximum cluster size
    cluster_array = clustering.labels_

    return cluster_array


# TODO: Make it only cluster the data chosen by the dropdown
# Function create_cluster_data finds the coordinates of the four corners of each cluster in an array of clusters, as well as the color associated with the group of the cluster
def create_cluster_data(df, array_of_clusters, index_bin):
    shape_lon_coords = [] # This 2D list will hold all of the latitude coordinates for clusters
    shape_lat_coords = [] # This 2D list will hold all of the longitude coordinates for clusters
    shape_colors = [] # This list will hold the colours for every cluster

    error_count = 0 # For counting caught errors

    for cluster_id in array_of_clusters:
        cluster_id = cluster_id.astype('int32')

        poi_id_array = [] # List to hold all of the POIs within the cluster # INFO: This is crap coding... sort it out you idiot
        poi_coords_array = [] # List to hold the coords of POIs in the cluster
        for i in range(0, len(df.index)):
            # This if statement is true if the POI is in the cluster
            if (i not in index_bin) and (df.at[i, 'cluster id'] == cluster_id):
                poi_id_array.append(i)
                poi_coords_array.append([df.at[i, 'lon'], df.at[i, 'lat']])

        # The rest of the code within the for loop doesn't work if the id_array is empty
        if poi_id_array == []:
            continue

        # HAPPY
        try:
            points = np.array(poi_coords_array)
            hull = ConvexHull(points) # Computes a convex hull from the POIs in the cluster - to find out more about convex hulls visit https://www.geeksforgeeks.org/convex-hull-algorithm/
            boundary_points = points[hull.vertices].tolist() # This assigns the coordinates of the hull points to a new list
        
            boundary_coords = [[], []]

            # This loop creates a set of coordinates for the cluster that can then be used later to create a shape in plotly
            for point in boundary_points:
                boundary_coords[0].append(point[1])
                boundary_coords[1].append(point[0])
            boundary_coords[0].extend([boundary_coords[0][0], None])
            boundary_coords[1].extend([boundary_coords[1][0], None])

            shape_lat_coords.append(boundary_coords[0])
            shape_lon_coords.append(boundary_coords[1])

            # Assign a color from the color map
            group = data_utilities.classify_data(1, df.at[poi_id_array[0], 'pointX classification code'])
            shape_colors.append(color_map[group])

        except Exception as e:
            error_count += 1
            print(error_count, ' QH6154 Qhull precision errors caught', end = '\r')

    print(error_count, 'QH6154 Qhull precision errors caught', end = '\n')

    return shape_lon_coords, shape_lat_coords, shape_colors


# Function rasterise_shape rasterises a polygon given by coords into a binary grid.
def rasterise_shape(coords, grid_size, bounds):
    x_min, x_max, y_min, y_max = bounds
    x = np.linspace(x_min, x_max, grid_size)
    y = np.linspace(y_min, y_max, grid_size)
    xv, yv = np.meshgrid(x, y)
    points = np.vstack((xv.flatten(), yv.flatten())).T

    path = Path(coords)
    mask = path.contains_points(points)
    return mask.reshape((grid_size, grid_size)).astype(int)

# Function correlation computes spatial correlation coefficient between two shapes.
def compute_correlation(cluster_id, msoa_id, grid_size=100):
    # Find coords
    f = open('Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V7_-4346226057264668960.geojson')
    msoa_data = json.load(f)
    for i in msoa_data['EPSG:4326']:
        if i['properties']['MSOA21CD'] == msoa_id:
            msoa_coords = i['geometry']['coordinates']
    cluster_coords = shape_lon_coords[cluster_id], shape_lat_coords[cluster_id]


    # Determine the bounding box that covers both shapes
    all_coords = np.vstack((cluster_coords, msoa_coords))
    x_min, y_min = np.min(all_coords, axis = 0)
    x_max, y_max = np.max(all_coords, axis = 0)
    bounds = (x_min, x_max, y_min, y_max)

    # Rasterise the shapes
    r1 = rasterise_shape(cluster_coords, grid_size, bounds)
    r2 = rasterise_shape(msoa_coords, grid_size, bounds)

    # Flatten and compute correlation
    flat1 = r1.flatten()
    flat2 = r2.flatten()
    
    if np.all(flat1 == 0) or np.all(flat2 == 0):
        return 0.0  # No overlap or shape is entirely outside bounds

    r_value, p_value = pearsonr(flat1, flat2)
    print('Correlation (r) is: ' + str(r_value) + "/nP value is: " + str(p_value))

