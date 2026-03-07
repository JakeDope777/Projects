"""
Chat API endpoints - interface to the Brain orchestrator.

POST /chat       - Send a message and get an AI response
GET  /chat/{id}  - Retrieve conversation history
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..db.schemas import ChatRequest, ChatResponse
from ..brain.orchestrator import BrainOrchestrator, LLMClient
from ..brain.memory_manager import MemoryManager
from ..core.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])

# Initialize brain components
_llm_client = LLMClient(api_key=settings.OPENAI_API_KEY, model=settings.OPENAI_MODEL)
_memory_manager = MemoryManager()
_brain = BrainOrchestrator(llm_client=_llm_client, memory_manager=_memory_manager)


def get_brain() -> BrainOrchestrator:
    """Dependency to get the brain orchestrator instance."""
    return _brain


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    brain: BrainOrchestrator = Depends(get_brain),
):
    """
    Send a message to the Digital CMO AI and receive a response.

    The brain will classify the intent, retrieve relevant context,
    and route to the appropriate skill module.
    """
    try:
        result = await brain.process_message(
            message=request.message,
            conversation_id=request.conversation_id,
            user_context=request.context,
        )
        return ChatResponse(
            reply=result["reply"],
            conversation_id=result["conversation_id"],
            module_used=result.get("module_used"),
            tokens_used=result.get("tokens_used", 0),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    brain: BrainOrchestrator = Depends(get_brain),
):
    """Retrieve the conversation history for a given conversation ID."""
    history = brain.get_conversation(conversation_id)
    if not history:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"conversation_id": conversation_id, "messages": history}


@router.delete("/{conversation_id}")
async def clear_conversation(
    conversation_id: str,
    brain: BrainOrchestrator = Depends(get_brain),
):
    """Clear a conversation from memory."""
    if brain.clear_conversation(conversation_id):
        return {"status": "cleared", "conversation_id": conversation_id}
    raise HTTPException(status_code=404, detail="Conversation not found")
