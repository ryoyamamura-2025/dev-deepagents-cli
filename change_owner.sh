#!/usr/bin/env bash

# 1. 所有者をkyoryoに変更
sudo chown -R kyoryo:kyoryo /home/kyoryo/workspace/dev-deepagents-cli

# 2. 適切なアクセス権を設定（ディレクトリには実行権限、ファイルには読み書き権限）
chmod -R u+rwX /home/kyoryo/workspace/dev-deepagents-cli