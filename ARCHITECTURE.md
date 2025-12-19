\# Deep Agents CLI - アーキテクチャガイド



\## 概要



Deep Agents CLIは、LangGraphとDeepAgentsフレームワークを使用したフルスタックAIエージェントアプリケーションです。ユーザーはブラウザUIまたはCLIから対話的にAIエージェントを操作でき、ファイルシステムへのアクセス、ツール実行承認、長期記憶、スキルシステムなどの高度な機能を提供します。



\## クイックナビゲーション



\- \*\*\[フロントエンドガイド](./docs/architecture/FRONTEND.md)\*\* - React/Next.jsアプリケーションの構造と開発方法

\- \*\*\[バックエンドガイド](./docs/architecture/BACKEND.md)\*\* - Python/FastAPI/LangGraphエージェントの実装詳細

\- \*\*\[デプロイメントガイド](./docs/architecture/DEPLOYMENT.md)\*\* - Docker、開発環境、本番環境のセットアップ



\## プロジェクト構成



```

dev-deepagents-cli/

├── frontend/                    # Next.js 16 + React 19 SPAアプリケーション

│   ├── src/app/                # Next.js App Router

│   │   ├── components/         # UIコンポーネント (Chat, FileBrowser, Thread)

│   │   ├── hooks/              # カスタムフック (useChat, useThreads, useFileBrowser)

│   │   ├── types/              # TypeScript型定義

│   │   └── page.tsx            # メインエントリーポイント (322行)

│   └── package.json            # 76の依存関係

│

├── backend/                     # Python 3.13 バックエンド

│   ├── backend\_agent\_main.py   # LangGraphエージェント定義 (546行)

│   ├── file\_main.py            # FastAPIサーバー (550行)

│   ├── deepagents\_cli/         # コアライブラリ

│   │   ├── agent.py            # エージェント作成・管理 (466行)

│   │   ├── execution.py        # タスク実行エンジン (681行)

│   │   ├── agent\_memory.py     # 長期記憶システム (327行)

│   │   ├── skills/             # スキルシステム

│   │   └── tools.py            # カスタムツール (182行)

│   └── file\_api/               # ファイルシステムAPI

│

├── agent\_config/               # エージェント設定

│   └── .deepagents/agent/      # システムプロンプトとスキル定義

│

├── docs/                       # ドキュメント

│   └── architecture/           # アーキテクチャドキュメント

│

├── Dockerfile                  # 本番マルチステージビルド

├── docker-compose.yaml         # ローカル開発オーケストレーション

└── deploy\_local.sh             # ローカルデプロイスクリプト

```



\## 技術スタック



\### フロントエンド



| カテゴリ | 技術 | 用途 |

|---------|------|------|

| \*\*フレームワーク\*\* | Next.js 16.0.7, React 19.1.0 | SPAフレームワーク (静的エクスポート) |

| \*\*言語\*\* | TypeScript 5.9.3 | 型安全性 |

| \*\*ビルドツール\*\* | Turbopack | 高速バンドラー |

| \*\*UIライブラリ\*\* | Radix UI, Shadcn UI | アクセシブルなコンポーネント |

| \*\*スタイリング\*\* | Tailwind CSS 3.4.4 | ユーティリティファーストCSS |

| \*\*状態管理\*\* | LangGraph SDK, Nuqs | AI通信とURL状態 |

| \*\*データフェッチ\*\* | SWR, LangGraph React | キャッシングとストリーミング |

| \*\*その他\*\* | React Markdown, React Syntax Highlighter | コンテンツレンダリング |



\### バックエンド



| カテゴリ | 技術 | 用途 |

|---------|------|------|

| \*\*ランタイム\*\* | Python 3.13 | メイン言語 |

| \*\*パッケージ管理\*\* | UV 0.8.14 | 高速パッケージマネージャー |

| \*\*Webフレームワーク\*\* | FastAPI 0.124.4 | ファイルAPIサーバー |

