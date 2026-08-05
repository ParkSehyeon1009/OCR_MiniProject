# =============================================================================
# 이 파일의 책임: EasyOCR(PyTorch) 추론을 메인 API 프로세스와 완전히 분리된
#   별도 OS 프로세스에서 실행한다. 이 스크립트가 끝나면(exit) OS가 프로세스의
#   메모리를 100% 강제 회수하므로, 같은 프로세스 안에서 로드/해제하는 방식에서
#   겪었던 "PyTorch 캐싱 allocator/glibc malloc이 해제된 메모리를 OS에
#   돌려주지 않는" 문제가 구조적으로 발생하지 않는다.
# 주의: 반드시 subprocess로만 실행할 것 (app.extractors.easyocr_subprocess_extractor
#   참고). 이 모듈을 메인 API 프로세스에서 import하면 그 순간 easyocr/torch가
#   메인 프로세스에 로드되어 격리 의미가 없어진다.
# 사용법: python -m app.workers.easyocr_worker <입력 이미지 경로> <출력 JSON 경로>
# =============================================================================

import json
import sys


def main() -> None:
    image_path, output_path = sys.argv[1], sys.argv[2]

    import easyocr
    import numpy as np
    from PIL import Image

    reader = easyocr.Reader(["ko", "en"], gpu=False)
    image = Image.open(image_path).convert("RGB")
    results = reader.readtext(np.asarray(image))

    elements = []
    for box, text, confidence in results:
        normalized_text = str(text).strip()
        if not normalized_text:
            continue

        xs = [point[0] for point in box]
        ys = [point[1] for point in box]

        elements.append(
            {
                "x": float(min(xs)),
                "y": float(min(ys)),
                "content": normalized_text,
                "confidence": float(confidence),
            }
        )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(elements, f)


if __name__ == "__main__":
    main()
