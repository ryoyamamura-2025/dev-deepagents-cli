# ============================================
# Stage 1: フロントエンドのビルド
# ============================================
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

# package.jsonとpackage-lock.jsonをコピー
COPY frontend/package*.json ./
RUN npm ci

# ソースコードをコピーしてビルド
COPY frontend/ ./
RUN npm run build

# ============================================
# Stage 2: Pythonバックエンド
# ============================================
FROM python:3.13-slim

# uv（高速パッケージマネージャ）を取り込み
# 別イメージから /uv /uvx バイナリをコピーするワンライナー
COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

# # OpenCVや動画の処理用
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libgl1 \
#     ffmpeg \
#     && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ
WORKDIR /app

# 依存だけインストール（中間レイヤ）
COPY ./backend/pyproject.toml ./backend/uv.lock /app/
RUN uv sync --locked --no-install-project

# ここで初めてソースをコピー
COPY ./backend ./
COPY ./agent_config /root

# プロジェクト本体を同期
RUN uv sync

# フロントエンドのビルド成果物
COPY --from=frontend-builder /app/frontend/out /app/static-build

# 環境変数の設定
ENV STATIC_DIR=/app/static-build
ENV LANGGRAPH_API_URL=http://localhost:2024
ENV WATCH_DIR=/app/workspace
ENV PORT=8080

# プロジェクト本体を editable で同期（デフォルトが editable）
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

# PORT 公開
EXPOSE 8080

# 起動スクリプトを作成
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# LangGraphサーバーをバックグラウンドで起動\n\
uv run langgraph dev --allow-blocking --host 0.0.0.0 --port 2024 &\n\
\n\
# LangGraphサーバーの起動を待機\n\
sleep 3\n\
\n\
# FastAPIサーバーを起動\n\
uv run python file_main.py' > /app/start.sh && chmod +x /app/start.sh

# コンテナ起動時のコマンド
CMD ["bash", "/app/start.sh"]