| \*\*AIフレームワーク\*\* | LangGraph CLI 0.4.10+, LangChain 1.2.0 | エージェントオーケストレーション |

| \*\*LLM SDK\*\* | Anthropic Claude SDK, Google GenAI | Claude/Gemini統合 |

| \*\*クラウド\*\* | Google Cloud Storage 2.18.2 | 設定ストレージ |

| \*\*ミドルウェア\*\* | カスタム実装 | Memory, Skills, Shell |

| \*\*ユーティリティ\*\* | Rich 14.2.0, Watchdog 6.0.0 | CLI UI、ファイル監視 |



\### インフラストラクチャ



| カテゴリ | 技術 | 用途 |

|---------|------|------|

| \*\*コンテナ\*\* | Docker, Docker Compose | 開発・本番環境 |

| \*\*デプロイ\*\* | Google Cloud Run | サーバーレスデプロイ |

| \*\*ストレージ\*\* | Google Cloud Storage | エージェント設定 |

| \*\*AI\*\* | Google Vertex AI | LLM推論 (Gemini 2.5 Flash) |



\## コアコンポーネント



\### 1. フロントエンド - ユーザーインターフェース



\*\*エントリーポイント\*\*: `frontend/src/app/page.tsx:1`



3パネルレイアウト:

\- \*\*スレッドリスト\*\* - 会話履歴の管理

\- \*\*ファイルブラウザ\*\* - リアルタイムファイルシステム操作

\- \*\*チャットインターフェース\*\* - エージェントとの対話



\*\*主要機能\*\*:

\- リアルタイムメッセージストリーミング

\- ツール実行承認 (Human-in-the-Loop)

\- ファイル差分表示

\- サブエージェント実行の可視化

\- タスク追跡 (Todo表示)



詳細は \[フロントエンドガイド](./docs/architecture/FRONTEND.md) を参照。



\### 2. バックエンド - AIエージェントエンジン



\*\*エントリーポイント\*\*:

\- FastAPI: `backend/file\_main.py:1`

\- LangGraph: `backend/backend\_agent\_main.py:1`



\*\*アーキテクチャ\*\*:

```

\[ブラウザ]

&nbsp;   ↓

\[FastAPI (Port 8080)]

&nbsp;   ↓ (プロキシ)

\[LangGraph Server (Port 2024)]

&nbsp;   ↓

\[DeepAgents + ミドルウェア]

&nbsp;   ↓

\[Claude/Gemini API]

```



\*\*ミドルウェアスタック\*\*:

1\. \*\*AgentMemoryMiddleware\*\* - プロジェクト/ユーザー記憶の注入

2\. \*\*SkillsMiddleware\*\* - 動的スキルのロードと注入

3\. \*\*ShellMiddleware\*\* - シェルコマンド実行

4\. \*\*InterruptOnConfig\*\* - ツール承認ワークフロー



詳細は \[バックエンドガイド](./docs/architecture/BACKEND.md) を参照。



\### 3. LangGraph エージェント



\*\*定義ファイル\*\*: `backend/backend\_agent\_main.py:73-100`



DeepAgentsライブラリの `create\_deep\_agent()` を使用してエージェントグラフを作成:

\- \*\*再帰制限\*\*: 1000ステップ

\- \*\*チェックポイント\*\*: インメモリストレージ

\- \*\*バックエンド\*\*: カスタムFilesystemBackend (UIファイル追跡用)



\*\*エージェント状態\*\*:

```python

{

&nbsp; messages: Message\[]        # 会話履歴

&nbsp; todos: TodoItem\[]          # タスク追跡

&nbsp; files: Dict\[str, str]      # ファイル辞書

&nbsp; email?: EmailObject        # メールメタデータ

&nbsp; ui?: Any                   # カスタムUI状態

}

```



\### 4. ファイルシステムAPI



\*\*実装\*\*: `backend/file\_main.py:211-491`



\*\*エンドポイント\*\*:

\- `GET /api/files` - ファイルリスト取得

\- `GET /api/files/{path}` - ファイル内容読み取り (シンタックスハイライト付き)

