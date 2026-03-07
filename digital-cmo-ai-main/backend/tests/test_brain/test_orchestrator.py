"""
Comprehensive tests for the Brain Orchestrator.

Tests cover:
- Message processing pipeline
- Intent routing integration
- Conversation state management
- Memory watcher integration
- Conversation summarization
- Task management
- LLM client wrapper
"""

import pytest
from app.brain.orchestrator import BrainOrchestrator, LLMClient
from app.brain.memory_manager import MemoryManager
from app.brain.conversation_state import ConversationStateManager


@pytest.fixture
def orchestrator(temp_memory_dir, tmp_path):
    llm = LLMClient()  # No API key = demo mode
    memory = MemoryManager(
        memory_base_path=temp_memory_dir,
        db_path=":memory:",
        vector_store=None,
    )
    state_manager = ConversationStateManager(persist_dir=str(tmp_path / "states"))
    return BrainOrchestrator(
        llm_client=llm,
        memory_manager=memory,
        state_manager=state_manager,
    )


# ---------------------------------------------------------------------------
# Message processing tests
# ---------------------------------------------------------------------------

class TestMessageProcessing:
    """Tests for the main message processing pipeline."""

    @pytest.mark.asyncio
    async def test_process_message_returns_reply(self, orchestrator):
        result = await orchestrator.process_message("Hello, what can you do?")
        assert "reply" in result
        assert "conversation_id" in result
        assert result["reply"] != ""

    @pytest.mark.asyncio
    async def test_process_message_has_metadata(self, orchestrator):
        result = await orchestrator.process_message("Tell me about analytics")
        assert "module_used" in result
        assert "classification_confidence" in result
        assert "classification_method" in result
        assert "tokens_used" in result
        assert "conversation_phase" in result
        assert "turn_count" in result

    @pytest.mark.asyncio
    async def test_conversation_id_persisted(self, orchestrator):
        result1 = await orchestrator.process_message("First message")
        conv_id = result1["conversation_id"]
        result2 = await orchestrator.process_message("Second message", conversation_id=conv_id)
        assert result2["conversation_id"] == conv_id

    @pytest.mark.asyncio
    async def test_turn_count_increments(self, orchestrator):
        result1 = await orchestrator.process_message("First")
        conv_id = result1["conversation_id"]
        assert result1["turn_count"] == 1

        result2 = await orchestrator.process_message("Second", conversation_id=conv_id)
        assert result2["turn_count"] == 2

    @pytest.mark.asyncio
    async def test_tokens_used_tracked(self, orchestrator):
        result = await orchestrator.process_message("Write some marketing copy")
        assert result["tokens_used"] > 0


# ---------------------------------------------------------------------------
# Intent routing tests
# ---------------------------------------------------------------------------

class TestIntentRouting:
    """Tests for intent routing integration."""

    @pytest.mark.asyncio
    async def test_business_analysis_routing(self, orchestrator):
        result = await orchestrator.process_message("Do a SWOT analysis for our product")
        assert result["module_used"] == "business_analysis"

    @pytest.mark.asyncio
    async def test_creative_routing(self, orchestrator):
        result = await orchestrator.process_message("Write a blog post about AI")
        assert result["module_used"] == "creative_design"

    @pytest.mark.asyncio
    async def test_general_routing(self, orchestrator):
        result = await orchestrator.process_message("Hello there")
        assert result["module_used"] == "general"

    @pytest.mark.asyncio
    async def test_analytics_routing(self, orchestrator):
        result = await orchestrator.process_message("Show me the KPI dashboard")
        assert result["module_used"] == "analytics_reporting"


# ---------------------------------------------------------------------------
# Conversation state tests
# ---------------------------------------------------------------------------

class TestConversationState:
    """Tests for conversation state management."""

    @pytest.mark.asyncio
    async def test_conversation_state_created(self, orchestrator):
        result = await orchestrator.process_message("Hello")
        conv_id = result["conversation_id"]
        state = orchestrator.get_conversation_state(conv_id)
        assert state is not None
        assert state["conversation_id"] == conv_id

    @pytest.mark.asyncio
    async def test_conversation_history_stored(self, orchestrator):
        result = await orchestrator.process_message("Hello")
        conv_id = result["conversation_id"]
        history = orchestrator.get_conversation(conv_id)
        assert len(history) >= 2  # user + assistant

    @pytest.mark.asyncio
    async def test_conversation_phase_tracked(self, orchestrator):
        result = await orchestrator.process_message("Hello")
        assert "conversation_phase" in result

    @pytest.mark.asyncio
    async def test_clear_conversation(self, orchestrator):
        result = await orchestrator.process_message("Test message")
        conv_id = result["conversation_id"]
        assert orchestrator.clear_conversation(conv_id) is True
        assert orchestrator.get_conversation(conv_id) == []

    def test_clear_nonexistent_conversation(self, orchestrator):
        assert orchestrator.clear_conversation("nonexistent") is False

    @pytest.mark.asyncio
    async def test_list_conversations(self, orchestrator):
        await orchestrator.process_message("Msg 1", user_context={"user_id": "u1"})
        await orchestrator.process_message("Msg 2", user_context={"user_id": "u1"})
        convs = orchestrator.list_conversations(user_id="u1")
        assert len(convs) >= 1


