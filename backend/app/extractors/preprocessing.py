# =============================================================================
# 이 파일의 책임: OCR 정확도를 높이기 위한 이미지 전처리 단계들을 정의하고,
#   여러 단계를 순서대로 실행하는 파이프라인 함수 preprocess() 를 제공한다.
#   각 단계는 Image -> Image 순수 함수이며 상태를 갖지 않는다.
# 다른 파일과의 관계: ocr_extractor.py 가 OCR 실행 직전에 preprocess() 를 호출한다.
#   전처리 강도는 엔진마다 다르게 적용해야 하므로 프리셋으로 분리한다 —
#   PaddleOCR(딥러닝)은 과한 이진화가 손해일 수 있고, Tesseract(전통 알고리즘)는
#   이진화·노이즈 제거의 이득이 크다.
# Spring 비교: 여러 전처리기를 순서대로 통과시키는 FilterChain 과 같은 구조.
#   각 단계가 독립 함수라서 순서 변경·추가·제거가 자유롭다.
# =============================================================================

from typing import Callable

import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass, field


# OCR은 해상도에 민감하다. 이 폭보다 작으면 확대한다.
MIN_WIDTH = 1000
# 확대 배율 상한. 작은 로고·도장 이미지가 과도하게 커져 OCR 시간이
# 폭증하는 것을 막는다. 면적은 배율의 제곱으로 늘어난다(2배 확대 = 4배 면적).
MAX_UPSCALE = 2.0

# 이 각도보다 작은 기울기는 보정하지 않는다 (불필요한 재보간 방지).
MIN_DESKEW_ANGLE = 0.5

PreprocessStep = Callable[[Image.Image], Image.Image]

@dataclass(frozen=True)
class PreprocessResult:
    """전처리 결과와 좌표 역변환에 필요한 정보.

    OCR은 전처리된 이미지 기준으로 좌표를 돌려주므로, 호출자가 원본
    좌표계로 되돌릴 수 있도록 배율을 함께 전달한다. 회전이 포함되면
    단순 배율로는 되돌릴 수 없어 rotated 로 표시한다.
    """

    image: Image.Image
    applied: list[str] = field(default_factory=list)
    scale: float = 1.0
    rotated: bool = False


# ----------------------------------------------------------------- 단계 함수

def to_grayscale(image: Image.Image) -> Image.Image:
    """색 정보를 제거한다. 글자 인식에 색상은 쓰이지 않는다."""
    return image if image.mode == "L" else image.convert("L")

def upscale(image: Image.Image) -> Image.Image:
    """폭이 MIN_WIDTH 미만이면 비율을 유지해 확대한다."""
    if image.width >= MIN_WIDTH:
        return image

    scale = min(MIN_WIDTH / image.width, MAX_UPSCALE)
    if scale <= 1.0:
        return image

    size = (MIN_WIDTH, max(1, round(image.height * scale)))
    return image.resize(size, Image.LANCZOS)

def denoise(image: Image.Image) -> Image.Image:
    """점 형태의 노이즈를 제거한다. 스캔·촬영본에서 효과가 크다."""
    array = np.asarray(to_grayscale(image))
    return Image.fromarray(cv2.medianBlur(array, 3))

