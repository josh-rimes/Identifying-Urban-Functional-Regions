import numpy as np
from scipy.spatial import ConvexHull
import sklearn as skl
from classification import color_map, classify_data


def DBSCAN(data, size, min_samples=10):
    X = np.array(data)
    clustering = skl.cluster.DBSCAN(eps=size, min_samples=min_samples).fit(X)
    cluster_array = clustering.labels_
    return cluster_array


# TODO: Make it only cluster the data chosen by the dropdown
# Function create_cluster_data finds the coordinates of the four corners of each cluster in an array of clusters, as well as the color associated with the group of the cluster
def create_cluster_data(df, array_of_clusters, index_bin):
    shape_lon_coords = []
    shape_lat_coords = []
    shape_colors = []

    error_count = 0

    for cluster_id in array_of_clusters:
        cluster_id = cluster_id.astype('int32')

        poi_id_array = []
        poi_coords_array = []
        for i in range(0, len(df.index)):
            if (i not in index_bin) and (df.at[i, 'cluster id'] == cluster_id):
                poi_id_array.append(i)
                poi_coords_array.append([df.at[i, 'lon'], df.at[i, 'lat']])

        if poi_id_array == []:
            continue

        # HAPPY
        try:
            points = np.array(poi_coords_array)
            hull = ConvexHull(points)
            boundary_points = points[hull.vertices].tolist()

            boundary_coords = [[], []]

            for point in boundary_points:
                boundary_coords[0].append(point[1])
                boundary_coords[1].append(point[0])
            boundary_coords[0].extend([boundary_coords[0][0], None])
            boundary_coords[1].extend([boundary_coords[1][0], None])

            shape_lat_coords.append(boundary_coords[0])
            shape_lon_coords.append(boundary_coords[1])

            group = classify_data(1, df.at[poi_id_array[0], 'pointX classification code'])
            shape_colors.append(color_map[group])

        except Exception as e:
            error_count += 1
            print(error_count, ' QH6154 Qhull precision errors caught', end='\r')

    print(error_count, 'QH6154 Qhull precision errors caught', end='\n')

    return shape_lon_coords, shape_lat_coords, shape_colors
