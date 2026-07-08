FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MEK_MCP_HOST=0.0.0.0 \
    MEK_MCP_PORT=8000 \
    MEK_MCP_TRANSPORT=streamable-http

WORKDIR /app

COPY pyproject.toml setup.py README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir .

EXPOSE 8000

CMD ["mek-mcp-http"]
