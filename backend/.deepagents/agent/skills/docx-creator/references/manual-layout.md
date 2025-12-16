# マニュアル作成のページレイアウト ベストプラクティス

このガイドは、マニュアル作成時に適用すべきページレイアウトのベストプラクティスを説明します。

## 基本構造

マニュアルは以下の構造で構成します：

1. **タイトルページ** - マニュアルタイトルと概要
2. **目次** - セクション一覧（TableOfContentsを使用）
3. **本文** - セクションとコンテンツ行
4. **ページ番号** - フッターに表示

## ページ設定

```javascript
sections: [{
  properties: {
    page: {
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }, // 1インチの余白
      pageNumbers: { start: 1, formatType: "decimal" }
    }
  },
  footers: {
    default: new Footer({
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun("Page "),
            new TextRun({ children: [PageNumber.CURRENT] }),
            new TextRun(" of "),
            new TextRun({ children: [PageNumber.TOTAL_PAGES] })
          ]
        })
      ]
    })
  }
}]
```

## タイトルページ

マニュアルのタイトルページは以下の要素を含めます：

- **タイトル**: 大きなフォントサイズ（56pt）、中央揃え、太字
- **概要**: タイトルの下に配置、通常の本文サイズ（24pt）、適切なスペーシング

```javascript
// タイトル
new Paragraph({
  heading: HeadingLevel.TITLE,
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 400 },
  children: [new TextRun({ text: manualTitle, bold: true, size: 56 })]
}),

// 概要（abstract）
new Paragraph({
  alignment: AlignmentType.LEFT,
  spacing: { before: 200, after: 600 },
  indent: { left: 720, right: 720 },
  children: [new TextRun({ text: manualAbstract, size: 24 })]
}),

// ページ区切り
new Paragraph({ children: [new PageBreak()] })
```

## 目次

目次はタイトルページの後に配置します：

```javascript
new TableOfContents("目次", {
  hyperlink: true,
  headingStyleRange: "1-3" // H1からH3までを含める
}),
new Paragraph({ children: [new PageBreak()] })
```

## セクション構造

各セクションは以下の構造で作成します：

### セクションタイトル

```javascript
new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 400, after: 300 },
  pageBreakBefore: false, // 通常は改ページしない
  children: [new TextRun({ text: sectionTitle, bold: true, size: 32 })]
})
```

### コンテンツ行（Rows）

各コンテンツ行は以下の要素を含めます：

1. **タイムスタンプと見出し** - 行の開始を示す
2. **タグ** - Check、Analysis、Conclusionなどの視覚的な区別
3. **メインコンテンツ** - 説明文
4. **箇条書き** - 詳細なポイント
5. **スクリーンショット** - 必要に応じて

#### タイムスタンプと見出し

```javascript
new Paragraph({
  spacing: { before: 200, after: 100 },
  children: [
    new TextRun({ 
      text: `[${timestampStart}] `, 
      color: "666666", 
      size: 20,
      italics: true 
    }),
    new TextRun({ 
      text: heading, 
      bold: true, 
      size: 26 
    })
  ]
})
```

#### タグの視覚的表示

タグは見出しの後に配置し、色分けや背景色で区別します：

```javascript
// タグの背景色マッピング
const tagColors = {
  "Check": { fill: "E3F2FD", text: "確認" },      // 薄い青
  "Analysis": { fill: "FFF3E0", text: "解析" },    // 薄いオレンジ
  "Conclusion": { fill: "E8F5E9", text: "結論" }, // 薄い緑
  "Warning": { fill: "FFEBEE", text: "警告" },     // 薄い赤
  "Info": { fill: "F3E5F5", text: "情報" }        // 薄い紫
};

// タグ表示（インライン）
new Paragraph({
  spacing: { before: 0, after: 100 },
  children: [
    new TextRun({ 
      text: tagColors[tag]?.text || tag, 
      bold: true,
      size: 20,
      color: "000000",
      shading: { fill: tagColors[tag]?.fill || "F5F5F5", type: ShadingType.CLEAR }
    })
  ]
})
```

または、テーブルセルを使用してより目立つタグ表示：

