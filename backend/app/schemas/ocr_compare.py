from pydantic import BaseModel, ConfigDict


class OcrEngineResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    engine: str
    text: str
    char_count: int
    avg_confidence: float | None = None
    elapsed_ms: int
    ground_truth_accuracy: float | None = None


class OcrCompareResponse(BaseModel):
    paddle: OcrEngineResult
    tesseract: OcrEngineResult
    easyocr: OcrEngineResult
