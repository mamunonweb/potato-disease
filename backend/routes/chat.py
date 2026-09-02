"""Chat endpoints: non-streaming reply + SSE stream."""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from schemas import ChatRequest, ChatResponse
from services import chat
from services.guidance import DISEASE_INFO

router = APIRouter()

CHAT_DISCLAIMER = (
    "This is general guidance about the detected condition, not a "
    "definitive diagnosis or a substitute for local agricultural advice."
)


def _validate(request: ChatRequest) -> None:
    if request.predicted_class not in DISEASE_INFO:
        raise HTTPException(status_code=422, detail="Unknown disease class.")


@router.post("/api/chat")
def chat_once(request: ChatRequest) -> ChatResponse:
    _validate(request)
    try:
        reply, source = chat.chat_reply(
            request.predicted_class,
            request.confidence,
            request.message,
            [turn.model_dump() for turn in request.history],
        )
    except Exception:
        # Never leak stack traces; the chat is an enhancement.
        raise HTTPException(
            status_code=503,
            detail="The guidance provider is unavailable right now.",
        )
    return ChatResponse(
        reply=reply,
        guidance_source=source,
        disclaimer=CHAT_DISCLAIMER,
    )


@router.post("/api/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    _validate(request)

    def generate():
        try:
            for delta in chat.chat_reply_stream(
                request.predicted_class,
                request.confidence,
                request.message,
                [turn.model_dump() for turn in request.history],
            ):
                yield "data: " + json.dumps({"type": "delta", "text": delta}) + "\n\n"
            yield "data: " + json.dumps({"type": "done", "disclaimer": CHAT_DISCLAIMER}) + "\n\n"
        except Exception:
            yield (
                "data: "
                + json.dumps({"type": "error", "text": "The guidance provider is unavailable."})
                + "\n\n"
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
