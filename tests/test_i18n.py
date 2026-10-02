from anti_dating_scam_desktop import i18n


def test_bi_returns_only_the_selected_language() -> None:
    i18n.set_language("en", persist=False)
    assert i18n.bi("Hello", "你好") == "Hello"

    i18n.set_language("zh", persist=False)
    assert i18n.bi("Hello", "你好") == "你好"

    i18n.set_language("en", persist=False)  # reset for other tests


def test_bi_never_concatenates_languages() -> None:
    i18n.set_language("en", persist=False)
    result = i18n.bi("Settings", "设置")
    assert "/" not in result
    assert result == "Settings"


def test_bi_falls_back_when_one_language_missing() -> None:
    i18n.set_language("zh", persist=False)
    assert i18n.bi("/only/a/path", "") == "/only/a/path"
    i18n.set_language("en", persist=False)


def test_toggle_flips_language() -> None:
    i18n.set_language("en", persist=False)
    assert i18n.toggle_language(persist=False) == "zh"
    assert i18n.toggle_language(persist=False) == "en"


def test_other_language_label() -> None:
    i18n.set_language("en", persist=False)
    assert i18n.other_language_label() == "中文"
    i18n.set_language("zh", persist=False)
    assert i18n.other_language_label() == "English"
    i18n.set_language("en", persist=False)
