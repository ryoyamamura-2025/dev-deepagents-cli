# ファイルブラウザ機能拡張ガイド

## 📝 概要

このドキュメントでは、Deep Agents UIのファイルブラウザに追加された新機能について説明します。

**実装日:** 2025-12-16
**コミット:** `feat: フロントエンドファイルブラウザの機能拡張`

---

## 🎯 実装した機能

### 1. ファイルの編集と保存機能
### 2. .txt/.mdファイルのプレビュー見た目修正
### 3. PDF・画像のプレビュー機能
### 4. ファイルアップロード・削除機能

---

## 📦 1. ファイルの編集と保存機能

### 概要
ファイルブラウザから直接ファイルを編集し、保存できる機能を実装しました。

### バックエンドAPI

#### `PUT /api/files/{file_path}`
ファイル内容を更新するエンドポイント

**リクエスト:**
```json
{
  "content": "ファイルの新しい内容"
}
```

**レスポンス:**
```json
{
  "success": true,
  "message": "File updated successfully",
  "path": "相対パス"
}
```

**実装箇所:** `file_api/main.py:191-234`

```python
@app.put("/api/files/{file_path:path}")
async def update_file(file_path: str, request: FileUpdateRequest):
    """ファイル内容を更新"""
    target_file = sanitize_path(file_path, WATCH_DIR)
    target_file.write_text(request.content, encoding="utf-8")
    return {"success": True, "message": "File updated successfully"}
```

### フロントエンド実装

#### `useFileBrowser.ts`
```typescript
const updateFile = useCallback(async (filePath: string, content: string) => {
  const response = await fetch(`${FILE_API_URL}/api/files/${filePath}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!response.ok) throw new Error('Failed to update file');
  await mutate(); // ファイル一覧を再取得
}, [mutate]);
```

#### `FileBrowser.tsx`
```typescript
const handleSaveFile = async (fileName: string, content: string) => {
  await updateFile(fileName, content);
  // 選択中のファイル内容を更新
  if (selectedFile) {
    setSelectedFile({ ...selectedFile, content });
  }
};
```

### 使い方
1. ファイルをクリックしてプレビューダイアログを開く
2. 「Edit」ボタンをクリック
3. テキストエリアでファイルを編集
4. 「Save」ボタンで保存
5. WebSocketでリアルタイムにファイル一覧が更新される

---

## 🎨 2. .txt/.mdファイルのプレビュー見た目修正

### 概要
テキストファイルとMarkdownファイルが適切にフォーマットされて表示されるように修正しました。

### 修正前の問題
- すべてのファイルがコードブロック（シンタックスハイライト）で表示されていた
- `.txt`ファイルの可読性が低かった
- `.md`ファイルがMarkdownとしてレンダリングされていなかった

### 修正後
- `.txt`, `.log`, `.env`などのプレーンテキストファイル → 通常のテキスト表示
- `.md`ファイル → Markdownレンダリング
- コードファイル（`.py`, `.js`, `.ts`など） → シンタックスハイライト

### 実装詳細

#### `FileViewDialog.tsx`
```typescript
// ファイルタイプの判定
const isMarkdown = useMemo(() => {
  return fileExtension === "md" || fileExtension === "markdown";
}, [fileExtension]);

const isPlainText = useMemo(() => {
  return ["txt", "log", "env", "gitignore", ""].includes(fileExtension);
}, [fileExtension]);

// 表示の切り替え
{isMarkdown ? (
  <MarkdownContent content={fileContent} />
) : isPlainText ? (
  <pre className="whitespace-pre-wrap break-words font-mono text-sm">
    {fileContent}
  </pre>
) : (
  <SyntaxHighlighter language={language} style={oneDark}>
    {fileContent}
  </SyntaxHighlighter>
)}
```

### 対応ファイル拡張子

| タイプ | 拡張子 | 表示形式 |
|--------|--------|----------|
| Markdown | `.md`, `.markdown` | Markdownレンダリング |
| プレーンテキスト | `.txt`, `.log`, `.env`, `.gitignore` | 通常テキスト |
| コードファイル | `.py`, `.js`, `.ts`, `.jsx`, `.tsx`, `.json`など | シンタックスハイライト |

---

## 🖼️ 3. PDF・画像のプレビュー機能

### 概要
画像ファイルとPDFファイルをブラウザ内でプレビュー表示できるようになりました。

### バックエンドAPI

#### `GET /api/files/{file_path}?raw=true`
バイナリファイルを直接配信するパラメータを追加

**パラメータ:**
- `raw=false` (デフォルト): テキストファイルとしてJSON形式で返す
- `raw=true`: バイナリファイルとして直接配信（Content-Type自動設定）

**実装箇所:** `file_api/main.py:129-203`

```python
@app.get("/api/files/{file_path:path}")
async def read_file(file_path: str, raw: bool = False):
    """ファイル内容を取得"""
    target_file = sanitize_path(file_path, WATCH_DIR)

    if raw:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(target_file))
        return FileResponse(
            path=target_file,
            media_type=mime_type or "application/octet-stream",
            filename=target_file.name
        )

    # テキストファイルとして読み取り
    content = target_file.read_text(encoding="utf-8")
    return {"success": True, "content": content, ...}
