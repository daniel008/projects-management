import pytest

from app.board_service import validate_board_payload
from app.schemas import BoardPayload


def test_validate_board_payload_accepts_valid_board() -> None:
    board = BoardPayload.model_validate(
        {
            "columns": [
                {"id": "col-a", "title": "A", "cardIds": ["card-1"]},
                {"id": "col-b", "title": "B", "cardIds": ["card-2"]},
            ],
            "cards": {
                "card-1": {"id": "card-1", "title": "Card 1", "details": "D1"},
                "card-2": {"id": "card-2", "title": "Card 2", "details": "D2"},
            },
        }
    )
    validate_board_payload(board)


def test_validate_board_payload_rejects_missing_card_reference() -> None:
    board = BoardPayload.model_validate(
        {
            "columns": [{"id": "col-a", "title": "A", "cardIds": ["card-1"]}],
            "cards": {},
        }
    )
    with pytest.raises(ValueError, match="referenced but missing"):
        validate_board_payload(board)


def test_validate_board_payload_rejects_duplicate_card_placement() -> None:
    board = BoardPayload.model_validate(
        {
            "columns": [
                {"id": "col-a", "title": "A", "cardIds": ["card-1"]},
                {"id": "col-b", "title": "B", "cardIds": ["card-1"]},
            ],
            "cards": {
                "card-1": {"id": "card-1", "title": "Card 1", "details": "D1"},
            },
        }
    )
    with pytest.raises(ValueError, match="multiple columns"):
        validate_board_payload(board)


def test_validate_board_payload_rejects_orphan_card() -> None:
    board = BoardPayload.model_validate(
        {
            "columns": [{"id": "col-a", "title": "A", "cardIds": []}],
            "cards": {
                "card-1": {"id": "card-1", "title": "Card 1", "details": "D1"},
            },
        }
    )
    with pytest.raises(ValueError, match="exactly once"):
        validate_board_payload(board)
