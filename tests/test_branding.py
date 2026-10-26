import json
import pytest

from video2pptx.branding import BrandConfig


def test_brand_config_normalizes_colors(tmp_path):
    path = tmp_path / "brand.json"
    path.write_text(json.dumps({"primary_color": "#abcdef", "logo_position": "left-sidebar"}))
    config = BrandConfig.load(path)
    assert config.primary_color == "ABCDEF"
    assert config.logo_position == "left-sidebar"


def test_brand_config_rejects_unknown_fields(tmp_path):
    path = tmp_path / "brand.json"; path.write_text('{"mystery": true}')
    with pytest.raises(ValueError, match="Unknown"):
        BrandConfig.load(path)


def test_brand_config_rejects_bad_color():
    with pytest.raises(ValueError, match="hex color"):
        BrandConfig(primary_color="blue")

