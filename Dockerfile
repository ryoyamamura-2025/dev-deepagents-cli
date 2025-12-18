# ============================================
# Stage 1: フロントエンドのビルド
# ============================================
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

# package.jsonとpackage-lock.jsonをコピー
COPY frontend/package*.json ./
RUN npm ci --only=production --no-audit --no-fund

# ソースコードをコピーしてビルド
COPY frontend/ ./
RUN npm run build \
    && rm -rf node_modules \
    && rm -rf .next/cache

# ============================================
# Stage 2: Pythonバックエンド
# ============================================
FROM python:3.13-slim

# uv（高速パッケージマネージャ）を取り込み
COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

# 必要なパッケージを一括インストール＆クリーンアップ
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    npm \
    && npm install -g docx \
    && npm cache clean --force \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# 依存関係のみをインストール（キャッシュ活用）
COPY ./backend/pyproject.toml ./backend/uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# ソースをコピー
COPY ./backend ./

# プロジェクト本体を同期
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# フロントエンドのビルド成果物のみをコピー
COPY --from=frontend-builder /app/frontend/out /app/static-build

# 環境変数の設定
ENV STATIC_DIR=/app/static-build \
    LANGGRAPH_API_URL=http://localhost:2024 \
    WATCH_DIR=/app/workspace \
    PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# PORT 公開
EXPOSE 8080

# 起動スクリプトを作成
RUN echo '#!/bin/bash\nset -e\nuv run python file_main.py' > /app/start.sh && chmod +x /app/start.sh

# コンテナ起動時のコマンド
CMD ["bash", "/app/start.sh"]