```javascript
new Table({
  columnWidths: [2000, 7360],
  rows: [
    new TableRow({
      children: [
        new TableCell({
          width: { size: 2000, type: WidthType.DXA },
          shading: { fill: tagColors[tag]?.fill || "F5F5F5", type: ShadingType.CLEAR },
          verticalAlign: VerticalAlign.CENTER,
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({ 
                  text: tagColors[tag]?.text || tag, 
                  bold: true,
                  size: 20
                })
              ]
            })
          ]
        }),
        new TableCell({
          width: { size: 7360, type: WidthType.DXA },
          children: [/* メインコンテンツ */]
        })
      ]
    })
  ]
})
```

#### メインコンテンツ

```javascript
new Paragraph({
  spacing: { before: 100, after: 100 },
  children: [new TextRun({ text: mainText, size: 24 })]
})
```

#### 箇条書き

```javascript
// 箇条書きの設定
numbering: {
  config: [{
    reference: "manual-bullets",
    levels: [{
      level: 0,
      format: LevelFormat.BULLET,
      text: "•",
      alignment: AlignmentType.LEFT,
      style: {
        paragraph: { indent: { left: 720, hanging: 360 } }
      }
    }]
  }]
}

// 箇条書きの使用
bulletPoints.forEach(point => {
  new Paragraph({
    numbering: { reference: "manual-bullets", level: 0 },
    spacing: { before: 50, after: 50 },
    children: [new TextRun({ text: point, size: 22 })]
  })
})
```

#### スクリーンショット

スクリーンショットは中央揃えで配置し、キャプションを追加します：

```javascript
// スクリーンショット画像
new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 200, after: 100 },
  children: [
    new ImageRun({
      type: "png", // または "jpg", "jpeg" など
      data: fs.readFileSync(screenshotPath),
      transformation: { 
        width: 600,  // 適切なサイズに調整
        height: 400,
        rotation: 0 
      },
      altText: {
        title: "スクリーンショット",
        description: caption,
        name: "Screenshot"
      }
    })
  ]
}),

// キャプション
new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 0, after: 200 },
  children: [
    new TextRun({ 
      text: caption, 
      size: 20, 
      color: "666666",
      italics: true 
    })
  ]
})
```

## セクション間の区切り

セクション間には適切なスペーシングを設けます：

```javascript
// セクション終了後のスペーシング
new Paragraph({
  spacing: { before: 0, after: 400 },
  children: [] // 空のパラグラフでスペースを確保
})
```

## スタイル設定

マニュアル全体で一貫したスタイルを適用します：

```javascript
styles: {
  default: {
    document: {
      run: { font: "Arial", size: 24 } // 12pt デフォルト
    }
  },
  paragraphStyles: [
    {
      id: "Title",
      name: "Title",
      basedOn: "Normal",
      run: { size: 56, bold: true, color: "000000", font: "Arial" },
      paragraph: {
        spacing: { before: 240, after: 120 },
        alignment: AlignmentType.CENTER
      }
    },
    {
      id: "Heading1",
      name: "Heading 1",
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { size: 32, bold: true, color: "000000", font: "Arial" },
      paragraph: {
        spacing: { before: 400, after: 300 },
        outlineLevel: 0
      }
    },
    {
      id: "Heading2",
      name: "Heading 2",
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { size: 28, bold: true, color: "000000", font: "Arial" },
      paragraph: {
        spacing: { before: 200, after: 200 },
        outlineLevel: 1
      }
    }
  ]
}
```

## 重要な原則

1. **一貫性**: 同じレベルの要素には同じスタイルを適用
2. **可読性**: 適切な余白とスペーシングを確保
3. **視覚的階層**: タイトル > 見出し > 本文の明確な階層
4. **タグの視覚的区別**: 色分けや背景色でタグを明確に区別
5. **スクリーンショットの配置**: 関連する説明の近くに配置し、キャプションを追加
6. **ページ番号**: すべてのページにページ番号を表示
7. **目次**: 長いマニュアルには必ず目次を含める

## 実装例の構造

```javascript
const doc = new Document({
  styles: { /* 上記のスタイル設定 */ },
  numbering: { /* 箇条書き設定 */ },
  sections: [{
    properties: { /* ページ設定 */ },
    headers: { /* 必要に応じて */ },
    footers: { /* ページ番号 */ },
    children: [
      // 1. タイトルページ
      // 2. 目次
      // 3. 各セクション
      sections.forEach(section => {
        // セクションタイトル
        section.rows.forEach(row => {
          // タイムスタンプと見出し
          // タグ
          // メインコンテンツ
          // 箇条書き
          // スクリーンショット
        })
      })
    ]
  }]
})
```
