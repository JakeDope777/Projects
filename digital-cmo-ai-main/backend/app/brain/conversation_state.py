"""
Conversation State Manager - tracks multi-turn conversation state.

Manages:
- **Turn tracking** – message history per conversation with timestamps.
- **Active task state** – what the user is currently working on (e.g.
  "building a campaign", "analysing competitors").
- **Slot filling** – tracks required information that has been collected
  vs. still needed for the current task.
- **Conversation metadata** – topic, module, turn count, timestamps.
- **Persistence** – serialises state to JSON for storage / recovery.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ConversationPhase(str, Enum):
    """High-level phase of a conversation."""
    GREETING = "greeting"
    INFORMATION_GATHERING = "information_gathering"
    TASK_EXECUTION = "task_execution"
    FOLLOW_UP = "follow_up"
    CLOSING = "closing"


class TaskStatus(str, Enum):
    """Status of an active task within a conversation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SlotDefinition:
    """A piece of information required to complete a task."""
    name: str
    description: str
    required: bool = True
    value: Optional[str] = None
    filled: bool = False

    def fill(self, value: str) -> None:
        self.value = value
        self.filled = True


@dataclass
class ActiveTask:
    """Represents an in-progress task within a conversation."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    module: str = "general"
    status: TaskStatus = TaskStatus.PENDING
    slots: list[SlotDefinition] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result: Optional[str] = None

    @property
    def missing_slots(self) -> list[SlotDefinition]:
        """Return slots that are required but not yet filled."""
        return [s for s in self.slots if s.required and not s.filled]

    @property
    def is_complete(self) -> bool:
        return len(self.missing_slots) == 0

    def fill_slot(self, name: str, value: str) -> bool:
        """Fill a slot by name. Returns True if the slot was found."""
        for slot in self.slots:
            if slot.name == name:
                slot.fill(value)
                self.updated_at = datetime.now(timezone.utc).isoformat()
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "module": self.module,
            "status": self.status.value,
            "slots": [
                {"name": s.name, "description": s.description,
                 "required": s.required, "value": s.value, "filled": s.filled}
                for s in self.slots
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ActiveTask":
        slots = [
            SlotDefinition(
                name=s["name"], description=s["description"],
                required=s.get("required", True),
                value=s.get("value"), filled=s.get("filled", False),
            )
            for s in data.get("slots", [])
        ]
        return cls(
            task_id=data.get("task_id", str(uuid.uuid4())),
            description=data.get("description", ""),
            module=data.get("module", "general"),
            status=TaskStatus(data.get("status", "pending")),
            slots=slots,
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
            result=data.get("result"),
        )


@dataclass
class ConversationState:
    """Full state of a single conversation."""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    phase: ConversationPhase = ConversationPhase.GREETING
    topic: Optional[str] = None
    current_module: str = "general"
    messages: list[dict] = field(default_factory=list)
    summary: Optional[str] = None
    active_tasks: list[ActiveTask] = field(default_factory=list)
    context_variables: dict[str, Any] = field(default_factory=dict)
    turn_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_message(self, role: str, content: str) -> None:
        """Add a message and update turn count."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        if role == "user":
            self.turn_count += 1
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_recent_messages(self, n: int = 20) -> list[dict]:
        """Return the last *n* messages."""
        return self.messages[-n:]

    def set_variable(self, key: str, value: Any) -> None:
        """Store a context variable."""
        self.context_variables[key] = value
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def get_variable(self, key: str, default: Any = None) -> Any:
        """Retrieve a context variable."""
        return self.context_variables.get(key, default)

    def start_task(self, description: str, module: str, slots: Optional[list[dict]] = None) -> ActiveTask:
        """Create and register a new active task."""
        slot_defs = []
        if slots:
            for s in slots:
                slot_defs.append(SlotDefinition(
                    name=s["name"],
                    description=s.get("description", ""),
                    required=s.get("required", True),
                ))
        task = ActiveTask(
            description=description,
            module=module,
            status=TaskStatus.IN_PROGRESS,
            slots=slot_defs,
        )
        self.active_tasks.append(task)
        self.phase = ConversationPhase.TASK_EXECUTION
        self.updated_at = datetime.now(timezone.utc).isoformat()
        return task

    def get_current_task(self) -> Optional[ActiveTask]:
        """Return the most recent non-completed task, or None."""
        for task in reversed(self.active_tasks):
            if task.status in (TaskStatus.IN_PROGRESS, TaskStatus.WAITING_FOR_INPUT, TaskStatus.PENDING):
                return task
        return None

    def complete_current_task(self, result: Optional[str] = None) -> Optional[ActiveTask]:
        """Mark the current task as completed."""
        task = self.get_current_task()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.updated_at = datetime.now(timezone.utc).isoformat()
            self.phase = ConversationPhase.FOLLOW_UP
            self.updated_at = datetime.now(timezone.utc).isoformat()
        return task

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "phase": self.phase.value,
            "topic": self.topic,
            "current_module": self.current_module,
            "messages": self.messages,
            "summary": self.summary,
            "active_tasks": [t.to_dict() for t in self.active_tasks],
            "context_variables": self.context_variables,
            "turn_count": self.turn_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConversationState":
        state = cls(
            conversation_id=data.get("conversation_id", str(uuid.uuid4())),
            user_id=data.get("user_id"),
            phase=ConversationPhase(data.get("phase", "greeting")),
            topic=data.get("topic"),
            current_module=data.get("current_module", "general"),
            messages=data.get("messages", []),
            summary=data.get("summary"),
            context_variables=data.get("context_variables", {}),
            turn_count=data.get("turn_count", 0),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=data.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )
        state.active_tasks = [
            ActiveTask.from_dict(t) for t in data.get("active_tasks", [])
        ]
        return state


