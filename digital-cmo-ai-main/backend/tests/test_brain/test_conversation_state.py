"""
Comprehensive tests for the Conversation State Manager.

Tests cover:
- ConversationState data class
- ActiveTask and SlotDefinition
- ConversationStateManager (CRUD, persistence, listing)
- Phase transitions
- Task slot-filling workflows
"""

import os
import json
import tempfile

import pytest
from app.brain.conversation_state import (
    ConversationState,
    ConversationPhase,
    ConversationStateManager,
    ActiveTask,
    SlotDefinition,
    TaskStatus,
    TASK_SLOT_TEMPLATES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def state():
    return ConversationState(conversation_id="test-conv-1", user_id="user-1")


@pytest.fixture
def manager(tmp_path):
    return ConversationStateManager(persist_dir=str(tmp_path / "conversations"))


@pytest.fixture
def memory_manager(tmp_path):
    return ConversationStateManager()


# ---------------------------------------------------------------------------
# SlotDefinition tests
# ---------------------------------------------------------------------------

class TestSlotDefinition:
    """Tests for the SlotDefinition data class."""

    def test_create_slot(self):
        slot = SlotDefinition(name="budget", description="Campaign budget")
        assert slot.name == "budget"
        assert slot.required is True
        assert slot.filled is False
        assert slot.value is None

    def test_fill_slot(self):
        slot = SlotDefinition(name="budget", description="Campaign budget")
        slot.fill("$50,000")
        assert slot.filled is True
        assert slot.value == "$50,000"

    def test_optional_slot(self):
        slot = SlotDefinition(name="notes", description="Additional notes", required=False)
        assert slot.required is False


# ---------------------------------------------------------------------------
# ActiveTask tests
# ---------------------------------------------------------------------------

class TestActiveTask:
    """Tests for the ActiveTask data class."""

    def test_create_task(self):
        task = ActiveTask(description="Create campaign", module="crm_campaign")
        assert task.status == TaskStatus.PENDING
        assert task.description == "Create campaign"
        assert task.module == "crm_campaign"

    def test_missing_slots(self):
        task = ActiveTask(
            description="Test",
            slots=[
                SlotDefinition(name="a", description="A", required=True),
                SlotDefinition(name="b", description="B", required=True),
                SlotDefinition(name="c", description="C", required=False),
            ],
        )
        assert len(task.missing_slots) == 2

    def test_fill_slot(self):
        task = ActiveTask(
            description="Test",
            slots=[
                SlotDefinition(name="name", description="Name", required=True),
            ],
        )
        assert task.fill_slot("name", "My Campaign") is True
        assert task.is_complete is True

    def test_fill_nonexistent_slot(self):
        task = ActiveTask(description="Test")
        assert task.fill_slot("nonexistent", "value") is False

    def test_is_complete_no_slots(self):
        task = ActiveTask(description="Test")
        assert task.is_complete is True

    def test_to_dict(self):
        task = ActiveTask(
            description="Test task",
            module="analytics_reporting",
            slots=[SlotDefinition(name="metric", description="KPI")],
        )
        d = task.to_dict()
        assert d["description"] == "Test task"
        assert d["module"] == "analytics_reporting"
        assert len(d["slots"]) == 1

    def test_from_dict(self):
        data = {
            "task_id": "task-1",
            "description": "Test",
            "module": "general",
            "status": "in_progress",
            "slots": [
                {"name": "a", "description": "A", "required": True, "value": None, "filled": False}
            ],
        }
        task = ActiveTask.from_dict(data)
        assert task.task_id == "task-1"
        assert task.status == TaskStatus.IN_PROGRESS
        assert len(task.slots) == 1


# ---------------------------------------------------------------------------
# ConversationState tests
# ---------------------------------------------------------------------------

class TestConversationState:
    """Tests for the ConversationState data class."""

    def test_create_state(self, state):
        assert state.conversation_id == "test-conv-1"
        assert state.user_id == "user-1"
        assert state.phase == ConversationPhase.GREETING
        assert state.turn_count == 0

    def test_add_message(self, state):
        state.add_message("user", "Hello")
        assert len(state.messages) == 1
        assert state.messages[0]["role"] == "user"
        assert state.messages[0]["content"] == "Hello"
        assert state.turn_count == 1

    def test_add_assistant_message_no_turn_increment(self, state):
        state.add_message("assistant", "Hi there!")
        assert state.turn_count == 0  # Only user messages increment turns

    def test_get_recent_messages(self, state):
        for i in range(30):
            state.add_message("user", f"Message {i}")
        recent = state.get_recent_messages(10)
        assert len(recent) == 10
        assert recent[-1]["content"] == "Message 29"

    def test_set_and_get_variable(self, state):
        state.set_variable("project", "Alpha")
        assert state.get_variable("project") == "Alpha"

    def test_get_variable_default(self, state):
        assert state.get_variable("nonexistent", "default") == "default"

    def test_start_task(self, state):
        task = state.start_task(
            "Create email campaign",
            "crm_campaign",
            slots=[
                {"name": "audience", "description": "Target audience"},
                {"name": "subject", "description": "Email subject"},
            ],
        )
        assert task.description == "Create email campaign"
        assert len(task.slots) == 2
        assert state.phase == ConversationPhase.TASK_EXECUTION

    def test_get_current_task(self, state):
        assert state.get_current_task() is None
        state.start_task("Test task", "general")
        assert state.get_current_task() is not None

    def test_complete_current_task(self, state):
        state.start_task("Test task", "general")
        task = state.complete_current_task(result="Done!")
        assert task is not None
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "Done!"
        assert state.phase == ConversationPhase.FOLLOW_UP

    def test_complete_no_task(self, state):
        result = state.complete_current_task()
        assert result is None

    def test_to_dict(self, state):
        state.add_message("user", "Hello")
        state.set_variable("key", "value")
        d = state.to_dict()
        assert d["conversation_id"] == "test-conv-1"
        assert len(d["messages"]) == 1
        assert d["context_variables"]["key"] == "value"

    def test_from_dict(self):
        data = {
            "conversation_id": "conv-2",
            "user_id": "user-2",
            "phase": "task_execution",
            "topic": "Marketing",
            "current_module": "creative_design",
            "messages": [{"role": "user", "content": "Hi", "timestamp": "2025-01-01"}],
            "summary": "Previous summary",
            "active_tasks": [],
            "context_variables": {"x": 1},
            "turn_count": 5,
        }
        state = ConversationState.from_dict(data)
        assert state.conversation_id == "conv-2"
        assert state.phase == ConversationPhase.TASK_EXECUTION
        assert state.turn_count == 5
        assert state.summary == "Previous summary"

    def test_multiple_tasks(self, state):
        state.start_task("Task 1", "general")
        state.complete_current_task("Done 1")
        state.start_task("Task 2", "analytics_reporting")
        current = state.get_current_task()
        assert current is not None
        assert current.description == "Task 2"


# ---------------------------------------------------------------------------
# ConversationStateManager tests
# ---------------------------------------------------------------------------

class TestConversationStateManager:
    """Tests for the state manager."""

    def test_get_or_create_new(self, manager):
        state = manager.get_or_create("conv-new", user_id="user-1")
        assert state.conversation_id == "conv-new"
        assert state.user_id == "user-1"

    def test_get_or_create_existing(self, manager):
        state1 = manager.get_or_create("conv-1")
        state1.add_message("user", "Hello")
        state2 = manager.get_or_create("conv-1")
        assert len(state2.messages) == 1  # Same state

    def test_get_nonexistent(self, manager):
        assert manager.get("nonexistent") is None

    def test_save_and_get(self, manager):
        state = manager.get_or_create("conv-save")
        state.add_message("user", "Test")
        manager.save(state)
        retrieved = manager.get("conv-save")
        assert retrieved is not None
        assert len(retrieved.messages) == 1

    def test_delete(self, manager):
        manager.get_or_create("conv-del")
        assert manager.delete("conv-del") is True
        assert manager.get("conv-del") is None

    def test_delete_nonexistent(self, manager):
        assert manager.delete("nonexistent") is False

    def test_list_conversations(self, manager):
        manager.get_or_create("conv-a", user_id="user-1")
        manager.get_or_create("conv-b", user_id="user-2")
        manager.get_or_create("conv-c", user_id="user-1")

        all_convs = manager.list_conversations()
        assert len(all_convs) == 3

        user1_convs = manager.list_conversations(user_id="user-1")
        assert len(user1_convs) == 2

    def test_persistence(self, tmp_path):
        persist_dir = str(tmp_path / "persist_test")

        # Create and save
        mgr1 = ConversationStateManager(persist_dir=persist_dir)
        state = mgr1.get_or_create("conv-persist", user_id="user-1")
        state.add_message("user", "Persistent message")
        mgr1.save(state)

        # Load from disk
        mgr2 = ConversationStateManager(persist_dir=persist_dir)
        loaded = mgr2.get("conv-persist")
        assert loaded is not None
        assert len(loaded.messages) == 1
        assert loaded.messages[0]["content"] == "Persistent message"

    def test_get_active_conversations(self, manager):
        state1 = manager.get_or_create("conv-active")
        state1.start_task("Active task", "general")

        state2 = manager.get_or_create("conv-inactive")
        # No task started

        active = manager.get_active_conversations()
        assert len(active) == 1
        assert active[0].conversation_id == "conv-active"

    def test_in_memory_manager(self):
        """Test manager without persistence directory."""
        manager = ConversationStateManager()
        state = manager.get_or_create("conv-mem")
        state.add_message("user", "Hello")
        manager.save(state)
        assert manager.get("conv-mem") is not None


# ---------------------------------------------------------------------------
# Phase transition tests
# ---------------------------------------------------------------------------

class TestPhaseTransitions:
    """Tests for automatic phase transitions."""

    def test_greeting_phase(self, manager):
        state = manager.get_or_create("conv-phase")
        phase = manager.update_phase(state)
        assert phase == ConversationPhase.GREETING

    def test_task_execution_phase(self, manager):
        state = manager.get_or_create("conv-phase")
        state.add_message("user", "Create a campaign")
        state.start_task("Create campaign", "crm_campaign")
        phase = manager.update_phase(state)
        assert phase == ConversationPhase.TASK_EXECUTION

    def test_information_gathering_phase(self, manager):
        state = manager.get_or_create("conv-phase")
        state.add_message("user", "Create a campaign")
        task = state.start_task(
            "Create campaign",
            "crm_campaign",
            slots=[{"name": "audience", "description": "Target audience"}],
        )
        phase = manager.update_phase(state)
        assert phase == ConversationPhase.INFORMATION_GATHERING

    def test_follow_up_phase(self, manager):
        state = manager.get_or_create("conv-phase")
        state.add_message("user", "Create a campaign")
        state.start_task("Create campaign", "crm_campaign")
        state.complete_current_task("Campaign created!")
        phase = manager.update_phase(state)
        assert phase == ConversationPhase.FOLLOW_UP


# ---------------------------------------------------------------------------
# Task slot templates tests
# ---------------------------------------------------------------------------

class TestTaskSlotTemplates:
    """Tests for predefined task slot templates."""

    def test_campaign_creation_template(self):
        template = TASK_SLOT_TEMPLATES["campaign_creation"]
        assert len(template) > 0
        names = [s["name"] for s in template]
        assert "campaign_name" in names
        assert "target_audience" in names

    def test_content_creation_template(self):
        template = TASK_SLOT_TEMPLATES["content_creation"]
        assert len(template) > 0
        names = [s["name"] for s in template]
        assert "content_type" in names
        assert "topic" in names

    def test_competitor_analysis_template(self):
        template = TASK_SLOT_TEMPLATES["competitor_analysis"]
        assert len(template) > 0

    def test_analytics_report_template(self):
        template = TASK_SLOT_TEMPLATES["analytics_report"]
        assert len(template) > 0
