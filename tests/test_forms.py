import pytest
from flask import Flask
from forms import WormCatForm, BatchForm


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def test_wormcat_form_valid(app):
    with app.test_request_context():
        form = WormCatForm(
            name="Test User",
            email="test@example.com",
            title="Test Dataset",
            annotation_type="whole_genome_v2",
            input_type="Sequence.ID",
            rgs="W02A11.1\nW02A11.2\n",
        )
        assert form.validate() is True


def test_wormcat_form_missing_required_fields(app):
    with app.test_request_context():
        form = WormCatForm(
            name="",
            email="",
            title="",
            annotation_type="whole_genome_v2",
            input_type="Sequence.ID",
            rgs="",
        )
        assert form.validate() is False
        assert "name" in form.errors
        assert "email" in form.errors
        assert "title" in form.errors
        assert "rgs" in form.errors


def test_batch_form(app):
    with app.test_request_context():
        form = BatchForm(
            email="user@test.org",
            xsl_file_nm="/tmp/test.xlsx",
            batch_user="Test Batch",
            annotation_file="whole_genome_v2_nov-11-2021.csv",
        )
        assert form.email.data == "user@test.org"
        assert form.batch_user.data == "Test Batch"
