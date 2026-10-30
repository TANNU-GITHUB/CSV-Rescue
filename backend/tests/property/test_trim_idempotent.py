from app.cleaning.actions.trim_whitespace import tidy


def test_tidy_idempotent():
    samples = ["  hi  ", "a  b", "\u00a0x\u200b", "Jaipur"]
    for s in samples:
        once = tidy(s, True)
        assert tidy(once, True) == once
