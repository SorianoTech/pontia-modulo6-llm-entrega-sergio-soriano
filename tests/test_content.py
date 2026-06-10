from app.services.content import get_info_cards


def test_get_info_cards_returns_three_sections() -> None:
    cards = get_info_cards()

    assert len(cards) == 3
    assert cards[0].title == "Tenerife norte"

