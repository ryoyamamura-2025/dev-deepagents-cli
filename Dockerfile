# ステージ1: フロントエンドビルド
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ステージ2: 本番環境
# 1) ベースイメージ：軽量な Python
FROM python:3.13-slim

# 2) uv（高速パッケージマネージャ）を取り込み
#    別イメージから /uv /uvx バイナリをコピーするワンライナー
COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

# # OpenCVや動画の処理用
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libgl1 \
#     ffmpeg \
#     && rm -rf /var/lib/apt/lists/*

# 3) 作業ディレクトリ
WORKDIR /app

# 4) 依存だけインストール（中間レイヤ）
COPY ./backend/pyproject.toml ./backend/uv.lock /app/
RUN uv sync --locked --no-install-project

# 5) ここで初めてソースをコピー
COPY ./backend/pyproject.toml ./backend/uv.lock ./
COPY ./backend ./

# フロントエンドのビルド成果物
COPY --from=frontend-builder /app/frontend/out ./frontend/out

# 6) プロジェクト本体を editable で同期（デフォルトが editable）
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

# 7 PORT設定
EXPOSE 8124

# 8) コンテナ起動時のコマンド
CMD ["bash", "/app/start.sh"]