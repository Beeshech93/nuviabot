import io


def test_analytics_summary_endpoint(client, auth_headers):
    res = client.get("/api/v1/analytics/summary?days=30", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_connected_accounts" in data
    assert "total_followers" in data
    assert "by_platform" in data
    assert "instagram" in data["by_platform"]
    assert "facebook" in data["by_platform"]


def test_analytics_csv_export(client, auth_headers):
    res = client.get("/api/v1/analytics/export-csv", headers=auth_headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    content = res.text
    assert "NUVIO GROWTH BOT" in content
    assert "Total Connected Accounts" in content


def test_analytics_executive_report_view(client, auth_headers):
    res = client.get("/api/v1/analytics/report-view?days=30", headers=auth_headers)
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    content = res.text
    assert "NUVIO GROWTH BOT" in content
    assert "Informe Ejecutivo" in content


def test_media_upload_validation(client, auth_headers):
    # Test uploading an invalid text file as media
    invalid_file = io.BytesIO(b"this is just plain text")
    res = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        files={"file": ("malicious.txt", invalid_file, "text/plain")},
        data={"folder": "General"},
    )
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]

    # Test uploading a valid image file
    valid_png = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
    res_valid = client.post(
        "/api/v1/media/upload",
        headers=auth_headers,
        files={"file": ("banner.png", valid_png, "image/png")},
        data={"folder": "Banners", "tags": "promo,summer"},
    )
    assert res_valid.status_code == 200
    asset = res_valid.json()
    assert asset["mime_type"] == "image/png"
    assert asset["folder"] == "Banners"
    assert asset["file_url"].startswith("/static/uploads/")

