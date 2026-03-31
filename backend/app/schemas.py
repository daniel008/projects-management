from pydantic import BaseModel, ConfigDict, Field


class CardPayload(BaseModel):
    id: str
    title: str
    details: str


class ColumnPayload(BaseModel):
    id: str
    title: str
    card_ids: list[str] = Field(alias="cardIds")


class BoardPayload(BaseModel):
    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]


class AIConnectivityResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    status: str
    provider: str
    model: str
    assistant_message: str | None = Field(
        default=None, alias="assistantMessage")
    error: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class AIChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = Field(default_factory=list)


class AIChatResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    status: str
    provider: str
    model: str
    assistant_message: str = Field(alias="assistantMessage")
    board_updated: bool = Field(alias="boardUpdated")
    board: dict
    error: str | None = None
