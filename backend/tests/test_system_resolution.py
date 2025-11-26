"""
Tests for system_resolution utility function.
"""
import pytest
from app.utils.system_resolution import get_system_resolution


def test_get_system_resolution():
    """Test that get_system_resolution returns a valid result."""
    result = get_system_resolution()
    
    assert isinstance(result, dict)
    assert "width" in result
    assert "height" in result
    assert isinstance(result["width"], int)
    assert isinstance(result["height"], int)
    assert result["width"] > 0
    assert result["height"] > 0

