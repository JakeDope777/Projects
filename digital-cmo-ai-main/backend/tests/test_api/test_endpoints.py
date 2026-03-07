"""
Integration tests for API endpoints.
"""

import pytest


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert "modules" in data

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_signup(self, client):
        response = client.post(
            "/auth/signup",
            json={"email": "new_user@example.com", "password": "securepassword123"},
        )
        assert response.status_code in (201, 409)  # 409 if already exists
        if response.status_code == 201:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data

    def test_login(self, client):
        # First signup
        client.post(
            "/auth/signup",
            json={"email": "login_test@example.com", "password": "testpass123"},
        )
        # Then login
        response = client.post(
            "/auth/login",
            json={"email": "login_test@example.com", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client):
        client.post(
            "/auth/signup",
            json={"email": "wrongpass@example.com", "password": "correct"},
        )
        response = client.post(
            "/auth/login",
            json={"email": "wrongpass@example.com", "password": "incorrect"},
        )
        assert response.status_code == 401


class TestChatEndpoints:
    """Tests for chat endpoints."""

    def test_send_message(self, client):
        response = client.post(
            "/chat",
            json={"message": "Hello, what can you do?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "conversation_id" in data

    def test_send_message_with_conversation_id(self, client):
        # First message
        r1 = client.post("/chat", json={"message": "First message"})
        conv_id = r1.json()["conversation_id"]
        # Follow-up
        r2 = client.post(
            "/chat",
            json={"message": "Follow up", "conversation_id": conv_id},
        )
        assert r2.json()["conversation_id"] == conv_id

    def test_get_conversation(self, client):
        r1 = client.post("/chat", json={"message": "Test"})
        conv_id = r1.json()["conversation_id"]
        response = client.get(f"/chat/{conv_id}")
        assert response.status_code == 200

    def test_get_nonexistent_conversation(self, client):
        response = client.get("/chat/nonexistent-id")
        assert response.status_code == 404


class TestAnalysisEndpoints:
    """Tests for business analysis endpoints."""

    def test_market_analysis(self, client):
        response = client.post(
            "/analysis/market",
            json={"query": "SaaS market in Europe"},
        )
        assert response.status_code == 200

    def test_swot_analysis(self, client):
        response = client.post(
            "/analysis/swot",
            json={"subject": "Our product launch"},
        )
        assert response.status_code == 200

    def test_pestel_analysis(self, client):
        response = client.post(
            "/analysis/pestel",
            json={"subject": "European tech market"},
        )
        assert response.status_code == 200

    def test_competitor_analysis(self, client):
        response = client.post(
            "/analysis/competitors",
            json={"company_names": ["Company A", "Company B"]},
        )
        assert response.status_code == 200

    def test_persona_generation(self, client):
        response = client.post(
            "/analysis/personas",
            json={"data_source": "general", "num_personas": 2},
        )
        assert response.status_code == 200


class TestCreativeEndpoints:
    """Tests for creative & design endpoints."""

    def test_generate_copy(self, client):
        response = client.post(
            "/creative/generate",
            json={"brief": "Write a LinkedIn post about AI"},
        )
        assert response.status_code == 200

    def test_generate_image(self, client):
        response = client.post(
            "/creative/image",
            json={"description": "Modern tech banner"},
        )
        assert response.status_code == 200

    def test_ab_test(self, client):
        response = client.post(
            "/creative/ab-test",
            json={"base_copy": "Buy now and save 20%!"},
        )
        assert response.status_code == 200

    def test_content_schedule(self, client):
        response = client.post(
            "/creative/schedule",
            json={"events": []},
        )
        assert response.status_code == 200


class TestCRMEndpoints:
    """Tests for CRM & campaign endpoints."""

    def test_create_lead(self, client):
        response = client.post(
            "/crm/lead",
            json={"lead_id": "lead-api-001", "attributes": {"name": "Test Lead"}},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    def test_create_campaign(self, client):
        response = client.post(
            "/crm/campaign",
            json={"name": "Test Campaign", "channel": "email"},
        )
        assert response.status_code == 200

    def test_trigger_workflow(self, client):
        response = client.post(
            "/crm/workflow",
            json={"workflow_id": "welcome_series", "lead_id": "lead-wf-001"},
        )
        assert response.status_code == 200

    def test_check_compliance(self, client):
        response = client.post(
            "/crm/compliance",
            json={"message": "Buy now!", "channel": "email"},
        )
        assert response.status_code == 200

    def test_list_leads(self, client):
        response = client.get("/crm/leads")
        assert response.status_code == 200

    def test_list_campaigns(self, client):
        response = client.get("/crm/campaigns")
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Tests for analytics & reporting endpoints."""

    def test_get_dashboard(self, client):
        response = client.get("/analytics/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data

    def test_get_forecast(self, client):
        response = client.post(
            "/analytics/forecast",
            json={"metric": "revenue", "horizon": 14},
        )
        assert response.status_code == 200

    def test_record_experiment(self, client):
        response = client.post(
            "/analytics/experiment",
            json={
                "experiment_id": "exp-api-001",
                "variants": [
                    {"name": "Control", "sample_size": 1000, "conversions": 50},
                    {"name": "Variant A", "sample_size": 1000, "conversions": 70},
                ],
            },
        )
        assert response.status_code == 200


class TestMemoryEndpoints:
    """Tests for memory endpoints."""

    def test_store_memory(self, client):
        response = client.post(
            "/memory/store",
            json={"file_path": "workspace/test.md", "content": "Test content"},
        )
        assert response.status_code == 200

    def test_list_memory_files(self, client):
        response = client.get("/memory/files")
        assert response.status_code == 200

    def test_retrieve_memories(self, client):
        response = client.post(
            "/memory/retrieve",
            json={"query": "marketing budget"},
        )
        assert response.status_code == 200
