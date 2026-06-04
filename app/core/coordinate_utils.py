import pyproj


def create_bng_transformer():
    """Returns a transformer from British National Grid (EPSG:27700) to WGS84 lat/lon (EPSG:4326)."""
    return pyproj.Transformer.from_crs('EPSG:27700', 'EPSG:4326')
