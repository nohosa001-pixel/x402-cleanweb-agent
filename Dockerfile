FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY . .

# 표준 입출력 버퍼링 방지
ENV PYTHONUNBUFFERED=1

# MCP stdio 서버 실행 (Smithery / Docker MCP 실행용)
CMD ["python", "-u", "mcp_server.py"]