\- `PUT /api/files/{path}` - ファイル更新/作成

\- `DELETE /api/files/{path}` - ファイル削除

\- `POST /api/files/upload` - ファイルアップロード

\- `WebSocket /ws` - リアルタイムファイルイベント



\*\*ファイル監視\*\*: Watchdogライブラリを使用してファイルシステムの変更を検出し、WebSocket経由でクライアントに通知。



\### 5. スキルシステム



\*\*場所\*\*:

\- ユーザーレベル: `~/.deepagents/{AGENT\_NAME}/skills/`

\- プロジェクトレベル: `agent\_config/.deepagents/agent/skills/`



\*\*実装\*\*: `backend/deepagents\_cli/skills/`



各スキルは `SKILL.md` ファイルで定義され、YAMLフロントマターでメタデータを含みます:

```yaml

---

name: skill-name

description: Short description

---

\# Detailed skill instructions

```



スキルは動的にロードされ、エージェントのシステムプロンプトに注入されます。



\### 6. 長期記憶システム



\*\*実装\*\*: `backend/deepagents\_cli/agent\_memory.py:1`



階層的な記憶ロード:

1\. エンタープライズレベル記憶

2\. プロジェクトレベル記憶 (`{project\_root}/.deepagents/agent.md`)

3\. ユーザーレベル記憶 (`~/.deepagents/{AGENT\_NAME}/agent.md`)



記憶はミドルウェアによってLLMリクエスト時に自動注入されます。



\## 開発ワークフロー



\### ローカル開発



\*\*Docker Composeを使用\*\*:

```bash

\# 環境変数を設定

cp .env.example .env

\# 編集: GOOGLE\_APPLICATION\_CREDENTIALS, GOOGLE\_CLOUD\_PROJECT, etc.



\# サービス起動

docker compose up -d



\# ログ確認

docker compose logs -f



\# 停止

docker compose down

```



\- フロントエンド: http://localhost:3000

\- バックエンド: http://localhost:8124



\*\*または個別に実行\*\*:

```bash

\# フロントエンド

cd frontend

npm install

npm run dev



\# バックエンド (別ターミナル)

cd backend

uv sync --locked

uv run python file\_main.py  # FastAPIサーバー

\# 別ターミナルで:

uv run langgraph dev --allow-blocking --host 0.0.0.0 --port 2024

```



\### 本番ビルド



\*\*Docker単一イメージ\*\*:

```bash

./deploy\_local.sh build

./deploy\_local.sh start

```



アクセス: http://localhost:3232



詳細は \[デプロイメントガイド](./docs/architecture/DEPLOYMENT.md) を参照。



\## 重要な設定ファイル



| ファイル | 用途 |

|---------|------|

| `frontend/next.config.ts` | Next.js設定 (静的エクスポート有効) |

| `frontend/tailwind.config.mjs` | Tailwindテーマ設定 |

| `backend/langgraph.json` | LangGraphグラフ定義 |

| `backend/pyproject.toml` | Python依存関係 |

| `backend/file\_api/config.py` | ファイルAPI設定 (CORS, 監視ディレクトリ) |

| `.env` | 環境変数 (GCP認証情報、モデル設定) |

| `Dockerfile` | 本番マルチステージビルド |

| `docker-compose.yaml` | ローカル開発環境 |



\## アーキテクチャの特徴



\### 1. リアルタイム通信

\- \*\*Server-Sent Events (SSE)\*\*: LangGraphからのメッセージストリーミング

\- \*\*WebSocket\*\*: ファイルシステムイベントのリアルタイム通知



\### 2. Human-in-the-Loop (HITL)

\- ツール実行前に承認を要求

\- ファイル変更の差分表示

\- 承認/拒否/自動承認の選択肢



\### 3. マルチテナント

\- LangGraphのスレッド機能で複数の会話を管理

\- 各スレッドは独立した状態を持つ



\### 4. 拡張性

\- ミドルウェアアーキテクチャで機能追加が容易

