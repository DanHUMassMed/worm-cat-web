import os
import tempfile
from utils.email_utility import construct_message_with_html, construct_message_with_attachment


def test_construct_message_with_html():
    msg = construct_message_with_html(
        subject="Test Subject",
        sender="sender@example.com",
        receiver="receiver@example.com",
        message_text="Hello text",
        message_html="<p>Hello HTML</p>",
    )
    assert "Subject: Test Subject" in msg
    assert "To: receiver@example.com" in msg
    assert "From: sender@example.com" in msg
    assert "Hello text" in msg


def test_construct_message_with_attachment():
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        f.write(b"dummy zip content")
        temp_path = f.name

    try:
        msg = construct_message_with_attachment(
            subject="Results",
            sender="sender@example.com",
            receiver="receiver@example.com",
            message_text="Here are your results",
            the_file=temp_path,
        )
        assert "Subject: Results" in msg
        assert "To: receiver@example.com" in msg
        assert "From: sender@example.com" in msg
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