# ---------------------------------------------------------------------------
# Skill registration tests
# ---------------------------------------------------------------------------

class TestSkillRegistration:
    """Tests for skill module registration."""

    def test_register_skill(self, orchestrator):
        class MockSkill:
            async def handle(self, msg, ctx):
                return {"response": "mock response"}

        orchestrator.register_skill("test_skill", MockSkill())
        assert "test_skill" in orchestrator._skills

    @pytest.mark.asyncio
    async def test_registered_skill_invoked(self, orchestrator):
        class MockAnalyticsSkill:
            async def handle(self, msg, ctx):
                return {"response": "Analytics result: CTR is 3.5%"}

        orchestrator.register_skill("analytics_reporting", MockAnalyticsSkill())
        result = await orchestrator.process_message("Show me the analytics dashboard")
        assert "Analytics result" in result["reply"]

    @pytest.mark.asyncio
    async def test_skill_error_handled(self, orchestrator):
        class FailingSkill:
            async def handle(self, msg, ctx):
                raise RuntimeError("Skill crashed")

        orchestrator.register_skill("business_analysis", FailingSkill())
        result = await orchestrator.process_message("Do a SWOT analysis")
        assert "Skill Error" in result["reply"]


# ---------------------------------------------------------------------------
# Task management tests
# ---------------------------------------------------------------------------

class TestTaskManagement:
    """Tests for task slot-filling workflows."""

    @pytest.mark.asyncio
    async def test_start_task(self, orchestrator):
        result = await orchestrator.process_message("Hello")
        conv_id = result["conversation_id"]
        task_info = orchestrator.start_task(
            conv_id, "campaign_creation", "Create Q2 email campaign"
        )
        assert task_info is not None
        assert "task_id" in task_info
        assert len(task_info["missing_slots"]) > 0

    @pytest.mark.asyncio
    async def test_start_task_nonexistent_conversation(self, orchestrator):
        result = orchestrator.start_task("nonexistent", "campaign_creation")
        assert result is None

    @pytest.mark.asyncio
    async def test_slot_filling_workflow(self, orchestrator):
        # Start conversation
        result = await orchestrator.process_message("I want to create a campaign")
        conv_id = result["conversation_id"]

        # Start task with slots
        orchestrator.start_task(conv_id, "campaign_creation", "Create campaign")

        # Fill first slot
        result2 = await orchestrator.process_message(
            "Summer Sale 2025", conversation_id=conv_id
        )
        # Should acknowledge the slot fill
        if "active_task" in result2:
            assert result2["active_task"]["status"] in ("waiting_for_input", "in_progress")


# ---------------------------------------------------------------------------
# Memory integration tests
# ---------------------------------------------------------------------------

class TestMemoryIntegration:
    """Tests for memory watcher and retrieval integration."""

    @pytest.mark.asyncio
    async def test_important_facts_stored(self, orchestrator):
        # Send a message with important content
        result = await orchestrator.process_message(
            "Our brand guideline is to always use a professional tone and our budget is $50,000"
        )
        # The memory watcher should have extracted and stored facts
        # We can verify by searching for them
        memories = orchestrator.memory.retrieve_similar("brand guideline", k=5)
        # At least the fallback should have stored something
        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_memory_stats(self, orchestrator):
        stats = orchestrator.get_memory_stats()
        assert "folder_count" in stats
        assert "vector_store_available" in stats


# ---------------------------------------------------------------------------
# LLM Client tests
# ---------------------------------------------------------------------------

class TestLLMClient:
    """Tests for the LLM client wrapper."""

    @pytest.mark.asyncio
    async def test_demo_mode_response(self):
        client = LLMClient()  # No API key
        messages = [{"role": "user", "content": "Test"}]
        response = await client.generate(messages)
        assert "Demo Mode" in response

    @pytest.mark.asyncio
    async def test_demo_mode_with_string(self):
        client = LLMClient()
        response = await client.generate("Test prompt string")
        assert "Demo Mode" in response

    @pytest.mark.asyncio
    async def test_demo_mode_empty_messages(self):
        client = LLMClient()
        response = await client.generate([])
        assert isinstance(response, str)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_message(self, orchestrator):
        result = await orchestrator.process_message("")
        assert "reply" in result

    @pytest.mark.asyncio
    async def test_very_long_message(self, orchestrator):
        long_msg = "marketing strategy " * 500
        result = await orchestrator.process_message(long_msg)
        assert "reply" in result

    @pytest.mark.asyncio
    async def test_special_characters(self, orchestrator):
        result = await orchestrator.process_message("!@#$%^&*() 🎉")
        assert "reply" in result

    @pytest.mark.asyncio
    async def test_multiple_conversations(self, orchestrator):
        r1 = await orchestrator.process_message("Conv 1 message")
        r2 = await orchestrator.process_message("Conv 2 message")
        assert r1["conversation_id"] != r2["conversation_id"]

    @pytest.mark.asyncio
    async def test_user_context_passed(self, orchestrator):
        result = await orchestrator.process_message(
            "Hello",
            user_context={"user_id": "test-user", "project": "test-project"},
        )
        assert "reply" in result
