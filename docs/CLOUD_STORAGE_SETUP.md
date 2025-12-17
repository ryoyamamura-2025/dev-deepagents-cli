# Cloud Storage セットアップガイド

このガイドでは、`agent_config` ディレクトリを Google Cloud Storage から動的に取得するための設定方法を説明します。

## 概要

アプリケーションは起動時に以下の順序で `agent_config` を取得します:

1. **Cloud Storage からダウンロード** (設定されている場合)
2. **ローカルフォールバック** (Cloud Storage が利用できない場合)
3. **既存のディレクトリを使用** (既に存在する場合)

これにより、ローカル開発と Cloud Run デプロイの両方で柔軟に対応できます。

## セットアップ手順

### 1. Cloud Storage バケットの作成

```bash
# バケットを作成
gsutil mb -p your-project-id -l us-central1 gs://your-bucket-name

# または gcloud コマンドで
gcloud storage buckets create gs://your-bucket-name \
  --project=your-project-id \
  --location=us-central1
```

### 2. agent_config のアップロード

プロジェクトルートから以下のコマンドを実行:

```bash
# 依存関係をインストール
cd backend
uv sync

# agent_config をアップロード
uv run python ../scripts/upload_agent_config.py \
  --bucket your-bucket-name \
  --source ../agent_config \
  --prefix agent_config
```

**オプション:**
- `--bucket`: Cloud Storage のバケット名 (必須)
- `--source`: アップロード元のディレクトリパス (デフォルト: `./agent_config`)
- `--prefix`: Cloud Storage 内のパスプレフィックス (デフォルト: `agent_config`)

### 3. 環境変数の設定

`.env.yaml` を編集して、バケット名を設定:

```yaml
# for Cloud Storage agent_config
GCS_AGENT_CONFIG_BUCKET: "your-bucket-name"  # ← コメントを外してバケット名を設定
GCS_AGENT_CONFIG_PREFIX: "agent_config"
AGENT_CONFIG_DEST_DIR: "/root"
AGENT_CONFIG_FALLBACK_DIR: "./agent_config"
```

## 環境変数の詳細

| 環境変数 | 説明 | デフォルト値 |
|---------|------|-------------|
| `GCS_AGENT_CONFIG_BUCKET` | Cloud Storage のバケット名。設定すると起動時にダウンロードを試みます | なし (設定しない場合はローカルフォールバックを使用) |
| `GCS_AGENT_CONFIG_PREFIX` | Cloud Storage 内のパスプレフィックス | `agent_config` |
| `AGENT_CONFIG_DEST_DIR` | ダウンロード先のディレクトリ | `/root` |
| `AGENT_CONFIG_FALLBACK_DIR` | ローカルフォールバックディレクトリ | `./agent_config` |

## 動作モード

### Cloud Run デプロイ時

Cloud Run にデプロイする場合、以下の設定を推奨:

1. `.env.yaml` で `GCS_AGENT_CONFIG_BUCKET` を設定
2. Cloud Run サービスに適切な IAM 権限を付与:

```bash
# Cloud Run サービスアカウントに Storage Object Viewer ロールを付与
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:your-service-account@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

### ローカル開発時

ローカル開発では以下の2つの方法があります:

#### オプション1: Cloud Storage を使用

```bash
# gcloud で認証
gcloud auth application-default login

# .env.yaml で GCS_AGENT_CONFIG_BUCKET を設定
# アプリケーション起動時に Cloud Storage からダウンロード
```

#### オプション2: ローカルフォールバックを使用

```bash
# .env.yaml で GCS_AGENT_CONFIG_BUCKET をコメントアウト
# アプリケーションは ./agent_config を使用
```

## トラブルシューティング

### Cloud Storage からダウンロードできない

1. **IAM 権限を確認:**
   ```bash
   gcloud projects get-iam-policy your-project-id \
     --flatten="bindings[].members" \
     --format="table(bindings.role)" \
     --filter="bindings.members:your-service-account@your-project-id.iam.gserviceaccount.com"
   ```

2. **バケットが存在するか確認:**
   ```bash
   gsutil ls gs://your-bucket-name
   ```

3. **ログを確認:**
   ```bash
   # Cloud Run のログ
   gcloud run services logs read your-service-name --region us-central1
   ```

### ローカルでの認証エラー

```bash
# Application Default Credentials を再設定
gcloud auth application-default login

# または特定のプロジェクトを設定
gcloud config set project your-project-id
```

## agent_config の更新

Cloud Storage 上の `agent_config` を更新する場合:

```bash
# 既存のファイルを削除 (オプション)
gsutil -m rm -r gs://your-bucket-name/agent_config/

# 新しいバージョンをアップロード
cd backend
uv run python ../scripts/upload_agent_config.py \
  --bucket your-bucket-name \
  --source ../agent_config

# Cloud Run を再デプロイ (新しい設定を読み込むため)
./deploy.sh
```

## セキュリティのベストプラクティス

1. **最小権限の原則:** Cloud Run サービスアカウントには `Storage Object Viewer` ロールのみを付与
2. **バケットの公開アクセスを無効化:**
   ```bash
   gsutil iam ch -d allUsers:objectViewer gs://your-bucket-name
   ```
3. **バージョニングを有効化:**
   ```bash
   gsutil versioning set on gs://your-bucket-name
   ```

## 参考リンク

- [Cloud Storage ドキュメント](https://cloud.google.com/storage/docs)
- [Cloud Run IAM](https://cloud.google.com/run/docs/securing/service-identity)
- [Google Cloud Python クライアント](https://cloud.google.com/python/docs/reference/storage/latest)
