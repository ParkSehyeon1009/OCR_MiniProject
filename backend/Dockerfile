FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Seoul

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        tesseract-ocr \
        tesseract-ocr-kor \
        tesseract-ocr-eng \
        libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    # easyocr이 torch/torchvision을 의존하는데, 기본 PyPI 휠은 GPU(CUDA) 런타임까지
    # 통째로 딸려온다. 이 프로젝트는 GPU를 쓰지 않으므로(OcrExtractor류 전부 CPU 실행)
    # PyTorch의 CPU 전용 인덱스에서 먼저 설치해, 아래 requirements.txt 설치 단계가
    # CUDA 패키지를 받아오지 않게 만든다.
    && pip install --no-cache-dir torch==2.13.0+cpu torchvision==0.28.0+cpu \
        --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
