# =============================================================================
# 이 파일의 책임: EasyOCR 추론을 별도 프로세스(app.workers.easyocr_worker)로
#   실행해서, 매 호출이 끝나면 그 프로세스가 종료되며 OS가 메모리를 완전히
#   회수하게 한다. easyocr/torch를 이 모듈 안에서 import하지 않는다 — 그래야
#   메인 API 프로세스에는 이 무거운 패키지들이 전혀 로드되지 않는다.
# 다른 파일과의 관계: OcrCompareService가 기대하는 것과 동일한
#   `extract(image) -> list[LayoutElement]` 인터페이스를 그대로 구현해서,
#   기존 EasyOcrExtractor(같은 프로세스 안에서 로드하는 버전)와 자리를
#   그대로 교체할 수 있다.
# =============================================================================

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessError
from app.extractors.layout import LayoutElement

_WORKER_MODULE = "app.workers.easyocr_worker"
_TIMEOUT_SECONDS = 120


class EasyOcrSubprocessExtractor:
    def extract(self, image: Image.Image) -> list[LayoutElement]:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.png"
            output_path = Path(tmpdir) / "output.json"
            image.convert("RGB").save(input_path)

            try:
                result = subprocess.run(
                    [sys.executable, "-m", _WORKER_MODULE, str(input_path), str(output_path)],
                    capture_output=True,
                    text=True,
                    timeout=_TIMEOUT_SECONDS,
                )
            except subprocess.TimeoutExpired as exc:
                raise BusinessError(
                    ErrorCode.EXTRACTION_FAILED,
                    detail=f"EasyOCR 처리 시간이 {_TIMEOUT_SECONDS}초를 초과했습니다.",
                ) from exc

            if result.returncode != 0:
                raise BusinessError(
                    ErrorCode.EXTRACTION_FAILED,
                    detail=f"EasyOCR 처리 중 오류가 발생했습니다: {result.stderr[-500:]}",
                )

            raw_elements = json.loads(output_path.read_text(encoding="utf-8"))

        return [
            LayoutElement(
                x=item["x"],
                y=item["y"],
                content=item["content"],
                source="ocr",
                confidence=item["confidence"],
            )
            for item in raw_elements
        ]
