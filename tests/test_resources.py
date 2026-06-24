from __future__ import annotations

import pytest

from kuksa_mcp_server.server import create_server


@pytest.fixture
def server():
    return create_server()


def test_resources_are_registered(server):
    """Verify all expected resources and templates are registered."""
    resources = server._resource_manager.list_resources()
    templates = server._resource_manager.list_templates()
    total = len(resources) + len(templates)
    assert total >= 3, f"Expected at least 3 resources, got {total}"


def test_static_resource_uris(server):
    """Static (non-template) resources should include kuksa://info."""
    uris = [str(r.uri) for r in server._resource_manager.list_resources()]
    assert "kuksa://info" in uris, f"kuksa://info not found in {uris}"


def test_template_resource_uris(server):
    """Template resources should include signal and branch patterns."""
    uris = [t.uri_template for t in server._resource_manager.list_templates()]
    assert "kuksa://signals/{path}" in uris
    assert "kuksa://branches/{path}" in uris


def test_templates_require_path_param(server):
    """Template resources should have a 'path' parameter."""
    for tmpl in server._resource_manager.list_templates():
        props = tmpl.parameters.get("properties", {})
        assert "path" in props, f"Template {tmpl.uri_template} missing 'path' param"
