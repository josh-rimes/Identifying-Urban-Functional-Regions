from classification import color_map, groups
from data_utilities import classify_data


def test_every_group_has_a_display_color():
    for group_name in groups.values():
        assert group_name in color_map, (
            f"Group '{group_name}' has no entry in color_map"
        )


def test_no_orphaned_colors():
    group_names = set(groups.values())
    for color_key in color_map:
        assert color_key in group_names, (
            f"color_map key '{color_key}' does not match any known group"
        )


def test_known_poi_code_resolves_to_correct_group():
    # 03170245: group '03' → 'Attractions'
    assert classify_data(1, '03170245') == 'Attractions'


def test_known_poi_code_resolves_to_correct_category():
    # 03170245: category '17' → 'Historical and cultural'
    assert classify_data(2, '03170245') == 'Historical and cultural'


def test_known_poi_code_resolves_to_correct_class():
    # 03170245: class '0245' → 'Historic and ceremonial structures'
    assert classify_data(3, '03170245') == 'Historic and ceremonial structures'


def test_unrecognised_poi_code_returns_no_classification():
    assert classify_data(1, 'XXXXXXXX') is None
    assert classify_data(2, 'XXXXXXXX') is None
    assert classify_data(3, 'XXXXXXXX') is None
