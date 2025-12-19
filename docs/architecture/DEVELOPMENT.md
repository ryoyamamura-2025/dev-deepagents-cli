\# デプロイメント \& インフラストラクチャガイド



\## 概要



このガイドでは、Deep Agents CLIのローカル開発環境と本番環境のセットアップ、Docker構成、Google Cloud Runへのデプロイ方法を説明します。



\## 目次



1\. \[環境構成](#環境構成)

2\. \[ローカル開発環境](#ローカル開発環境)

3\. \[Docker構成](#docker構成)

4\. \[本番デプロイ](#本番デプロイ)

5\. \[環境変数](#環境変数)

6\. \[トラブルシューティング](#トラブルシューティング)



\## 環境構成



\### システム要件



\*\*開発環境\*\*:

\- Docker 20.10+

\- Docker Compose 2.0+

\- Node.js 22+ (ローカル開発の場合)

\- Python 3.13+ (ローカル開発の場合)

\- UV 0.8.14+ (Python パッケージマネージャー)



\*\*本番環境\*\*:

\- Docker対応ランタイム (Google Cloud Run, AWS Fargate, など)

\- Google Cloud Platform アカウント (GCP統合の場合)

\- 最小 1GB RAM, 1 vCPU



\### アーキテクチャ



```

┌─────────────────────────────────────────────┐

│           ロードバランサー (Optional)          │

└─────────────────┬───────────────────────────┘

&nbsp;                 │

┌─────────────────▼───────────────────────────┐

│          Dockerコンテナ (Port 8080)          │

│  ┌────────────────────────────────────────┐ │

│  │  Nginx/FastAPI (Port 8080)             │ │

│  │  - 静的ファイルサーブ (Next.js build)   │ │

│  │  - /api/\* → FastAPI                    │ │

│  │  - /agent/\* → LangGraphプロキシ        │ │

│  └──────────────┬─────────────────────────┘ │

│                 │                            │

│  ┌──────────────▼─────────────────────────┐ │

│  │  LangGraph Server (Port 2024)          │ │

│  │  - AIエージェントランタイム             │ │

│  │  - DeepAgents + ミドルウェア            │ │

│  └──────────────┬─────────────────────────┘ │

└─────────────────┼───────────────────────────┘

&nbsp;                 │

┌─────────────────▼───────────────────────────┐

│         外部サービス                         │

│  - Google Vertex AI (Gemini)               │

│  - Anthropic API (Claude)                  │

│  - Google Cloud Storage                    │

└─────────────────────────────────────────────┘

```



\## ローカル開発環境



\### 方法1: Docker Compose (推奨)



\*\*手順\*\*:



1\. \*\*環境変数を設定\*\*:

```bash

\# .envファイルをコピー

cp .env.example .env



\# .envを編集

nano .env

```



必須設定:

```bash

\# Google Cloud認証情報

GOOGLE\_APPLICATION\_CREDENTIALS=/path/to/service-account-key.json

GOOGLE\_CLOUD\_PROJECT=your-project-id



\# LLMモデル (Gemini)

GOOGLE\_MODEL=gemini-2.5-flash



\# または Anthropic Claude

ANTHROPIC\_API\_KEY=your-claude-api-key



\# 作業ディレクトリ

WATCH\_DIR=/app/workspace



\# CORS設定

CORS\_ORIGINS=http://localhost:3000,http://localhost:8124

```



2\. \*\*サービス起動\*\*:

```bash

docker compose up -d

```



\*\*Docker Compose 構成\*\*:

\- \*\*フロントエンド\*\*: `http://localhost:3000`

&nbsp; - コンテナ: `frontend`

&nbsp; - ベースイメージ: `node:22-slim`

&nbsp; - コマンド: `npm install \&\& npm run dev`

&nbsp; - ボリューム: `./frontend:/app` (ホットリロード)



\- \*\*バックエンド\*\*: `http://localhost:8124`

&nbsp; - コンテナ: `backend`

&nbsp; - ベースイメージ: `Dockerfile.dev`

&nbsp; - コマンド: `uv run python file\_main.py`

&nbsp; - ボリューム: `./backend:/app`, `./agent\_config:/app/agent\_config`



\*\*ログ確認\*\*:

```bash

\# 全サービスのログ

docker compose logs -f



\# 特定サービスのログ

docker compose logs -f backend

docker compose logs -f frontend

```



\*\*停止\*\*:

```bash

docker compose down

```



\*\*再ビルド\*\*:

```bash

docker compose up -d --build

```



\### 方法2: ローカル実行



\*\*フロントエンド\*\*:

```bash

cd frontend

npm install

npm run dev

\# → http://localhost:3000

```



\*\*バックエンド\*\* (別ターミナル):

```bash

cd backend



\# 依存関係インストール

uv sync --locked



\# FastAPIサーバー

uv run python file\_main.py

\# → http://localhost:8124



\# LangGraphサーバー (別ターミナル)

uv run langgraph dev --allow-blocking --host 0.0.0.0 --port 2024

```



\### 方法3: ローカルDocker単一イメージ



\*\*場所\*\*: `deploy\_local.sh`



```bash

\# ビルドと起動

./deploy\_local.sh build



\# 起動のみ

./deploy\_local.sh start



\# 再起動

./deploy\_local.sh restart



\# 停止

./deploy\_local.sh stop



\# ログ確認

./deploy\_local.sh logs

```



\*\*アクセス\*\*: `http://localhost:3232`



\*\*内部構成\*\*:

\- コンテナ名: `cli-agent-app`

\- イメージ名: `cli-agent-app:dev`

\- ポートマッピング: `3232:8080`

\- 環境変数: `.env.local` から読み込み



\*\*deploy\_local.sh の実装\*\*:

```bash

\#!/bin/bash



IMAGE\_NAME="cli-agent-app:dev"

CONTAINER\_NAME="cli-agent-app"



case "$1" in

&nbsp; build)

&nbsp;   # Dockerイメージをビルド

&nbsp;   docker build -t $IMAGE\_NAME .



&nbsp;   # 既存コンテナを停止・削除

&nbsp;   docker stop $CONTAINER\_NAME 2>/dev/null || true

&nbsp;   docker rm $CONTAINER\_NAME 2>/dev/null || true



&nbsp;   # 新しいコンテナを起動

&nbsp;   docker run -d \\

&nbsp;     --name $CONTAINER\_NAME \\

&nbsp;     -p 3232:8080 \\

&nbsp;     --env-file .env.local \\

&nbsp;     $IMAGE\_NAME

&nbsp;   ;;



&nbsp; start)

&nbsp;   docker start $CONTAINER\_NAME

&nbsp;   ;;



&nbsp; restart)

&nbsp;   docker restart $CONTAINER\_NAME

&nbsp;   ;;



&nbsp; stop)

&nbsp;   docker stop $CONTAINER\_NAME

&nbsp;   ;;



&nbsp; logs)

&nbsp;   docker logs -f $CONTAINER\_NAME

&nbsp;   ;;



&nbsp; \*)

&nbsp;   echo "Usage: $0 {build|start|restart|stop|logs}"

&nbsp;   exit 1

&nbsp;   ;;

esac

```



\## Docker構成



\### Dockerfile (本番用マルチステージビルド)



\*\*場所\*\*: `Dockerfile`



\*\*ステージ1: フロントエンドビルド\*\*



```dockerfile

\# ステージ1: フロントエンドビルド

FROM node:22-slim AS frontend-builder



WORKDIR /app/frontend



\# 依存関係のインストール

COPY frontend/package\*.json ./

RUN npm ci



\# ソースコードをコピー

COPY frontend/ ./



\# Next.jsビルド (静的エクスポート)

RUN npm run build



\# 出力: /app/frontend/out/

```



\*\*ステージ2: バックエンド + 統合\*\*



```dockerfile

\# ステージ2: Pythonバックエンド

FROM python:3.13-slim



WORKDIR /app



\# UVパッケージマネージャーをインストール

RUN pip install uv==0.8.14



\# Python依存関係をインストール

COPY backend/pyproject.toml backend/uv.lock ./backend/

RUN cd backend \&\& uv sync --locked --no-dev



\# バックエンドコードをコピー

COPY backend/ ./backend/



\# フロントエンドビルドをコピー

COPY --from=frontend-builder /app/frontend/out ./static-build



\# エージェント設定をコピー (オプション)

COPY agent\_config/ ./agent\_config/



\# ポート公開

EXPOSE 8080



\# 起動スクリプト

CMD \["sh", "-c", "\\

&nbsp; cd backend \&\& \\

&nbsp; uv run langgraph dev --allow-blocking --host 0.0.0.0 --port 2024 \& \\

&nbsp; uv run python file\_main.py \\

"]

```



\*\*最適化ポイント\*\*:

\- マルチステージビルドで最終イメージサイズを削減

\- `npm ci` で高速な依存関係インストール

\- `--no-dev` で本番依存関係のみインストール

\- レイヤーキャッシュを活用した高速ビルド



\### Dockerfile.dev (開発用)



\*\*場所\*\*: `Dockerfile.dev`



```dockerfile

FROM python:3.13-slim



WORKDIR /app



\# UVインストール

RUN pip install uv==0.8.14



\# 依存関係インストール (開発依存含む)

COPY backend/pyproject.toml backend/uv.lock ./backend/

RUN cd backend \&\& uv sync --locked



\# ボリュームマウント用 (コードは実行時にマウント)

VOLUME /app/backend

VOLUME /app/agent\_config



\# 開発サーバー起動

CMD \["sh", "-c", "\\

&nbsp; cd backend \&\& \\

&nbsp; uv run langgraph dev --allow-blocking --host 0.0.0.0 --port 2024 \& \\

&nbsp; uv run python file\_main.py \\

"]

```



\### Dockerfile\_node.dev (フロントエンド開発用)



\*\*場所\*\*: `Dockerfile\_node.dev`



```dockerfile

FROM node:22-slim



WORKDIR /app



\# 依存関係インストール

COPY frontend/package\*.json ./

RUN npm install



\# ボリュームマウント用

VOLUME /app



\# 開発サーバー起動

CMD \["npm", "run", "dev"]

```



\### docker-compose.yaml



\*\*場所\*\*: `docker-compose.yaml`



```yaml

version: '3.8'



services:

&nbsp; frontend:

&nbsp;   build:

&nbsp;     context: ./frontend

&nbsp;     dockerfile: ../Dockerfile\_node.dev

&nbsp;   ports:

&nbsp;     - "3000:3000"

&nbsp;   volumes:

&nbsp;     - ./frontend:/app

&nbsp;     - /app/node\_modules  # node\_modulesを除外

&nbsp;   env\_file:

&nbsp;     - .env.development

&nbsp;   command: npm run dev



&nbsp; backend:

&nbsp;   build:

&nbsp;     context: .

&nbsp;     dockerfile: Dockerfile.dev

&nbsp;   ports:

&nbsp;     - "8124:8124"

&nbsp;     - "2024:2024"

&nbsp;   volumes:

&nbsp;     - ./backend:/app/backend

&nbsp;     - ./agent\_config:/app/agent\_config

&nbsp;   env\_file:

&nbsp;     - .env

&nbsp;   environment:

&nbsp;     - WATCH\_DIR=/app/workspace

&nbsp;     - CORS\_ORIGINS=http://localhost:3000

&nbsp;   command: sh -c "cd backend \&\& uv run langgraph dev --allow-blocking --host 0.0.0.0 --port 2024 \& uv run python file\_main.py"



volumes:

&nbsp; node\_modules:

```



\## 本番デプロイ



\### Google Cloud Run へのデプロイ



\*\*前提条件\*\*:

1\. Google Cloud Platform (GCP) アカウント

2\. `gcloud` CLI インストール

3\. Artifact Registry 有効化

4\. サービスアカウント作成 (Vertex AI, Cloud Storage 権限)



\*\*手順\*\*:



1\. \*\*deploy.sh を作成\*\*:

```bash

cp deploy.sh.example deploy.sh

chmod +x deploy.sh

```



\*\*deploy.sh の内容\*\*:

```bash

\#!/bin/bash



set -e



PROJECT\_ID="your-gcp-project-id"

REGION="us-central1"

SERVICE\_NAME="deep-agents-cli"

IMAGE\_NAME="gcr.io/${PROJECT\_ID}/${SERVICE\_NAME}"



\# 1. Dockerイメージをビルド

echo "Building Docker image..."

docker build -t $IMAGE\_NAME .



\# 2. Google Container Registryにプッシュ

echo "Pushing image to GCR..."

docker push $IMAGE\_NAME



\# 3. Cloud Runにデプロイ

echo "Deploying to Cloud Run..."

gcloud run deploy $SERVICE\_NAME \\

&nbsp; --image $IMAGE\_NAME \\

&nbsp; --platform managed \\

&nbsp; --region $REGION \\

&nbsp; --allow-unauthenticated \\

&nbsp; --memory 2Gi \\

&nbsp; --cpu 2 \\

&nbsp; --timeout 3600 \\

&nbsp; --set-env-vars-file .env.yaml



echo "Deployment complete!"

echo "Service URL: https://${SERVICE\_NAME}-${PROJECT\_ID}.a.run.app"

```



2\. \*\*環境変数を設定\*\* (`.env.yaml`):

```yaml

GOOGLE\_CLOUD\_PROJECT: "your-project-id"

GOOGLE\_MODEL: "gemini-2.5-flash"

WATCH\_DIR: "/app/workspace"

CORS\_ORIGINS: "https://your-domain.com"

```



\*\*重要\*\*: サービスアカウントキーは環境変数ではなく、Cloud Runのシークレットマネージャーを使用:

```bash

\# シークレット作成

gcloud secrets create google-credentials --data-file=service-account-key.json



\# Cloud Runにマウント

gcloud run deploy $SERVICE\_NAME \\

&nbsp; --set-secrets=/secrets/google-credentials=google-credentials:latest

```



3\. \*\*デプロイ実行\*\*:

```bash

./deploy.sh

```



4\. \*\*デプロイ後の確認\*\*:

```bash

\# サービスURL取得

gcloud run services describe deep-agents-cli --region us-central1 --format 'value(status.url)'



\# ログ確認

gcloud logs tail --service deep-agents-cli

```



\### その他のプラットフォーム



\#### AWS Fargate / ECS



1\. \*\*ECRリポジトリ作成\*\*:

```bash

aws ecr create-repository --repository-name deep-agents-cli

```



2\. \*\*イメージをプッシュ\*\*:

```bash

\# ログイン

aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com



\# ビルド \& プッシュ

docker build -t deep-agents-cli .

docker tag deep-agents-cli:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/deep-agents-cli:latest

docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/deep-agents-cli:latest

```



3\. \*\*Fargateタスク定義作成\*\*:

```json

{

&nbsp; "family": "deep-agents-cli",

&nbsp; "networkMode": "awsvpc",

&nbsp; "containerDefinitions": \[

&nbsp;   {

&nbsp;     "name": "app",

&nbsp;     "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/deep-agents-cli:latest",

&nbsp;     "portMappings": \[{"containerPort": 8080}],

&nbsp;     "environment": \[

&nbsp;       {"name": "WATCH\_DIR", "value": "/app/workspace"}

&nbsp;     ],

&nbsp;     "secrets": \[

&nbsp;       {"name": "GOOGLE\_APPLICATION\_CREDENTIALS", "valueFrom": "arn:aws:secretsmanager:..."}

&nbsp;     ]

&nbsp;   }

&nbsp; ],

&nbsp; "requiresCompatibilities": \["FARGATE"],

&nbsp; "cpu": "1024",

&nbsp; "memory": "2048"

}

```



\#### Kubernetes / k8s



\*\*Deployment YAML\*\*:

```yaml

apiVersion: apps/v1

kind: Deployment

metadata:

&nbsp; name: deep-agents-cli

spec:

&nbsp; replicas: 2

&nbsp; selector:

&nbsp;   matchLabels:

&nbsp;     app: deep-agents-cli

&nbsp; template:

&nbsp;   metadata:

&nbsp;     labels:

&nbsp;       app: deep-agents-cli

&nbsp;   spec:

&nbsp;     containers:

&nbsp;     - name: app

&nbsp;       image: gcr.io/your-project/deep-agents-cli:latest

&nbsp;       ports:

&nbsp;       - containerPort: 8080

&nbsp;       env:

&nbsp;       - name: WATCH\_DIR

&nbsp;         value: "/app/workspace"

&nbsp;       - name: GOOGLE\_CLOUD\_PROJECT

&nbsp;         value: "your-project-id"

&nbsp;       volumeMounts:

&nbsp;       - name: google-credentials

&nbsp;         mountPath: /secrets

&nbsp;         readOnly: true

&nbsp;     volumes:

&nbsp;     - name: google-credentials

&nbsp;       secret:

&nbsp;         secretName: google-credentials

---

apiVersion: v1

kind: Service

metadata:

&nbsp; name: deep-agents-cli

spec:

&nbsp; selector:

&nbsp;   app: deep-agents-cli

&nbsp; ports:

&nbsp; - port: 80

&nbsp;   targetPort: 8080

&nbsp; type: LoadBalancer

```



\## 環境変数



\### 必須環境変数



| 変数名 | 説明 | 例 |

|--------|------|-----|

| `GOOGLE\_APPLICATION\_CREDENTIALS` | GCPサービスアカウントキーのパス | `/secrets/key.json` |

| `GOOGLE\_CLOUD\_PROJECT` | GCPプロジェクトID | `my-project-123` |

| `GOOGLE\_MODEL` | 使用するLLMモデル | `gemini-2.5-flash` |

| `WATCH\_DIR` | ファイル監視ディレクトリ | `/app/workspace` |

| `CORS\_ORIGINS` | 許可するCORSオリジン (カンマ区切り) | `https://example.com,http://localhost:3000` |



\### オプション環境変数



| 変数名 | 説明 | デフォルト値 |

|--------|------|-------------|

| `ANTHROPIC\_API\_KEY` | AnthropicのAPIキー (Claude使用時) | なし |

| `SKILL\_DIR` | スキルディレクトリのパス | `~/.deepagents/agent/skills` |

| `WORKING\_DIR` | エージェント作業ディレクトリ | `/app/workspace` |

| `MAX\_FILE\_SIZE` | 最大ファイルサイズ (バイト) | `10485760` (10MB) |

| `PORT` | FastAPIサーバーポート | `8080` |

| `LANGGRAPH\_PORT` | LangGraphサーバーポート | `2024` |



\### 環境別設定ファイル



\*\*開発環境\*\* (`.env`):

```bash

GOOGLE\_APPLICATION\_CREDENTIALS=/Users/you/keys/gcp-key.json

GOOGLE\_CLOUD\_PROJECT=dev-project-123

GOOGLE\_MODEL=gemini-2.5-flash

WATCH\_DIR=/Users/you/dev-deepagents-cli/backend/workspace

CORS\_ORIGINS=http://localhost:3000,http://localhost:8124

```



\*\*本番環境\*\* (`.env.yaml` for Cloud Run):

```yaml

GOOGLE\_CLOUD\_PROJECT: "prod-project-456"

GOOGLE\_MODEL: "gemini-2.5-flash"

WATCH\_DIR: "/app/workspace"

CORS\_ORIGINS: "https://app.example.com"

```



\### シークレット管理



\*\*Google Cloud Secret Manager\*\*:

```bash

\# シークレット作成

echo -n "your-api-key" | gcloud secrets create anthropic-api-key --data-file=-



\# Cloud Runでマウント

gcloud run deploy deep-agents-cli \\

&nbsp; --set-secrets=ANTHROPIC\_API\_KEY=anthropic-api-key:latest

```



\*\*AWS Secrets Manager\*\*:

```bash

\# シークレット作成

aws secretsmanager create-secret \\

&nbsp; --name anthropic-api-key \\

&nbsp; --secret-string "your-api-key"



\# ECSタスク定義で参照

{

&nbsp; "secrets": \[

&nbsp;   {

&nbsp;     "name": "ANTHROPIC\_API\_KEY",

&nbsp;     "valueFrom": "arn:aws:secretsmanager:region:account:secret:anthropic-api-key"

&nbsp;   }

&nbsp; ]

}

```



\## エージェント設定のデプロイ



\### Google Cloud Storage (GCS) との統合



\*\*場所\*\*: `backend/file\_api/cloud\_storage.py`



\*\*機能\*\*: 起動時にGCSからエージェント設定をダウンロード



\*\*設定手順\*\*:



1\. \*\*GCSバケット作成\*\*:

```bash

gsutil mb gs://your-project-agent-config

```



2\. \*\*設定ファイルをアップロード\*\*:

```bash

\# スクリプトを使用

python scripts/upload\_agent\_config.py --bucket your-project-agent-config --source ./agent\_config

```



または手動:

```bash

gsutil -m cp -r ./agent\_config/.deepagents gs://your-project-agent-config/

```



3\. \*\*環境変数を設定\*\*:

```bash

AGENT\_CONFIG\_BUCKET=your-project-agent-config

```



4\. \*\*自動ダウンロード\*\* (`file\_main.py:startup\_event`):

```python

@app.on\_event("startup")

async def startup\_event():

&nbsp;   from file\_api.cloud\_storage import ensure\_agent\_config



&nbsp;   # GCSから設定をダウンロード (ローカルになければ)

&nbsp;   await ensure\_agent\_config()

```



\*\*実装\*\* (`cloud\_storage.py`):

```python

async def ensure\_agent\_config():

&nbsp;   """GCSからエージェント設定をダウンロード (フォールバック付き)"""

&nbsp;   local\_path = Path("/app/agent\_config/.deepagents")



&nbsp;   # ローカルに存在すれば何もしない

&nbsp;   if local\_path.exists():

&nbsp;       logger.info("Agent config found locally")

&nbsp;       return



&nbsp;   # GCSからダウンロード

&nbsp;   bucket\_name = os.getenv("AGENT\_CONFIG\_BUCKET")

&nbsp;   if bucket\_name:

&nbsp;       logger.info(f"Downloading agent config from GCS: {bucket\_name}")

&nbsp;       await download\_agent\_config\_from\_gcs(bucket\_name, local\_path)

&nbsp;   else:

&nbsp;       logger.warning("No AGENT\_CONFIG\_BUCKET set, using default config")

```



\## モニタリング \& ログ



\### ログ出力



\*\*FastAPIログ\*\*:

```python

import logging



logging.basicConfig(

&nbsp;   level=logging.INFO,

&nbsp;   format="%(asctime)s \[%(levelname)s] %(name)s: %(message)s"

)



logger = logging.getLogger(\_\_name\_\_)

logger.info("Server started")

```



\*\*LangGraphログ\*\*:

LangGraphサーバーは標準出力にログを出力します。



\### Cloud Run ログ確認



```bash

\# 最新ログを表示

gcloud logs tail --service deep-agents-cli --format json



\# エラーログのみ

gcloud logs read --service deep-agents-cli --filter "severity>=ERROR"

```



\### メトリクス (Cloud Monitoring)



Cloud Runは自動的に以下のメトリクスを収集:

\- リクエスト数

\- レスポンスタイム

\- エラー率

\- CPU/メモリ使用率



\*\*カスタムメトリクス\*\*:

```python

from google.cloud import monitoring\_v3



client = monitoring\_v3.MetricServiceClient()

project\_name = f"projects/{project\_id}"



\# カスタムメトリクスを送信

series = monitoring\_v3.TimeSeries()

series.metric.type = "custom.googleapis.com/agent/execution\_time"

series.resource.type = "cloud\_run\_revision"

\# ...

client.create\_time\_series(name=project\_name, time\_series=\[series])

```



\## トラブルシューティング



\### デプロイが失敗する



\*\*症状\*\*: Docker ビルドが失敗する



\*\*解決策\*\*:

1\. Dockerfileの構文を確認

2\. ビルドコンテキストに必要なファイルがあるか確認

3\. `.dockerignore` が重要なファイルを除外していないか確認

4\. マルチステージビルドの各ステージを個別にテスト:

&nbsp;  ```bash

&nbsp;  docker build --target frontend-builder -t test-frontend .

&nbsp;  ```



\### Cloud Runでコンテナが起動しない



\*\*症状\*\*: デプロイ成功後、コンテナがクラッシュ



\*\*解決策\*\*:

1\. ログを確認:

&nbsp;  ```bash

&nbsp;  gcloud logs tail --service deep-agents-cli

&nbsp;  ```

2\. 環境変数が正しく設定されているか確認

3\. メモリ/CPU制限を確認 (`--memory 2Gi --cpu 2`)

4\. ヘルスチェックエンドポイント (`/health`) が応答しているか確認



\### LLM API呼び出しが失敗する



\*\*症状\*\*: `401 Unauthorized` または `403 Forbidden`



\*\*解決策\*\*:

1\. API キーが正しく設定されているか確認

2\. サービスアカウントに必要な権限があるか確認:

&nbsp;  - Vertex AI: `roles/aiplatform.user`

&nbsp;  - Cloud Storage: `roles/storage.objectViewer`

3\. API が有効化されているか確認:

&nbsp;  ```bash

&nbsp;  gcloud services enable aiplatform.googleapis.com

&nbsp;  ```



\### ファイル監視が動作しない



\*\*症状\*\*: ファイル変更がUIに反映されない



\*\*解決策\*\*:

1\. `WATCH\_DIR` が正しく設定されているか確認

2\. ファイルパーミッションを確認

3\. WebSocket接続が確立されているか確認 (ブラウザのネットワークタブ)

4\. ファイルウォッチャーが起動しているか確認:

&nbsp;  ```bash

&nbsp;  docker logs backend | grep "FileWatcher"

&nbsp;  ```



\### パフォーマンスが遅い



\*\*症状\*\*: レスポンスタイムが長い



\*\*解決策\*\*:

1\. LLMモデルを軽量化 (`gemini-2.5-flash` など)

2\. Cloud Runのメモリ/CPU を増やす

3\. キャッシュを有効化 (LangChain の `cache=True`)

4\. 不要なミドルウェアを削除



\## セキュリティベストプラクティス



\### 1. APIキー管理



\- 環境変数にハードコードしない

\- Secret Manager を使用

\- `.env` ファイルを `.gitignore` に追加



\### 2. CORS設定



本番環境では特定のオリジンのみ許可:

```python

CORS\_ORIGINS=https://app.example.com

```



\### 3. 認証・認可



フロントエンドに認証を追加:

```typescript

// Firebase Auth, Auth0, など

const user = await firebase.auth().currentUser

const token = await user.getIdToken()



// APIリクエストにトークンを含める

fetch("/api/files", {

&nbsp; headers: { "Authorization": `Bearer ${token}` }

})

```



バックエンドで検証:

```python

from fastapi import Depends, HTTPException

from fastapi.security import HTTPBearer



security = HTTPBearer()



async def verify\_token(credentials: HTTPCredentials = Depends(security)):

&nbsp;   token = credentials.credentials

&nbsp;   # トークン検証ロジック

&nbsp;   if not valid:

&nbsp;       raise HTTPException(status\_code=401)

```



\### 4. ファイルアップロード制限



```python

\# file\_api/config.py

MAX\_FILE\_SIZE = 10 \* 1024 \* 1024  # 10MB



\# file\_main.py

@app.post("/api/files/upload")

async def upload\_files(files: List\[UploadFile]):

&nbsp;   for file in files:

&nbsp;       if file.size > MAX\_FILE\_SIZE:

&nbsp;           raise HTTPException(status\_code=413, detail="File too large")

```



\### 5. レートリミット



```bash

pip install slowapi

```



```python

from slowapi import Limiter

from slowapi.util import get\_remote\_address



limiter = Limiter(key\_func=get\_remote\_address)

app.state.limiter = limiter



@app.get("/api/files")

@limiter.limit("100/minute")

async def list\_files():

&nbsp;   # ...

```



\## パフォーマンス最適化



\### 1. Dockerイメージサイズ削減



\- マルチステージビルドを使用

\- `.dockerignore` で不要なファイルを除外

\- Alpine ベースイメージを検討 (ただし互換性に注意)



\### 2. キャッシュ戦略



\*\*LangChain キャッシュ\*\*:

```python

from langchain.cache import InMemoryCache

from langchain.globals import set\_llm\_cache



set\_llm\_cache(InMemoryCache())

```



\*\*HTTP キャッシュ\*\*:

```python

from fastapi.responses import Response



@app.get("/api/files")

async def list\_files(response: Response):

&nbsp;   response.headers\["Cache-Control"] = "public, max-age=300"

&nbsp;   # ...

```



\### 3. 並行処理



```python

import asyncio



async def process\_multiple\_files(files: List\[str]):

&nbsp;   tasks = \[process\_file(f) for f in files]

&nbsp;   results = await asyncio.gather(\*tasks)

&nbsp;   return results

```



\## 参考資料



\- \[Docker ドキュメント](https://docs.docker.com/)

\- \[Docker Compose ドキュメント](https://docs.docker.com/compose/)

\- \[Google Cloud Run ドキュメント](https://cloud.google.com/run/docs)

\- \[AWS Fargate ドキュメント](https://docs.aws.amazon.com/fargate/)

\- \[Kubernetes ドキュメント](https://kubernetes.io/docs/)

\- \[FastAPI デプロイガイド](https://fastapi.tiangolo.com/deployment/)



\[← アーキテクチャ概要に戻る](../../ARCHITECTURE.md)

