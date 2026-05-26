import base64

import pandas as pd
import pytest
from dash import html

from classification import classify_data
from loaders.file_parser import parse_contents


def _encode_upload(csv_text: str, filename: str) -> str:
    """Produce the base64 data-URL string that Dash passes to parse_contents."""
    encoded = base64.b64encode(csv_text.encode()).decode()
    return f"data:text/csv;base64,{encoded}"


# ---------------------------------------------------------------------------
# classify_data — classification granularity
# ---------------------------------------------------------------------------

def test_group_classification_is_broader_than_class_classification():
    group = classify_data(1, '03170245')   # 'Attractions'
    class_ = classify_data(3, '03170245')  # 'Historic and ceremonial structures'
    assert group is not None
    assert class_ is not None
    assert group != class_


def test_all_three_levels_return_distinct_labels():
    group    = classify_data(1, '03170245')
    category = classify_data(2, '03170245')
    class_   = classify_data(3, '03170245')
    assert len({group, category, class_}) == 3, (
        "Group, category and class labels should all differ for the same code"
    )


def test_unrecognised_code_returns_none_at_every_level():
    for level in (1, 2, 3):
        assert classify_data(level, 'XXXXXXXX') is None


# ---------------------------------------------------------------------------
# parse_contents — file upload handling
# ---------------------------------------------------------------------------

def test_valid_csv_upload_produces_usable_dataset():
    upload = _encode_upload("col1,col2\n1,2\n3,4\n", "data.csv")
    result = parse_contents(upload, "data.csv")
    assert isinstance(result, pd.DataFrame)
    assert not result.empty


def test_corrupted_upload_produces_error_not_crash():
    # base64.b64decode raises before the try/except in parse_contents — known bug
    upload = "data:text/csv;base64,!!!NOT_VALID_BASE64!!!"
    result = parse_contents(upload, "data.csv")
    assert isinstance(result, html.Div)


def test_unsupported_file_type_produces_error_not_crash():
    # When no format branch matches, 'df' is never assigned; return df raises
    # UnboundLocalError outside the try/except — known bug
    upload = _encode_upload("col1,col2\n1,2\n", "data.pdf")
    result = parse_contents(upload, "data.pdf")
    assert isinstance(result, html.Div)