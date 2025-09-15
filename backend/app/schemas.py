from pydantic import BaseModel
from typing import List, Optional, Any

class LineItemOut(BaseModel):
    id: str
    description: str
    quantity: float
    unit_price: float
    total_price: float
    confidence: float

class POOut(BaseModel):
    id: str
    filename: str
    pdf_url: str
    created_at: str
    status: str
    progress: float
    avg_confidence: float
    buyer: dict
    ship_to: dict
    line_items: List[LineItemOut]
    ocr_text: Optional[str] = None
    llm_json: Optional[Any] = None

class StatsOut(BaseModel):
    total: int
    complete: int
    processing: int
    failed: int
    avg_confidence: float

class PromptPayload(BaseModel):
    global_prompt: Optional[str] = None
    customer_key: Optional[str] = None
    customer_prompt: Optional[str] = None

class PromptBundleOut(BaseModel):
    global_prompt: str
    customer_prompts: list
