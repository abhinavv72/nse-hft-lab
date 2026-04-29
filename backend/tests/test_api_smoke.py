from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_market_state_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/market/state")
        assert response.status_code == 200
        payload = response.json()
        assert "session" in payload
        assert "portfolio" in payload
        assert "news" in payload
        assert "signals" in payload


def test_news_and_signals_endpoints():
    with TestClient(app) as client:
        news_response = client.get("/api/news")
        assert news_response.status_code == 200
        news_payload = news_response.json()
        assert "articles" in news_payload
        assert len(news_payload["articles"]) >= 1

        signal_response = client.get("/api/signals")
        assert signal_response.status_code == 200
        signal_payload = signal_response.json()
        assert "signals" in signal_payload
        assert len(signal_payload["signals"]) >= 1