\- スキルシステムでカスタム機能を動的に追加



\### 5. クラウドネイティブ

\- Docker/Cloud Run対応

\- GCS統合でスケーラブルな設定管理

\- Vertex AI統合



\## よくある開発タスク



\### 新しいUIコンポーネントを追加



1\. `frontend/src/app/components/` に新しいコンポーネントファイルを作成

2\. 必要に応じて `frontend/src/app/hooks/` にカスタムフックを作成

3\. `page.tsx` または親コンポーネントからインポート



詳細: \[フロントエンドガイド - コンポーネント開発](./docs/architecture/FRONTEND.md#コンポーネント開発)



\### 新しいAPIエンドポイントを追加



1\. `backend/file\_main.py` にエンドポイント関数を追加

2\. フロントエンドから `useFileBrowser` または新しいカスタムフックで呼び出し



詳細: \[バックエンドガイド - API開発](./docs/architecture/BACKEND.md#api開発)



\### 新しいツールを追加



1\. `backend/deepagents\_cli/tools.py` にツール関数を追加

2\. `create\_deep\_agent()` の `tools` 引数に追加



詳細: \[バックエンドガイド - ツール開発](./docs/architecture/BACKEND.md#ツール開発)



\### 新しいスキルを作成



1\. `agent\_config/.deepagents/agent/skills/` に新しいディレクトリを作成

2\. `SKILL.md` ファイルを作成してYAMLフロントマターと説明を記述

3\. 再起動すると自動的にロードされる



詳細: \[バックエンドガイド - スキル開発](./docs/architecture/BACKEND.md#スキル開発)



\### ミドルウェアを追加



1\. `backend/deepagents\_cli/` に新しいミドルウェアファイルを作成

2\. `backend\_agent\_main.py` の `create\_deep\_agent()` に追加



詳細: \[バックエンドガイド - ミドルウェア開発](./docs/architecture/BACKEND.md#ミドルウェア開発)



\## トラブルシューティング



\### フロントエンドがバックエンドに接続できない



\- `frontend/src/app/page.tsx:25-35` でデプロイメントURL設定を確認

\- CORSが正しく設定されているか `backend/file\_api/config.py` で確認

\- ネットワークタブでリクエストURLを確認



\### エージェントが応答しない



\- LangGraphサーバーが起動しているか確認: `docker compose logs backend`

\- 環境変数 `GOOGLE\_APPLICATION\_CREDENTIALS` が正しく設定されているか確認

\- `backend/langgraph.json` のグラフ定義が正しいか確認



\### ファイル変更が反映されない



\- ファイルウォッチャーが起動しているか確認: `backend/file\_main.py:108-115`

\- WebSocket接続が確立されているか確認: ブラウザのネットワークタブ

\- `WATCH\_DIR` 環境変数が正しいか確認



\### Docker ビルドが失敗する



\- マルチステージビルドの各ステージを確認: `Dockerfile:1-50`

\- ビルドコンテキストに必要なファイルがあるか確認

\- `.dockerignore` が重要なファイルを除外していないか確認



\## さらに詳しく



\- \*\*\[フロントエンドガイド](./docs/architecture/FRONTEND.md)\*\* - コンポーネント、フック、状態管理の詳細

\- \*\*\[バックエンドガイド](./docs/architecture/BACKEND.md)\*\* - エージェント、API、ミドルウェアの実装詳細

\- \*\*\[デプロイメントガイド](./docs/architecture/DEPLOYMENT.md)\*\* - Docker、環境変数、Cloud Runデプロイ



\## 参考リンク



\- \[Next.js ドキュメント](https://nextjs.org/docs)

\- \[LangGraph ドキュメント](https://langchain-ai.github.io/langgraph/)

\- \[FastAPI ドキュメント](https://fastapi.tiangolo.com/)

\- \[Tailwind CSS ドキュメント](https://tailwindcss.com/docs)

\- \[Radix UI ドキュメント](https://www.radix-ui.com/)

