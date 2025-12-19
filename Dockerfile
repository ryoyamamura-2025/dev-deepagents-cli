# ============================================
# Stage 1: フロントエンドのビルド (変更なし/最適化)
# ============================================
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# ============================================
# Stage 2: 実行環境 (Python 3.13 + Node.jsバイナリ + FFmpeg)
# ============================================
FROM python:3.13-slim

# 1. uvを取り込み
COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

# 2. Node.js 22 の実行環境だけをコピー (aptを使わない技)
# node-slimイメージからバイナリとライブラリだけを持ってくることで軽量化
COPY --from=node:22-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-slim /usr/local/lib/node_modules /usr/local/lib/node_modules
# npmを使えるようにシンボリックリンクを貼る
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

# 3. 最小限のランタイム依存（ffmpeg等）のみインストール
# --no-install-recommends は必須
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     ffmpeg \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 4. Node.jsのグローバルパッケージ(docx)のインストール
# nodeバイナリが既にあるので実行可能
RUN npm install -g docx && npm cache clean --force

WORKDIR /app

# 5. Python依存関係のインストール (uvのキャッシュ活用)
COPY ./backend/pyproject.toml ./backend/uv.lock /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# 6. ソースとフロントエンド成果物のコピー
COPY ./backend ./
COPY --from=frontend-builder /app/frontend/out /app/static-build

# プロジェクト本体の同期
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# 実行設定
# 環境変数の設定
ENV STATIC_DIR=/app/static-build \
    LANGGRAPH_API_URL=http://localhost:2024 \
    WATCH_DIR_BASE=/app/workspace \
    PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8080

# 起動コマンド
CMD ["uv", "run", "python", "main.py"]