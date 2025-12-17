## ローカル開発

docker compose up -d
docker compose down

関連Dockerfile
Dockerfile.dev

環境変数
frontend: ./frontend/.env.development
backend: ./backend/.env


## ローカルビルドとテスト
bash deploy_local.sh

関連Dockerfile
Dockerfile

環境変数
.env.local

## クラウドへのデプロイ
bash deploy.sh

関連Dockerfile
Dockerfile

環境変数
.env.yaml