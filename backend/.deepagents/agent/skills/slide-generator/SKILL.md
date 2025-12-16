---
name: slide-generator
description: Gemini API（Nano Banana Pro）でスライド資料を生成。スライドの形式、長さ、言語をオプションで選択可能。
---

# 画像生成Skill

Vertex AI Gemini API（Nano Banana Pro）を使用したスライド資料生成

## 役割

このSkillは議事録、文字起こし、メモ、その他の入力データを元に一貫性のあるデザインでスライド資料を作成します。

## ワークフロー

1. **出力パスの設定**: Pythonスクリプトを実行し、入力情報及びスライド画像の保存先ディレクトリを作成
- `uv run python {SKILL_DIR}/scripts/setup_environment.py`を実行する。
- `{WORKING_DIR}/flow/slide-generator/{datetime}`が作成されます。

2. **入力情報の作成**: 
- `touch {WORKING_DIR}/flow/slide-generator/{datetime}/content.md`を実行
- `{WORKING_DIR}/resource`内の全てのテキストデータ(.md, .txt等)を転記するスクリプトを実行

Example
```bash
for file in {WORKING_DIR}/resource/*.txt {WORKING_DIR}/resource/*.md; do
    [ -f "$file" ] && {
        echo "--- Start of $file ---" >> {WORKING_DIR}/flow/slide-generator/{datetime}/content.md
        cat "$file" >> {WORKING_DIR}/flow/slide-generator/{datetime}/content.md
    }
done
```

3. **スライド形式、長さ、言語の設定**: もしユーザーから指定されていない場合、以下の表を提示し、選択を促す。指定されている場合はスキップする。

| 引数 | 必須 | 説明 |
|------|------|------|
| `--style STYLE` | No | スライドの形式。`detail`（詳細かつ包括的）または`presentor`（ポイント・ビジュアル重視）から選択。デフォルトは`detail` |
| `--length LENGTH` | No | スライドの枚数。`1`, `3`, `5~`から選択。デフォルトは`5~`。|
| `--lang LANGUAGE` | No | 言語。`jp`,`en`から選択デフォルトは`jp` |

**注意**: オプション外の選択肢は不可

4. **スライド生成の実行**: 
生成スクリプトの実行
```bash
uv run python {SKILL_DIR}/scripts/slide_generator.py OUTPUT_DIR [--style STYLE] [--length LENGTH] [--lang LANGUAGE]
```
**注意**: エラーが出てもスクリプトを勝手に変更しないこと！

## 留意事項
Pythonスクリプトの実行は**必ずuvを使う**こと 
### Example: 
- GOOD `uv run python script.py ...`
- BAD `python script.py ...`

## 制限事項

- APIレート制限あり
- スクリプトの変更禁止

## トラブルシューティング

| 問題 | 解決策 |
|------|--------|
| 生成失敗 | 少し待って再実行 |
| レート制限 | 少し待って再実行 |
