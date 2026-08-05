# =============================================================================
# 이 파일의 책임: OCR 비교 화면에서 "정답 데이터셋"을 이용한 실제 정확도를
#   계산한다. 정답은 LabelMe 라벨링 툴이 만드는 JSON 형식(shapes[].label +
#   points)을 그대로 사용한다. 각 shape의 좌표로 읽는 순서(위→아래, 왼쪽→
#   오른쪽)를 복원해 정답 텍스트 한 덩어리를 만들고, OCR 결과 텍스트와
#   편집거리(Levenshtein) 기반 CER(문자 오류율)로 비교해 정확도(%)를 낸다.
# 다른 파일과의 관계: ocr_compare_router.py 가 업로드된 정답 JSON을
#   parse_ground_truth_text() 로 정답 텍스트로 바꾸고, ocr_compare_service.py
#   의 compute_accuracy() 로 각 엔진 결과와 비교한다.
# =============================================================================

import json

from app.core.error_codes import ErrorCode
from app.core.exceptions import BusinessError


def parse_ground_truth_text(content: bytes) -> str:
    """LabelMe JSON에서 정답 텍스트를 읽는 순서대로 복원한다."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise BusinessError(
            ErrorCode.EXTRACTION_FAILED, detail="정답 데이터(JSON)를 읽을 수 없습니다."
        ) from exc

    shapes = data.get("shapes")
    if not isinstance(shapes, list) or not shapes:
        raise BusinessError(
            ErrorCode.EXTRACTION_FAILED,
            detail="정답 데이터에 shapes가 없습니다. LabelMe 형식 JSON이 맞는지 확인해 주세요.",
        )

    ordered: list[tuple[float, float, str]] = []

    for shape in shapes:
        label = str(shape.get("label", "")).strip()
        points = shape.get("points") or []

        if not label or not points:
            continue

        xs = [point[0] for point in points]
        ys = [point[1] for point in points]

        # 기존 코드의 좌표 정렬 관례(좌상단 x,y)와 맞춘다.
        ordered.append((min(ys), min(xs), label))

    if not ordered:
        raise BusinessError(
            ErrorCode.EXTRACTION_FAILED,
            detail="정답 데이터에서 라벨을 하나도 찾지 못했습니다.",
        )

    ordered.sort(key=lambda item: (item[0], item[1]))
    return "\n".join(label for _, _, label in ordered)


def compute_accuracy(reference: str, hypothesis: str) -> float:
    """정답 텍스트 대비 OCR 결과의 정확도(%)를 CER 기반으로 계산한다.

    accuracy = max(0, 1 - 편집거리(reference, hypothesis) / len(reference)) * 100
    줄바꿈/공백 표기 차이로 억울하게 깎이지 않도록 두 문자열 다 정규화한다.
    """
    normalized_reference = _normalize(reference)
    normalized_hypothesis = _normalize(hypothesis)

    if not normalized_reference:
        return 0.0

    distance = _levenshtein_distance(normalized_reference, normalized_hypothesis)
    cer = distance / len(normalized_reference)
    return max(0.0, 1.0 - cer) * 100


def _normalize(text: str) -> str:
    return " ".join(text.split())


def _levenshtein_distance(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    previous_row = list(range(len(b) + 1))

    for i, char_a in enumerate(a, start=1):
        current_row = [i]
        for j, char_b in enumerate(b, start=1):
            insert_cost = current_row[j - 1] + 1
            delete_cost = previous_row[j] + 1
            replace_cost = previous_row[j - 1] + (0 if char_a == char_b else 1)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row

    return previous_row[-1]
