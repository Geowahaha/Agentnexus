"""Tests for URL auto-normalization."""

from app.utils.url_normalize import extract_target_url, normalize_expert_skill_task

CASES = [
    ("aibotauth.com", "https://aibotauth.com"),
    ("www.aibotauth.com", "https://www.aibotauth.com"),
    ("https://aibotauth.com", "https://aibotauth.com"),
    ("http://aibotauth.com", "http://aibotauth.com"),
    ("  aibotauth.com  ", "https://aibotauth.com"),
    ("aibotauth.com keywords: seo audit", "https://aibotauth.com keywords: seo audit"),
]

INVALID = ["aibotauth", "", "   ", "not a url", "ftp://bad.com"]


def test_normalize_cases() -> None:
    for raw, expected in CASES:
        assert normalize_expert_skill_task(raw) == expected, f"normalize({raw!r})"
        assert extract_target_url(raw) == expected.split()[0], f"extract({raw!r})"


def test_invalid_returns_none() -> None:
    for raw in INVALID:
        if raw.strip() in ("", "ftp://bad.com"):
            continue
        if raw == "ftp://bad.com":
            assert extract_target_url(raw) is None
            continue
        assert extract_target_url(raw) is None, f"expected None for {raw!r}"


def main() -> None:
    test_normalize_cases()
    test_invalid_returns_none()
    print("test_url_normalize: OK")


if __name__ == "__main__":
    main()