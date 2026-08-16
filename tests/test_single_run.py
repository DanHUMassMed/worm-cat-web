import glob
import os
import shutil
from pathlib import Path
import pytest
from worm_cat_app import app

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORM_CAT_DIR = PROJECT_ROOT / "worm_cat"
SAMPLE_INPUT = WORM_CAT_DIR / "static" / "download" / "sams-1_up.csv"
DYNAMIC_DIR = WORM_CAT_DIR / "static" / "dynamic"
DOWNLOAD_DIR = WORM_CAT_DIR / "static" / "download"


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def cleanup_test_artifacts(monkeypatch):
    monkeypatch.chdir(WORM_CAT_DIR)
    yield
    # Clean up any test run directories and zip files
    for test_dir in glob.glob(str(DYNAMIC_DIR / "*Sams1-Single-Test*")):
        if os.path.isdir(test_dir):
            shutil.rmtree(test_dir, ignore_errors=True)
    for test_zip in glob.glob(str(DOWNLOAD_DIR / "*Sams1-Single-Test*.zip")):
        if os.path.isfile(test_zip):
            os.remove(test_zip)


def test_single_run_with_sams_1_up_upload(client):
    """Test single dataset analysis by uploading sams-1_up.csv."""
    with open(SAMPLE_INPUT, "rb") as f:
        upload_resp = client.post(
            "/sendfile",
            data={"file2upload": (f, "sams-1_up.csv")},
            content_type="multipart/form-data",
        )
    assert upload_resp.status_code == 200
    assert upload_resp.data == b"successful_upload"

    response = client.post(
        "/index",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "title": "Sams1 Single Test Upload",
            "annotation_type": "whole_genome_v2",
            "input_type": "Wormbase.ID",
            "rgs": "placeholder",
        },
    )

    assert response.status_code == 200
    assert b"WormCat Report" in response.data
    assert b"Category One" in response.data
    assert b"rgs_fisher_cat1_apv.svg" in response.data
    assert b"Wormcat Error" not in response.data


def test_single_run_with_sams_1_up_text_input(client):
    """Test single dataset analysis by pasting genes from sams-1_up.csv into textarea."""
    with open(SAMPLE_INPUT, "r") as f:
        lines = f.readlines()
    # Skip header line if present
    gene_text = "".join(lines[1:])

    response = client.post(
        "/index",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "title": "Sams1 Single Test Text",
            "annotation_type": "whole_genome_v2",
            "input_type": "Wormbase.ID",
            "rgs": gene_text,
        },
    )

    assert response.status_code == 200
    assert b"WormCat Report" in response.data
    assert b"Category One" in response.data
    assert b"rgs_fisher_cat1_apv.svg" in response.data
    assert b"Wormcat Error" not in response.data
