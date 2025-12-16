#!/usr/bin/env bash

# 1. 所有者をryoyamamuraに変更
sudo chown -R ryoyamamura:ryoyamamura /home/ryoyamamura/dev-cli-agent

# 2. 適切なアクセス権を設定（ディレクトリには実行権限、ファイルには読み書き権限）
chmod -R u+rwX /home/ryoyamamura/dev-cli-agent