```

### フロントエンド実装

#### `FileViewDialog.tsx`
```typescript
// ファイルタイプの判定
const isImage = useMemo(() => {
  return ["png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico"].includes(fileExtension);
}, [fileExtension]);

const isPdf = useMemo(() => {
  return fileExtension === "pdf";
}, [fileExtension]);

// ファイルURLの生成
const fileUrl = useMemo(() => {
  if (!file?.path) return "";
  const FILE_API_URL = process.env.NEXT_PUBLIC_FILE_API_URL || 'http://localhost:8124';
  return `${FILE_API_URL}/api/files/${file.path}?raw=true`;
}, [file?.path]);

// プレビュー表示
{isImage ? (
  <img
    src={fileUrl}
    alt={fileName}
    className="max-h-[600px] max-w-full object-contain"
  />
) : isPdf ? (
  <iframe
    src={fileUrl}
    className="h-[600px] w-full rounded-md"
    title={fileName}
  />
) : (
  // テキストファイルの表示
)}
```

#### `FileBrowser.tsx`
バイナリファイルの場合は内容を読み込まずにプレビュー

```typescript
const handleFileClick = async (item: FileSystemItem) => {
  const extension = item.extension?.toLowerCase() || "";
  const isBinaryFile = ["png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico", "pdf"].includes(extension);

  if (isBinaryFile) {
    // バイナリファイルは内容を空にする
    setSelectedFile({
      path: item.path,
      content: "",
      name: item.name,
    });
  } else {
    // テキストファイルは内容を読み込む
    const fileData = await readFile(item.path);
    setSelectedFile({
      path: item.path,
      content: fileData.content,
      name: item.name,
    });
  }
};
```

### 対応ファイル形式

#### 画像
- `.png` - PNG画像
- `.jpg`, `.jpeg` - JPEG画像
- `.gif` - GIFアニメーション
- `.svg` - SVGベクター画像
- `.webp` - WebP画像
- `.bmp` - ビットマップ画像
- `.ico` - アイコンファイル

#### PDF
- `.pdf` - PDFドキュメント

### UI/UX改善
- 画像・PDFファイルでは「Edit」と「Copy」ボタンを非表示
- 「Download」ボタンは表示（ダウンロード可能）
- 画像は最大600px高さで表示、アスペクト比維持
- PDFは600px高さのiframeで表示

---

## 📤 4. ファイルアップロード・削除機能

### 概要
ブラウザから直接ファイルをアップロード・削除できる機能を実装しました。

### 4-1. ファイルアップロード

#### バックエンドAPI

**エンドポイント:** `POST /api/files/upload`

**リクエスト:**
- `files`: ファイルのリスト（multipart/form-data）
- `path`: アップロード先の相対パス（オプション）

**レスポンス:**
```json
{
  "success": true,
  "message": "Uploaded 2 file(s)",
  "uploaded_files": ["path/to/file1.txt", "path/to/file2.jpg"]
}
```

**実装箇所:** `file_api/main.py:278-332`

```python
@app.post("/api/files/upload")
async def upload_files(
    files: List[UploadFile],
    path: str = Form("")
):
    """ファイルをアップロード"""
    target_dir = sanitize_path(path, WATCH_DIR)
    uploaded_files = []

    for file in files:
        if not file.filename:
            continue

        # ファイル名をサニタイズ（パストラバーサル防止）
        safe_filename = Path(file.filename).name
        target_file = target_dir / safe_filename

        # ファイルを保存
        content = await file.read()
        target_file.write_bytes(content)

        uploaded_files.append(str(target_file.relative_to(WATCH_DIR)))

    return {"success": True, "uploaded_files": uploaded_files}
