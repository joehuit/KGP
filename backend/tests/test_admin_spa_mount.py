"""Automated tests verifying admin SPA static mount on the backend."""

from fastapi.testclient import TestClient


def test_root_endpoint_includes_admin_dashboard_url(client: TestClient):
    """Test that GET / returns the admin dashboard route."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["admin_dashboard"] == "/admin"


def test_admin_dashboard_static_assets_served(client: TestClient):
    """Test that GET /admin/ serves index.html and all referenced JS/CSS assets resolve with 200 OK and valid MIME types."""
    res = client.get("/admin/")
    assert res.status_code == 200
    assert '<div id="root"></div>' in res.text
    assert "KGP LIST" in res.text

    # Extract script src and stylesheet href from rendered HTML
    js_src = None
    css_href = None
    for line in res.text.splitlines():
        if '<script' in line and 'src="' in line:
            start = line.find('src="') + 5
            end = line.find('"', start)
            js_src = line[start:end]
        if '<link' in line and 'rel="stylesheet"' in line and 'href="' in line:
            start = line.find('href="') + 6
            end = line.find('"', start)
            css_href = line[start:end]

    assert js_src is not None, "JavaScript module script tag not found in index.html"
    assert css_href is not None, "Stylesheet link tag not found in index.html"

    # Verify paths are correctly prefixed under /admin/ (Vite base: '/admin/')
    assert js_src.startswith("/admin/assets/"), f"JS asset path '{js_src}' must start with '/admin/assets/'"
    assert css_href.startswith("/admin/assets/"), f"CSS asset path '{css_href}' must start with '/admin/assets/'"

    # 1. Verify JavaScript asset resolves with HTTP 200 and text/javascript MIME type
    js_res = client.get(js_src)
    assert js_res.status_code == 200, f"Referenced JS asset '{js_src}' returned {js_res.status_code}"
    assert "javascript" in js_res.headers.get("content-type", "").lower()
    assert len(js_res.content) > 1000

    # 2. Verify CSS asset resolves with HTTP 200 and text/css MIME type
    css_res = client.get(css_href)
    assert css_res.status_code == 200, f"Referenced CSS asset '{css_href}' returned {css_res.status_code}"
    assert "text/css" in css_res.headers.get("content-type", "").lower()
    assert len(css_res.content) > 100

    # 3. Verify incorrect un-prefixed root paths return 404 (no accidental /assets fallback)
    raw_js_filename = js_src.replace("/admin/assets/", "")
    bad_root_asset = client.get(f"/assets/{raw_js_filename}")
    assert bad_root_asset.status_code == 404, "Root /assets/ request must return 404 (not masked by fallback)"


def test_admin_dashboard_nested_routes_fallback_and_missing_assets(client: TestClient):
    """Test that refreshing nested SPA paths returns index.html, while missing assets return 404."""
    # 1. Nested SPA route returns index.html (200 OK)
    res_orders = client.get("/admin/orders")
    assert res_orders.status_code == 200
    assert '<div id="root"></div>' in res_orders.text

    res_products = client.get("/admin/products")
    assert res_products.status_code == 200
    assert '<div id="root"></div>' in res_products.text

    # 2. Missing asset returns 404 Not Found
    res_missing = client.get("/admin/assets/non_existent_file.js")
    assert res_missing.status_code == 404


def test_security_headers_enforced(client: TestClient):
    """Test that HTTP responses include standard security headers."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "1; mode=block" in res.headers.get("X-XSS-Protection", "")

