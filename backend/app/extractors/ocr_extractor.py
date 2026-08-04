from threading import Lock

import numpy as np
from paddleocr import PaddleOCR
from PIL import Image

from app.extractors.layout import LayoutElement


class OcrExtractor:
    # 두 OCR 박스가 같은 줄인지 판단할 때 필요한 최소 세로 겹침 비율.
    _LINE_OVERLAP_RATIO = 0.45
    # 한 글자씩 분리된 박스 사이의 간격이 글자 높이의 이 비율 이하면 붙인다.
    _CHAR_JOIN_GAP_RATIO = 0.60

    def __init__(self) -> None:
        self._ocr = PaddleOCR(
            lang="korean",
            use_doc_orientation_classify=True,
            use_doc_unwarping=True,
            use_textline_orientation=True,
        )

        # 여러 요청이 같은 OCR 모델을 동시에 사용하지 못하도록 제어한다.
        self._inference_lock = Lock()

    def extract(
        self,
        image: Image.Image,
        offset_x: float = 0,
        offset_y: float = 0,
    ) -> list[LayoutElement]:
        rgb_image = image.convert("RGB")

        # 동시에 여러 요청이 들어와도 OCR은 한 번에 하나씩 실행한다.
        with self._inference_lock:
            results = self._ocr.ocr(np.asarray(rgb_image))

        if not results:
            return []

        page = results[0]

        if page is None:
            return []

        texts = page.get("rec_texts", [])
        scores = page.get("rec_scores", [])

        boxes = page.get("rec_boxes")

        # rec_boxes가 없으면 다각형 좌표인 rec_polys를 사용한다.
        if boxes is None or len(boxes) == 0:
            boxes = page.get("rec_polys", [])

        elements: list[LayoutElement] = []

        for text, score, box in zip(texts, scores, boxes):
            normalized_text = str(text).strip()

            if not normalized_text:
                continue

            box_array = np.asarray(box)

            if box_array.ndim == 1:
                # rec_boxes 형식: [x1, y1, x2, y2]
                x = float(box_array[0])
                y = float(box_array[1])
                x2 = float(box_array[2])
                y2 = float(box_array[3])
            else:
                # rec_polys 형식: [[x1, y1], [x2, y2], ...]
                x = float(box_array[:, 0].min())
                y = float(box_array[:, 1].min())
                x2 = float(box_array[:, 0].max())
                y2 = float(box_array[:, 1].max())

            elements.append(
                LayoutElement(
                    x=x + offset_x,
                    y=y + offset_y,
                    content=normalized_text,
                    source="ocr",
                    confidence=float(score),
                    x2=x2 + offset_x,
                    y2=y2 + offset_y,
                )
            )

        return self._merge_same_line_elements(elements)

    @classmethod
    def _merge_same_line_elements(
        cls,
        elements: list[LayoutElement],
    ) -> list[LayoutElement]:
        """세로 위치가 겹치는 OCR 박스를 한 줄로 병합한다."""
        if len(elements) < 2:
            return elements

        lines: list[list[LayoutElement]] = []

        for element in sorted(elements, key=cls._vertical_sort_key):
            matching_line = next(
                (line for line in lines if cls._belongs_to_line(element, line)),
                None,
            )

            if matching_line is None:
                lines.append([element])
            else:
                matching_line.append(element)

        merged = [cls._merge_line(line) for line in lines]
        merged.sort(key=lambda element: (element.y, element.x))
        return merged

    @staticmethod
    def _vertical_sort_key(element: LayoutElement) -> tuple[float, float]:
        y2 = element.y2 if element.y2 is not None else element.y
        return ((element.y + y2) / 2, element.x)

    @classmethod
    def _belongs_to_line(
        cls,
        element: LayoutElement,
        line: list[LayoutElement],
    ) -> bool:
        element_y2 = element.y2 if element.y2 is not None else element.y
        line_y1 = min(item.y for item in line)
        line_y2 = max(item.y2 if item.y2 is not None else item.y for item in line)

        element_height = max(element_y2 - element.y, 1.0)
        line_height = max(line_y2 - line_y1, 1.0)
        overlap = max(0.0, min(element_y2, line_y2) - max(element.y, line_y1))
        overlap_ratio = overlap / min(element_height, line_height)

        return overlap_ratio >= cls._LINE_OVERLAP_RATIO

    @classmethod
    def _merge_line(cls, line: list[LayoutElement]) -> LayoutElement:
        ordered = sorted(line, key=lambda element: element.x)
        parts = [ordered[0].content]

        for previous, current in zip(ordered, ordered[1:]):
            parts.append(cls._separator_between(previous, current))
            parts.append(current.content)

        confidences = [
            element.confidence
            for element in ordered
            if element.confidence is not None
        ]

        return LayoutElement(
            x=min(element.x for element in ordered),
            y=min(element.y for element in ordered),
            x2=max(
                element.x2 if element.x2 is not None else element.x
                for element in ordered
            ),
            y2=max(
                element.y2 if element.y2 is not None else element.y
                for element in ordered
            ),
            content="".join(parts),
            source="ocr",
            confidence=(
                sum(confidences) / len(confidences)
                if confidences
                else None
            ),
        )

    @classmethod
    def _separator_between(
        cls,
        previous: LayoutElement,
        current: LayoutElement,
    ) -> str:
        previous_x2 = previous.x2 if previous.x2 is not None else previous.x
        gap = current.x - previous_x2

        previous_y2 = previous.y2 if previous.y2 is not None else previous.y
        current_y2 = current.y2 if current.y2 is not None else current.y
        average_height = (
            max(previous_y2 - previous.y, 1.0)
            + max(current_y2 - current.y, 1.0)
        ) / 2

        # PaddleOCR가 한글 한 단어를 한 글자 박스로 잘게 나눈 경우에는
        # 박스 사이가 가까울 때 공백 없이 원래 단어로 복원한다.
        if (
            len(previous.content) == 1
            and len(current.content) == 1
            and gap <= average_height * cls._CHAR_JOIN_GAP_RATIO
        ):
            return ""

        # 겹치거나 거의 붙은 박스는 하나의 문자열 조각으로 본다.
        if gap <= average_height * 0.15:
            return ""

        return " "