# ---------------------------------------------------------------------------
# Conversation State Manager
# ---------------------------------------------------------------------------

class ConversationStateManager:
    """
    Manages multiple conversation states with optional file-based persistence.

    Usage::

        manager = ConversationStateManager(persist_dir="./data/conversations")
        state = manager.get_or_create("conv-123", user_id="user-1")
        state.add_message("user", "Hello")
        manager.save(state)
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self._states: dict[str, ConversationState] = {}
        self.persist_dir = Path(persist_dir) if persist_dir else None
        if self.persist_dir:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self._load_all()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_or_create(
        self,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ConversationState:
        """Get an existing conversation state or create a new one."""
        if conversation_id and conversation_id in self._states:
            return self._states[conversation_id]

        state = ConversationState(
            conversation_id=conversation_id or str(uuid.uuid4()),
            user_id=user_id,
        )
        self._states[state.conversation_id] = state
        return state

    def get(self, conversation_id: str) -> Optional[ConversationState]:
        """Get a conversation state by ID, or None."""
        return self._states.get(conversation_id)

    def save(self, state: ConversationState) -> None:
        """Persist the conversation state."""
        self._states[state.conversation_id] = state
        if self.persist_dir:
            path = self.persist_dir / f"{state.conversation_id}.json"
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation state."""
        if conversation_id in self._states:
            del self._states[conversation_id]
            if self.persist_dir:
                path = self.persist_dir / f"{conversation_id}.json"
                if path.exists():
                    path.unlink()
            return True
        return False

    def list_conversations(self, user_id: Optional[str] = None) -> list[dict]:
        """List all conversations, optionally filtered by user_id."""
        results = []
        for state in self._states.values():
            if user_id and state.user_id != user_id:
                continue
            results.append({
                "conversation_id": state.conversation_id,
                "user_id": state.user_id,
                "topic": state.topic,
                "phase": state.phase.value,
                "turn_count": state.turn_count,
                "updated_at": state.updated_at,
            })
        results.sort(key=lambda x: x["updated_at"], reverse=True)
        return results

    def get_active_conversations(self, user_id: Optional[str] = None) -> list[ConversationState]:
        """Return conversations that have an active (non-completed) task."""
        active = []
        for state in self._states.values():
            if user_id and state.user_id != user_id:
                continue
            if state.get_current_task() is not None:
                active.append(state)
        return active

    # ------------------------------------------------------------------
    # Phase transition helpers
    # ------------------------------------------------------------------

    def update_phase(self, state: ConversationState) -> ConversationPhase:
        """
        Automatically determine and update the conversation phase based on
        the current state.
        """
        if state.turn_count == 0:
            state.phase = ConversationPhase.GREETING
        elif state.get_current_task() is not None:
            task = state.get_current_task()
            if task and task.missing_slots:
                state.phase = ConversationPhase.INFORMATION_GATHERING
                task.status = TaskStatus.WAITING_FOR_INPUT
            else:
                state.phase = ConversationPhase.TASK_EXECUTION
        elif state.turn_count > 0 and not state.active_tasks:
            state.phase = ConversationPhase.GREETING
        else:
            # Check if the last task was recently completed
            if state.active_tasks and state.active_tasks[-1].status == TaskStatus.COMPLETED:
                state.phase = ConversationPhase.FOLLOW_UP

        state.updated_at = datetime.now(timezone.utc).isoformat()
        return state.phase

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load_all(self) -> None:
        """Load all conversation states from the persist directory."""
        if not self.persist_dir:
            return
        for path in self.persist_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                state = ConversationState.from_dict(data)
                self._states[state.conversation_id] = state
            except (json.JSONDecodeError, KeyError):
                continue


# ---------------------------------------------------------------------------
# Task slot templates for common marketing tasks
# ---------------------------------------------------------------------------

TASK_SLOT_TEMPLATES: dict[str, list[dict]] = {
    "campaign_creation": [
        {"name": "campaign_name", "description": "Name of the campaign", "required": True},
        {"name": "target_audience", "description": "Who is the campaign targeting?", "required": True},
        {"name": "channel", "description": "Marketing channel (email, social, ads)", "required": True},
        {"name": "budget", "description": "Campaign budget", "required": False},
        {"name": "start_date", "description": "Campaign start date", "required": False},
        {"name": "goal", "description": "Primary campaign goal", "required": True},
    ],
    "content_creation": [
        {"name": "content_type", "description": "Type of content (blog, social, email)", "required": True},
        {"name": "topic", "description": "Content topic or subject", "required": True},
        {"name": "tone", "description": "Desired tone (formal, casual, playful)", "required": False},
        {"name": "length", "description": "Approximate length", "required": False},
        {"name": "target_audience", "description": "Who is the content for?", "required": False},
    ],
    "competitor_analysis": [
        {"name": "competitors", "description": "List of competitors to analyse", "required": True},
        {"name": "focus_areas", "description": "Areas to focus on (pricing, features, marketing)", "required": False},
        {"name": "market", "description": "Target market or industry", "required": True},
    ],
    "analytics_report": [
        {"name": "metrics", "description": "Metrics to include in the report", "required": True},
        {"name": "time_period", "description": "Time period for the report", "required": True},
        {"name": "comparison", "description": "Compare against (previous period, target)", "required": False},
    ],
}
