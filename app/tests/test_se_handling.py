import se_handling


def test_only_msoa_rows_are_retained_after_cleaning(raw_se_df):
    result = se_handling.clean_se_data(raw_se_df.copy())
    assert (result['census_geography'] == 'msoa').all(), (
        "clean_se_data should remove all non-MSOA rows"
    )
    assert len(result) == 2, (
        "Only the two MSOA rows from the fixture should remain"
    )


def test_cleaned_se_data_has_valid_wgs84_coordinates(raw_se_df):
    result = se_handling.clean_se_data(raw_se_df.copy())
    # Cardiff-area MSOAs should land in the expected geographic range
    assert result['latitude'].between(51.0, 52.0).all(), (
        "Latitudes should be in the Cardiff area (~51° N)"
    )
    assert result['longitude'].between(-4.0, -3.0).all(), (
        "Longitudes should be in the Cardiff area (~3° W)"
    )


def test_all_indicator_columns_appear_as_selectable_layers(raw_se_df):
    result = se_handling.clean_se_data(raw_se_df.copy())
    layers = se_handling.get_layers(result)

    assert layers[0] == 'None', "First layer option should always be 'None'"
    assert 'deprivation_score' in layers
    assert 'employment_rate' in layers


def test_non_data_columns_are_not_offered_as_layers(raw_se_df):
    result = se_handling.clean_se_data(raw_se_df.copy())
    layers = se_handling.get_layers(result)

    for metadata_col in ('area_code', 'area_name', 'census_geography',
                         'latitude', 'longitude'):
        assert metadata_col not in layers, (
            f"Metadata column '{metadata_col}' should not appear as a layer"
        )
