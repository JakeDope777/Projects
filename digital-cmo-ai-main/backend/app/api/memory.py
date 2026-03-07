"""
Memory API endpoints.

POST /memory/store    - Save content to structured memory folders
POST /memory/retrieve - Retrieve similar memories from vector store
GET  /memory/files    - List all memory files
GET  /memory/read     - Read a specific memory file
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from ..db.schemas import MemoryStoreRequest, MemoryRetrieveRequest, MemoryResponse
from ..brain.memory_manager import MemoryManager

router = APIRouter(prefix="/memory", tags=["Memory"])

_memory = MemoryManager()


def get_memory() -> MemoryManager:
    return _memory


@router.post("/store", response_model=MemoryResponse)
async def store_memory(
    request: MemoryStoreRequest,
    memory: MemoryManager = Depends(get_memory),
):
    """Save content to a structured memory file."""
    try:
        path = memory.save_to_folder(request.file_path, request.content)
        return MemoryResponse(status="success", data={"path": path})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retrieve", response_model=MemoryResponse)
async def retrieve_memories(
    request: MemoryRetrieveRequest,
    memory: MemoryManager = Depends(get_memory),
):
    """Retrieve similar memories from the vector store."""
    results = memory.retrieve_similar(request.query, k=request.k)
    return MemoryResponse(status="success", data={"results": results})


@router.get("/files", response_model=MemoryResponse)
async def list_memory_files(
    folder: str = Query("", description="Subfolder to list"),
    memory: MemoryManager = Depends(get_memory),
):
    """List all files in the memory folder structure."""
    files = memory.list_folder(folder)
    return MemoryResponse(status="success", data={"files": files})


@router.get("/read", response_model=MemoryResponse)
async def read_memory_file(
    file_path: str = Query(..., description="Relative path within memory/"),
    memory: MemoryManager = Depends(get_memory),
):
    """Read content from a specific memory file."""
    content = memory.read_from_folder(file_path)
    if content is None:
        raise HTTPException(status_code=404, detail="Memory file not found")
    return MemoryResponse(status="success", data={"content": content, "path": file_path})
