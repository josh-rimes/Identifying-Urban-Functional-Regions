import numpy as np
from scipy.stats import pearsonr
from math import radians
import sklearn as skl
import json
import os
from matplotlib.path import Path


def haversine_distance(acoords, bcoords):
    acoords_in_radians = [radians(_) for _ in acoords]
    bcoords_in_radians = [radians(_) for _ in bcoords]

    distance = skl.metrics.pairwise.haversine_distances([acoords_in_radians, bcoords_in_radians])
    distance = distance * 6371000/1000

    return distance


def euclidean_distance(acoords, bcoords):
    distance = skl.metrics.pairwise.euclidean_distances(acoords, bcoords)

    return distance


def rasterise_shape(coords, grid_size, bounds):
    x_min, x_max, y_min, y_max = bounds
    x = np.linspace(x_min, x_max, grid_size)
    y = np.linspace(y_min, y_max, grid_size)
    xv, yv = np.meshgrid(x, y)
    points = np.vstack((xv.flatten(), yv.flatten())).T

    path = Path(coords)
    mask = path.contains_points(points)
    return mask.reshape((grid_size, grid_size)).astype(int)


def compute_correlation(cluster_id, msoa_id, cluster_lons=None, cluster_lats=None, grid_size=100):
    if cluster_lons is None or cluster_lats is None:
        return None

    try:
        idx = int(cluster_id)
    except (ValueError, TypeError):
        return None

    if idx < 0 or idx >= len(cluster_lons) or idx >= len(cluster_lats):
        return None

    geojson_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V7_-4346226057264668960.geojson'
    )

    with open(geojson_path) as f:
        msoa_data = json.load(f)

    msoa_coords = None
    for feature in msoa_data['features']:
        if feature['properties']['MSOA21CD'] == msoa_id:
            msoa_coords = feature['geometry']['coordinates'][0]
            break

    if msoa_coords is None:
        return None

    lon_list = [c for c in cluster_lons[idx] if c is not None]
    lat_list = [c for c in cluster_lats[idx] if c is not None]

    if len(lon_list) < 3:
        return None

    cluster_poly = list(zip(lon_list, lat_list))
    msoa_poly = [(c[0], c[1]) for c in msoa_coords]

    all_lons = [c[0] for c in msoa_poly] + lon_list
    all_lats = [c[1] for c in msoa_poly] + lat_list
    bounds = (min(all_lons), max(all_lons), min(all_lats), max(all_lats))

    r1 = rasterise_shape(cluster_poly, grid_size, bounds)
    r2 = rasterise_shape(msoa_poly, grid_size, bounds)

    r, _ = pearsonr(r1.flatten().astype(float), r2.flatten().astype(float))
    return r

    # Flatten and compute correlation
    flat1 = r1.flatten()
    flat2 = r2.flatten()

    if np.all(flat1 == 0) or np.all(flat2 == 0):
        return 0.0  # No overlap or shape is entirely outside bounds

    r_value, p_value = pearsonr(flat1, flat2)
    print('Correlation (r) is: ' + str(r_value) + "/nP value is: " + str(p_value))