```

#### フロントエンド実装

**`useFileBrowser.ts`**
```typescript
const uploadFiles = useCallback(async (files: File[], targetPath: string = "") => {
  const formData = new FormData();
  files.forEach(file => {
    formData.append('files', file);
  });
  formData.append('path', targetPath);

  const response = await fetch(`${FILE_API_URL}/api/files/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) throw new Error('Failed to upload files');
  await mutate(); // ファイル一覧を再取得
}, [mutate]);
```

**`FileBrowser.tsx`**
```typescript
// ヘッダーにアップロードボタンを追加
<Button
  variant="ghost"
  size="icon"
  onClick={handleUploadClick}
  title="ファイルをアップロード"
>
  <Upload className="h-4 w-4" />
</Button>

// 非表示のfile input
<input
  ref={fileInputRef}
  type="file"
  multiple
  className="hidden"
  onChange={handleFileInputChange}
/>
```

#### 使い方
1. ファイルブラウザのヘッダーにある「アップロード」ボタンをクリック
2. ファイル選択ダイアログが表示される
3. アップロードしたいファイルを選択（複数選択可能）
4. 現在のディレクトリにファイルがアップロードされる
5. WebSocketでリアルタイムにファイル一覧が更新される

### 4-2. ファイル削除

#### バックエンドAPI

**エンドポイント:** `DELETE /api/files/{file_path}`

**レスポンス:**
```json
{
  "success": true,
  "message": "File deleted successfully",
  "path": "相対パス"
}
```

**実装箇所:** `file_api/main.py:237-275`

```python
@app.delete("/api/files/{file_path:path}")
async def delete_file(file_path: str):
    """ファイルまたはディレクトリを削除"""
    target_path = sanitize_path(file_path, WATCH_DIR)

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="File or directory not found")

    # ディレクトリの場合は再帰的に削除
    if target_path.is_dir():
        import shutil
        shutil.rmtree(target_path)
    else:
        target_path.unlink()

    return {"success": True, "message": "File deleted successfully"}
```

#### フロントエンド実装

**`useFileBrowser.ts`**
```typescript
const deleteFile = useCallback(async (filePath: string) => {
  const response = await fetch(`${FILE_API_URL}/api/files/${filePath}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete file');
  await mutate(); // ファイル一覧を再取得
}, [mutate]);
```

**`FileSystemList.tsx`**
```typescript
// 各ファイル/フォルダに削除ボタンを追加（ホバー時表示）
{onDeleteClick && (
  <Button
    variant="ghost"
    size="icon"
    className="h-8 w-8 opacity-0 transition-opacity group-hover:opacity-100"
    onClick={(e) => {
      e.stopPropagation();
      if (confirm(`「${item.name}」を削除してもよろしいですか？`)) {
        onDeleteClick(item);
      }
    }}
    title="削除"
  >
    <Trash2 className="h-4 w-4 text-destructive" />
  </Button>
)}
```

#### 使い方
1. ファイルまたはフォルダにマウスをホバー
2. 右側に表示される「ゴミ箱」アイコンをクリック
3. 確認ダイアログが表示される
4. 「OK」をクリックするとファイル/フォルダが削除される
5. WebSocketでリアルタイムにファイル一覧が更新される

#### セキュリティ対策
- パストラバーサル攻撃の防止（`sanitize_path`関数）
- 削除前の確認ダイアログ
- ディレクトリ削除時は再帰的に削除（警告付き）

---

## 🔄 リアルタイム更新

すべてのファイル操作（作成、編集、削除、アップロード）は、WebSocketを通じて他のクライアントにリアルタイムで通知されます。

### 動作フロー

```
1. ユーザーがファイルを操作（編集/削除/アップロード）
   ↓
2. バックエンドAPIがファイルシステムを更新
   ↓
3. watchdogがファイル変更を検知
   ↓
4. WebSocketで全クライアントに通知
   ↓
5. フロントエンドが自動でファイル一覧を再取得
   ↓
6. 画面が自動更新される
```

---

## 📂 変更ファイル一覧

### バックエンド
- `file_api/main.py` - API拡張
  - `PUT /api/files/{path}` - ファイル更新
  - `DELETE /api/files/{path}` - ファイル削除
  - `POST /api/files/upload` - ファイルアップロード
  - `GET /api/files/{path}?raw=true` - バイナリファイル配信

### フロントエンド
- `deep-agents-ui/src/app/hooks/useFileBrowser.ts` - データ管理の拡張
  - `updateFile()` - ファイル更新
  - `deleteFile()` - ファイル削除
  - `uploadFiles()` - ファイルアップロード

- `deep-agents-ui/src/app/components/FileBrowser.tsx` - メインUI更新
  - アップロードボタンの追加
  - ファイル保存処理の実装
  - バイナリファイルのハンドリング

- `deep-agents-ui/src/app/components/FileSystemList.tsx` - ファイル一覧
  - 削除ボタンの追加（ホバー時表示）
  - 確認ダイアログの実装

- `deep-agents-ui/src/app/components/FileViewDialog.tsx` - プレビュー
  - プレーンテキスト表示の追加
  - 画像プレビューの実装
  - PDFプレビューの実装
  - 編集・保存機能の有効化

### ドキュメント
- `docs/ui_todo.md` - タスクリスト（新規作成）
- `docs/file-browser-features.md` - 本ドキュメント（新規作成）

---

## 🧪 テスト方法

### 1. ファイル編集・保存のテスト
```bash
# 1. ファイルブラウザで任意のテキストファイルをクリック
# 2. Editボタンをクリック
# 3. 内容を変更してSaveボタンをクリック
# 4. ファイルが更新されることを確認
```

### 2. プレビュー表示のテスト
```bash
# .txtファイル: プレーンテキスト表示を確認
# .mdファイル: Markdownレンダリングを確認
# .pyファイル: シンタックスハイライトを確認
# .pngファイル: 画像プレビューを確認
# .pdfファイル: PDFプレビューを確認
```

### 3. アップロードのテスト
```bash
# 1. Uploadボタンをクリック
# 2. 任意のファイルを選択
# 3. ファイルが現在のディレクトリにアップロードされることを確認
# 4. ファイル一覧が自動更新されることを確認
```

### 4. 削除のテスト
```bash
# 1. 任意のファイルにマウスをホバー
# 2. ゴミ箱アイコンをクリック
# 3. 確認ダイアログで「OK」をクリック
# 4. ファイルが削除され、ファイル一覧が自動更新されることを確認
```

---

## 🚀 今後の改善案

### 1. エラーハンドリングの改善
- トースト通知の実装（現在はconsole.errorのみ）
- エラーメッセージの日本語化

### 2. ファイル操作の拡張
- ファイル・フォルダのリネーム機能
- ファイル・フォルダのコピー・移動機能
- 新規フォルダ作成機能
- ドラッグ&ドロップでのアップロード

### 3. プレビュー機能の拡張
- コードエディタの統合（Monaco Editorなど）
- 画像のズーム機能
- PDFページナビゲーション
- 動画ファイルのプレビュー
- Officeファイル（.docx, .xlsx）のプレビュー

### 4. パフォーマンス改善
- 大きなファイルの遅延読み込み
- 画像のサムネイル生成
- ファイル一覧の仮想スクロール

### 5. その他
- ファイル検索機能
- お気に入り（ブックマーク）機能
- ファイルバージョン管理
- ゴミ箱機能（削除の取り消し）

---

## 📚 参考資料

### 関連ドキュメント
- [フロントエンド実装ガイド](./frontend-implementation-guide.md) - ファイルブラウザの基本機能
- [プロジェクト計画](./project_plan.md) - プロジェクト全体の計画
- [UI Todo](./ui_todo.md) - 実装タスクリスト

### 使用技術
- **バックエンド:** FastAPI, Python
- **フロントエンド:** Next.js, React, TypeScript
- **リアルタイム通信:** WebSocket, watchdog
- **データフェッチング:** SWR
- **UI:** Tailwind CSS, Radix UI

---

## ✅ まとめ

この実装により、Deep Agents UIのファイルブラウザは以下の機能を持つようになりました：

1. ✅ ファイルの編集と保存
2. ✅ 適切なファイルプレビュー（テキスト、Markdown、コード、画像、PDF）
3. ✅ ファイルのアップロード（複数ファイル対応）
4. ✅ ファイル・フォルダの削除
5. ✅ リアルタイム更新（WebSocket）
6. ✅ セキュリティ対策（パストラバーサル防止）

これにより、ユーザーはブラウザから直接ファイル管理ができるようになり、エージェントが作成したファイルをリアルタイムで確認・編集できるようになりました。