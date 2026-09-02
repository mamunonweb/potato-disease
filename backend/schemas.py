"""Pydantic schemas for API request/response payloads."""
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class TopPrediction(BaseModel):
    className: str
    displayName: str
    probability: float


class GradcamSeverity(BaseModel):
    ratio: float
    level: str


class GradcamInfo(BaseModel):
    image_data_uri: str
    layer_name: str
    severity: GradcamSeverity


class GuidanceInfo(BaseModel):
    source: Literal["openrouter", "builtin"]
    description: str
    symptoms: list[str]
    causes: list[str]
    actions: list[str]
    prevention: list[str]


class PredictionResponse(BaseModel):
    predicted_class: str
    display_name: str
    confidence: float
    probabilities: dict[str, float]
    top_predictions: list[TopPrediction]
    gradcam: GradcamInfo | None = None
    gradcam_note: str | None = None
    guidance: GuidanceInfo
    disclaimer: str


class BatchItemSuccess(BaseModel):
    status: Literal["ok"]
    filename: str
    predicted_class: str
    display_name: str
    confidence: float
    top_predictions: list[TopPrediction]


class BatchItemError(BaseModel):
    status: Literal["error"]
    filename: str
    error: str


BatchItem = Annotated[
    BatchItemSuccess | BatchItemError,
    Field(discriminator="status"),
]


class BatchResponse(BaseModel):
    results: list[BatchItem]
    healthy_count: int
    disease_count: int
    failed_count: int
    disclaimer: str


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    predicted_class: str
    confidence: float = Field(ge=0.0, le=1.0)
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)


class ChatChoiceDelta(BaseModel):
    content: str | None = None


class ChatStreamEvent(BaseModel):
    type: Literal["delta", "done", "error"]
    text: str = ""


class ChatResponse(BaseModel):
    reply: str
    guidance_source: Literal["openrouter", "builtin"]
    disclaimer: str
