from ember.web_search import (
    WebSearchRequest,
    is_direct_chrome_open_request,
    parse_web_search_request,
)


def test_parse_arabic_search_request() -> None:
    assert parse_web_search_request("افتح جوجل وابحث عن صور قطط") == (
        WebSearchRequest(query="صور قطط")
    )


def test_parse_english_search_request_with_host() -> None:
    assert parse_web_search_request(
        "Open https://www.google.com and search for desktop companions."
    ) == WebSearchRequest(query="desktop companions", host="google.com")


def test_non_search_messages_are_not_interpreted_as_web_searches() -> None:
    assert parse_web_search_request("How can I help you focus?") is None
    assert parse_web_search_request("Search for") is None


def test_direct_chrome_open_requests_are_recognized_without_matching_questions() -> None:
    assert is_direct_chrome_open_request("افتح جوجل كروم")
    assert is_direct_chrome_open_request("ممكن شغل كروم؟")
    assert is_direct_chrome_open_request("Please open Google Chrome.")
    assert not is_direct_chrome_open_request("How do I open Chrome?")
    assert not is_direct_chrome_open_request("Open Chrome and search for cats")
