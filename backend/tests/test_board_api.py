from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_get_board_bootstraps_default_for_new_user(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.db"
    client = TestClient(create_app(
        static_dir=tmp_path / "missing", db_path=db_path))

    response = client.get("/api/board/alice")
    assert response.status_code == 200
    body = response.json()
    assert db_path.exists()
    assert len(body["columns"]) == 5
    assert "card-1" in body["cards"]


def test_put_board_persists_and_can_be_read_back(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.db"
    client = TestClient(create_app(
        static_dir=tmp_path / "missing", db_path=db_path))

    payload = {
        "columns": [
            {"id": "col-a", "title": "Todo", "cardIds": ["card-1"]},
            {"id": "col-b", "title": "Done", "cardIds": []},
        ],
        "cards": {
            "card-1": {"id": "card-1", "title": "Updated", "details": "Saved"},
        },
    }

    put_response = client.put("/api/board/alice", json=payload)
    assert put_response.status_code == 200

    get_response = client.get("/api/board/alice")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["columns"][0]["title"] == "Todo"
    assert body["cards"]["card-1"]["title"] == "Updated"


def test_put_board_rejects_invalid_card_references(tmp_path: Path) -> None:
    db_path = tmp_path / "pm.db"
    client = TestClient(create_app(
        static_dir=tmp_path / "missing", db_path=db_path))

    payload = {
        "columns": [{"id": "col-a", "title": "Todo", "cardIds": ["card-99"]}],
        "cards": {},
    }

    response = client.put("/api/board/alice", json=payload)
    assert response.status_code == 400
    assert "referenced but missing" in response.json()["detail"]
