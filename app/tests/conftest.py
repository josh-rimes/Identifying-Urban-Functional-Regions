import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# POI fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def raw_poi_df():
    """Minimal raw POI DataFrame as produced by parse_contents from a valid file.

    Column A holds the full pipe-delimited record string; columns B-E are the
    remaining (empty) CSV columns that the real OS POI export produces.
    BNG coordinates (easting, northing) are real Cardiff-area values.
    """
    return pd.DataFrame({
        'A': [
            '10000001|War Memorial|03170245|317996|174906|1||extra',
            '10000002|Gospel Hall|06340459|317466|175278|1||extra',
            '10000003|Cafe Central|02020013|316000|174000|1||extra',
        ],
        'B': [np.nan, np.nan, np.nan],
        'C': [np.nan, np.nan, np.nan],
        'D': [np.nan, np.nan, np.nan],
        'E': [np.nan, np.nan, np.nan],
    })


@pytest.fixture
def raw_poi_df_with_bad_row():
    """Raw POI DataFrame where the last row is malformed (too few pipe fields)."""
    return pd.DataFrame({
        'A': [
            '10000001|War Memorial|03170245|317996|174906|1||extra',
            '10000002|Gospel Hall|06340459|317466|175278|1||extra',
            'bad_row_no_pipes',
        ],
        'B': [np.nan, np.nan, np.nan],
        'C': [np.nan, np.nan, np.nan],
        'D': [np.nan, np.nan, np.nan],
        'E': [np.nan, np.nan, np.nan],
    })


@pytest.fixture
def cleaned_poi_df():
    """30 Attractions POIs tightly clustered near Cardiff city centre.

    All share classification code 03170245 (Attractions / Historical and
    cultural / Historic and ceremonial structures). Points are spread within
    ±0.0005 degrees — well within the default DBSCAN eps of 0.002 — so they
    should all end up in a single cluster.
    """
    rng = np.random.default_rng(42)
    n = 30
    lats = 51.4816 + rng.uniform(-0.0005, 0.0005, n)
    lons = -3.1791 + rng.uniform(-0.0005, 0.0005, n)
    return pd.DataFrame({
        'unique reference number': [str(10000000 + i) for i in range(n)],
        'name': [f'POI {i}' for i in range(n)],
        'pointX classification code': ['03170245'] * n,
        'lon': lons,
        'lat': lats,
        'group': ['Attractions'] * n,
        'category': ['Historical and cultural'] * n,
        'class': ['Historic and ceremonial structures'] * n,
    })


@pytest.fixture
def cleaned_poi_df_two_groups():
    """30 Attractions POIs split into two geographically distant clusters.

    15 points near Cardiff, 15 near Bristol (~55 km apart). Both use the same
    Attractions classification so they are processed in the same DBSCAN pass,
    meaning they must end up in separate clusters.
    """
    rng = np.random.default_rng(42)
    n = 15
    lats_cardiff = 51.4816 + rng.uniform(-0.0005, 0.0005, n)
    lons_cardiff = -3.1791 + rng.uniform(-0.0005, 0.0005, n)
    lats_bristol = 51.4545 + rng.uniform(-0.0005, 0.0005, n)
    lons_bristol = -2.5879 + rng.uniform(-0.0005, 0.0005, n)
    return pd.DataFrame({
        'unique reference number': [str(20000000 + i) for i in range(n * 2)],
        'name': [f'POI {i}' for i in range(n * 2)],
        'pointX classification code': ['03170245'] * (n * 2),
        'lon': np.concatenate([lons_cardiff, lons_bristol]),
        'lat': np.concatenate([lats_cardiff, lats_bristol]),
        'group': ['Attractions'] * (n * 2),
        'category': ['Historical and cultural'] * (n * 2),
        'class': ['Historic and ceremonial structures'] * (n * 2),
    })


# ---------------------------------------------------------------------------
# Socio-economic fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def raw_se_df():
    """Minimal ONS SE DataFrame with two MSOA rows and one non-MSOA row.

    Uses BNG (EPSG:27700) centroid coordinates for Cardiff-area MSOAs.
    """
    return pd.DataFrame({
        'area_code':        ['E02006827', 'E02006828', 'E01033470'],
        'area_name':        ['Adamsdown', 'Butetown', 'Roath LSOA'],
        'census_geography': ['msoa',      'msoa',      'lsoa'],
        'centroid_x':       [319478.0,    320200.0,    318000.0],
        'centroid_y':       [176455.0,    174900.0,    175500.0],
        'deprivation_score': [15.2,        22.7,        8.1],
        'employment_rate':   [72.1,        68.4,        80.3],
    })


# ---------------------------------------------------------------------------
# Global state reset
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_index_bin():
    """Ensure poi_handling.index_bin is clean before and after every test.

    poi_handling.index_bin is a mutable module-level variable that is written
    by clean_POI_data.  Without this reset, state from one test leaks into the
    next when tests run in sequence.
    """
    import poi_handling
    poi_handling.index_bin = []
    yield
    poi_handling.index_bin = []
