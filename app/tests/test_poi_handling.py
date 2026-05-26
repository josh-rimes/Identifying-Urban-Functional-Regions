import poi_handling


# ---------------------------------------------------------------------------
# clean_POI_data
# ---------------------------------------------------------------------------

def test_well_formed_poi_file_produces_valid_output(raw_poi_df):
    result = poi_handling.clean_POI_data(raw_poi_df.copy())

    required_columns = {'lon', 'lat', 'group', 'category', 'class',
                        'unique reference number', 'name',
                        'pointX classification code'}
    assert required_columns.issubset(result.columns), (
        f"Missing columns: {required_columns - set(result.columns)}"
    )

    # Every row should have a geographic coordinate
    assert result['lon'].notna().all(), "All rows should have a valid longitude"
    assert result['lat'].notna().all(), "All rows should have a valid latitude"

    # Every row should have resolved to a classification group
    assert result['group'].notna().all(), (
        "All rows should resolve to a group classification"
    )


def test_well_formed_poi_file_records_no_dropped_rows(raw_poi_df):
    poi_handling.clean_POI_data(raw_poi_df.copy())
    assert poi_handling.index_bin == [], (
        "No rows should be flagged as dropped for a fully valid file"
    )


def test_malformed_row_is_excluded_from_output(raw_poi_df_with_bad_row):
    result = poi_handling.clean_POI_data(raw_poi_df_with_bad_row.copy())

    # Only 2 of the original 3 rows are valid
    assert len(result) == 2, (
        f"Expected 2 rows after dropping malformed row, got {len(result)}"
    )


def test_malformed_row_removal_is_recorded(raw_poi_df_with_bad_row):
    poi_handling.clean_POI_data(raw_poi_df_with_bad_row.copy())

    assert len(poi_handling.index_bin) == 1, (
        "Exactly one row should be recorded as dropped"
    )
    assert 2 in poi_handling.index_bin, (
        "The dropped row should be index 2 (the malformed row)"
    )


# ---------------------------------------------------------------------------
# add_cluster_ids
# ---------------------------------------------------------------------------

def test_nearby_pois_of_same_type_share_a_cluster(cleaned_poi_df):
    result_df, cluster_data = poi_handling.add_cluster_ids(
        cleaned_poi_df.copy(),
        level=1,
        slider_value=0.002,
        min_samples=10,
    )

    assert 'cluster id' in result_df.columns, (
        "add_cluster_ids should add a 'cluster id' column"
    )

    assigned = result_df['cluster id'].dropna()
    assigned_valid = assigned[assigned >= 0]

    assert len(assigned_valid) > 0, "At least some POIs should be assigned a cluster"

    dominant_count = assigned_valid.value_counts().iloc[0]
    assert dominant_count >= 20, (
        f"Expected at least 20 of 30 tight POIs in one cluster, "
        f"got dominant cluster size {dominant_count}"
    )


def test_distant_pois_of_same_type_receive_different_cluster_ids(cleaned_poi_df_two_groups):
    result_df, cluster_data = poi_handling.add_cluster_ids(
        cleaned_poi_df_two_groups.copy(),
        level=1,
        slider_value=0.002,
        min_samples=5,
    )

    assigned = result_df['cluster id'].dropna()
    distinct_clusters = set(assigned[assigned >= 0])

    assert len(distinct_clusters) >= 2, (
        "Cardiff and Bristol POIs should produce at least two distinct clusters "
        f"(got cluster IDs: {distinct_clusters})"
    )