def binarize(image: Image.Image) -> Image.Image:
    """Otsu 임계값으로 글자와 배경을 흑백으로 분리한다."""
    array = np.asarray(to_grayscale(image))
    _, binary = cv2.threshold(
        array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return Image.fromarray(binary)

def deskew(image: Image.Image) -> Image.Image:
    """글자 영역의 최소 외접 사각형으로 기울기를 추정해 회전 보정한다."""
    array = np.asarray(to_grayscale(image))

    # 글자를 흰색(255)으로 만들어야 findNonZero 가 글자 좌표를 찾는다.
    _, binary = cv2.threshold(
        array, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    coordinates = cv2.findNonZero(binary)

    if coordinates is None:
        return image

    angle = cv2.minAreaRect(coordinates)[-1]

    # minAreaRect 각도는 0~90 범위로 나온다. -45~45 로 정규화한다.
    if angle > 45:
        angle -= 90

    if abs(angle) < MIN_DESKEW_ANGLE:
        return image

    # 빈 영역은 흰색으로 채워 글자로 오인되지 않게 한다.
    return image.rotate(
        angle, resample=Image.BICUBIC, expand=True, fillcolor=255
    )
    
def adjust_contrast(image: Image.Image) -> Image.Image:
    """국소 영역별로 대비를 높인다 (CLAHE).

    사진 촬영본은 조명이 고르지 않아 한쪽이 어둡다. 이미지 전체에 같은
    보정을 하면 밝은 쪽이 날아가므로, 작은 격자로 나눠 각각 보정한다.
    clipLimit 은 대비 증폭 한계로, 너무 크면 노이즈까지 증폭된다.
    """
    array = np.asarray(to_grayscale(image))
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return Image.fromarray(clahe.apply(array))


# --- 좌표를 바꾸지 않거나 배율로 되돌릴 수 있는 단계들 --------------------
# 전처리 없음 — 비교 측정의 기준선
PRESET_NONE: list[PreprocessStep] = []

# 문서 추출 기본 — PaddleOCR은 방향·왜곡을 내부에서 처리하므로 해상도만 보정
PRESET_LIGHT: list[PreprocessStep] = [to_grayscale, upscale]

# 스캔·촬영본 — 조명 보정과 노이즈 제거까지. 좌표는 배율로 되돌릴 수 있다
PRESET_SCAN: list[PreprocessStep] = [
    to_grayscale,
    upscale,
    adjust_contrast,
    denoise,
    binarize,
]


# --- 회전을 포함해 좌표 역변환이 불가한 단계 조합 ------------------------
# 엔진 비교 전용. 좌표를 쓰지 않는 경로에서만 사용한다
PRESET_FULL: list[PreprocessStep] = PRESET_SCAN + [deskew]

PRESETS: dict[str, list[PreprocessStep]] = {
    "none": PRESET_NONE,
    "light": PRESET_LIGHT,
    "scan": PRESET_SCAN,
    "full": PRESET_FULL,
}

# 좌표를 변형해 역변환이 불가한 단계 이름
GEOMETRY_STEPS = {"deskew"}


# ------------------------------------------------------------- 파이프라인

def preprocess(
    image: Image.Image,
    steps: list[PreprocessStep] | None = None,
) -> PreprocessResult:
    """전처리 단계를 순서대로 적용하고, 좌표 역변환 정보를 함께 반환한다.

    scale 은 원본 폭 대비 결과 폭의 비율이다. OCR이 돌려준 좌표를
    scale 로 나누면 원본 이미지 좌표계로 되돌아간다.
    회전이 포함되면 배율만으로는 되돌릴 수 없으므로 rotated=True 로 알린다.
    """
    original_width = max(image.width, 1)
    applied: list[str] = []
    result = image

    for step in steps if steps is not None else PRESET_LIGHT:
        result = step(result)
        applied.append(step.__name__)

    # OCR 엔진은 3채널 이미지를 기대한다.
    if result.mode != "RGB":
        result = result.convert("RGB")

    rotated = any(name in GEOMETRY_STEPS for name in applied)

    return PreprocessResult(
        image=result,
        applied=applied,
        # 회전 시에는 캔버스가 커져 폭 비율이 배율과 다르므로 1.0 으로 둔다.
        scale=1.0 if rotated else result.width / original_width,
        rotated=rotated,
    )


def preprocess_by_name(
    image: Image.Image,
    preset: str = "light",
) -> PreprocessResult:
    """문자열로 프리셋을 선택한다. 알 수 없는 이름은 light 로 처리한다."""
    return preprocess(image, PRESETS.get(preset, PRESET_LIGHT))

def preprocess_for_layout(
    image: Image.Image,
    steps: list[PreprocessStep] | None = None,
) -> PreprocessResult:
    """좌표를 사용하는 경로(문서 추출)용 전처리.

    기하 변형(회전) 단계가 포함되면 OCR 좌표를 원본 좌표계로 되돌릴 수
    없으므로 즉시 예외를 던진다. 잘못된 프리셋이 조용히 좌표를 어긋나게
    만드는 것을 막기 위한 안전장치다.
    """
    result = preprocess(image, steps)

    if result.rotated:
        raise ValueError(
            "좌표를 사용하는 경로에서는 기하 변형 전처리를 사용할 수 없습니다. "
            f"적용된 단계: {result.applied}"
        )

    return result

