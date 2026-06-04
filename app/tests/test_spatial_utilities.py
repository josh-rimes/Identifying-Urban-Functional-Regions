import numpy as np
import pytest

from core import spatial_analysis
from core import clustering


# ---------------------------------------------------------------------------
# Distance calculations
# ---------------------------------------------------------------------------

def test_same_location_has_zero_distance():
    cardiff = [51.4816, -3.1791]
    result = spatial_analysis.haversine_distance(cardiff, cardiff)
    # haversine_distances returns a 2×2 matrix; [0][1] is the off-diagonal distance
    assert result[0][1] == pytest.approx(0.0, abs=1e-6)


def test_cardiff_to_london_distance_is_plausible():
    cardiff = [51.4816, -3.1791]
    london  = [51.5074, -0.1278]
    result = spatial_analysis.haversine_distance(cardiff, london)
    distance_km = result[0][1]
    # Straight-line distance is approximately 212 km
    assert 200 < distance_km < 230, (
        f"Expected Cardiff–London to be ~212 km, got {distance_km:.1f} km"
    )


# ---------------------------------------------------------------------------
# DBSCAN clustering behaviour
# ---------------------------------------------------------------------------

def test_isolated_poi_is_not_grouped_with_dense_cluster():
    rng = np.random.default_rng(0)
    # 20 tightly packed points near Cardiff
    cluster_points = (
        51.4816 + rng.uniform(-0.0003, 0.0003, (20, 1)),
        -3.1791 + rng.uniform(-0.0003, 0.0003, (20, 1)),
    )
    cluster_coords = np.hstack(cluster_points).tolist()
    # One isolated point far to the north
    isolated_coord = [[52.5, -3.1791]]
    data = cluster_coords + isolated_coord

    labels = clustering.DBSCAN(data, size=0.002, min_samples=5)

    isolated_label = labels[-1]
    assert isolated_label == -1, (
        f"Isolated point should be an outlier (label -1), got {isolated_label}"
    )


def test_spatially_separate_groups_produce_distinct_cluster_boundaries(cleaned_poi_df_two_groups):
    # Cardiff group: indices 0-14, Bristol group: indices 15-29
    cardiff_coords = cleaned_poi_df_two_groups[['lat', 'lon']].iloc[:15].values.tolist()
    bristol_coords = cleaned_poi_df_two_groups[['lat', 'lon']].iloc[15:].values.tolist()
    all_coords = cardiff_coords + bristol_coords

    labels = clustering.DBSCAN(all_coords, size=0.002, min_samples=5)

    cardiff_labels = set(labels[:15]) - {-1}
    bristol_labels = set(labels[15:]) - {-1}

    assert len(cardiff_labels) > 0, "Cardiff points should form at least one cluster"
    assert len(bristol_labels) > 0, "Bristol points should form at least one cluster"
    assert cardiff_labels.isdisjoint(bristol_labels), (
        "Cardiff and Bristol clusters should have different cluster IDs"
    )


# ---------------------------------------------------------------------------
# Convex hull / cluster shape generation
# ---------------------------------------------------------------------------

def test_two_distinct_clusters_produce_two_boundary_polygons():
    import pandas as pd

    rng = np.random.default_rng(1)
    # Cluster 0: near Cardiff
    lats_a = 51.4816 + rng.uniform(-0.001, 0.001, 8)
    lons_a = -3.1791 + rng.uniform(-0.001, 0.001, 8)
    # Cluster 1: near Bristol (clearly separated)
    lats_b = 51.4545 + rng.uniform(-0.001, 0.001, 8)
    lons_b = -2.5879 + rng.uniform(-0.001, 0.001, 8)

    df = pd.DataFrame({
        'unique reference number': [str(i) for i in range(16)],
        'name': [f'POI {i}' for i in range(16)],
        'pointX classification code': ['03170245'] * 16,
        'lon': np.concatenate([lons_a, lons_b]),
        'lat': np.concatenate([lats_a, lats_b]),
        'group': ['Attractions'] * 16,
        'category': ['Historical and cultural'] * 16,
        'class': ['Historic and ceremonial structures'] * 16,
        'cluster id': [0] * 8 + [1] * 8,
    })

    # create_cluster_data expects numpy integers (as produced by DBSCAN), not plain ints
    lons, lats, colors = clustering.create_cluster_data(
        df, {np.int32(0), np.int32(1)}, index_bin=[]
    )

    assert len(lons) == 2, f"Expected 2 boundary polygons, got {len(lons)}"
    assert len(lats) == 2
    assert len(colors) == 2


# ---------------------------------------------------------------------------
# Rasterisation
# ---------------------------------------------------------------------------

def test_rasterised_polygon_has_filled_interior():
    # Unit square (inset slightly to ensure interior points exist)
    square = [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]
    grid = spatial_analysis.rasterise_shape(square, grid_size=50, bounds=(0, 1, 0, 1))

    assert grid.sum() > 0, "Rasterised polygon should contain filled interior cells"
    assert grid.sum() < 50 * 50, "Not every cell should be inside the polygon"


# ---------------------------------------------------------------------------
# Known bug capture
# ---------------------------------------------------------------------------

def test_spatial_correlation_is_currently_broken():
    spatial_analysis.compute_correlation('0', 'E02006827')
