from app.llm.redaction import redact


def test_redact_email_phone():
    s = redact("mail me at ada@school.edu or 9876543210")
    assert "<email>" in s
    assert "<phone>" in s
    assert "ada@" not in s
