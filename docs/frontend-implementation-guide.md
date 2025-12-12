# フロントエンド実装ガイド：ファイルブラウザ機能

## 📋 目次
1. [何を追加したのか](#何を追加したのか)
2. [画面の変更点](#画面の変更点)
3. [追加したファイルの説明](#追加したファイルの説明)
4. [データの流れ](#データの流れ)
5. [使用している技術の説明](#使用している技術の説明)
6. [実装の詳細](#実装の詳細)

---

## 何を追加したのか

Deep Agents UIに**ファイルブラウザ機能**を追加しました。これにより、エージェントが作成・編集したファイルをリアルタイムで確認できるようになります。

### 主な機能
- ✅ ファイルとフォルダの一覧表示
- ✅ フォルダの階層移動（クリックで深い階層へ移動可能）
- ✅ ファイルのプレビュー（クリックで内容を確認）
- ✅ リアルタイム更新（エージェントがファイルを変更すると自動で反映）
- ✅ パンくずナビゲーション（現在の場所を表示）

---

## 画面の変更点

### Before（変更前）
```
┌──────────────────────────────────────────┐
│  Header                                   │
├───────────┬──────────────────────────────┤
│  Threads  │  Chat                        │
│  List     │  Interface                   │
│           │                              │
│           │                              │
└───────────┴──────────────────────────────┘
```

### After（変更後）
```
┌──────────────────────────────────────────────────────┐
│  Header  [Threads] [Files] [Settings] [New Thread]  │
├───────────┬──────────────┬──────────────────────────┤
│  Threads  │  Files       │  Chat                    │
│  List     │  Browser     │  Interface               │
│           │              │                          │
│  (左側)   │  (中央)      │  (右側)                  │
└───────────┴──────────────┴──────────────────────────┘
```

**変更内容:**
1. **2カラム → 3カラム**に変更
2. 中央に**ファイルブラウザパネル**を追加
3. ヘッダーに**Filesトグルボタン**を追加（クリックでファイルパネルの表示/非表示を切り替え）

---

## 追加したファイルの説明

### 1. `useFileBrowser.ts` - データ管理の心臓部
**場所:** `deep-agents-ui/src/app/hooks/useFileBrowser.ts`

**役割:**
- FastAPIサーバーからファイル一覧を取得
- WebSocketでリアルタイム更新を監視
- ファイルの読み込み機能を提供

**わかりやすい例え:**
図書館の司書のような役割です。「この棚にある本のリストください」とお願いすると、リストを持ってきてくれます。また、新しい本が追加されたら自動で教えてくれます。

**主な機能:**
```typescript
// ファイル一覧の取得
items: FileSystemItem[]  // ファイルとフォルダのリスト

// フォルダ移動
navigateTo(path: string)  // 指定したフォルダに移動

// ファイル読み込み
readFile(filePath: string)  // ファイルの中身を読む

// リアルタイム更新の状態
wsConnected: boolean  // WebSocketが接続されているか
```

---

### 2. `FileBrowser.tsx` - ファイルブラウザのメイン画面
**場所:** `deep-agents-ui/src/app/components/FileBrowser.tsx`

**役割:**
- ファイルブラウザ全体のレイアウトを管理
- パンくずナビゲーション（現在地表示）を表示
- リフレッシュボタンと閉じるボタンを配置
- ファイルプレビューのダイアログを表示

**わかりやすい例え:**
WindowsのエクスプローラーやmacのFinderのような画面です。上部に現在の場所が表示され、ファイルとフォルダが一覧表示されます。

**画面構成:**
```
┌─────────────────────────────────────┐
│ Files  [🔄 Refresh] [❌ Close]     │  ← ヘッダー
├─────────────────────────────────────┤
│ 🏠 Home > folder1 > folder2         │  ← パンくずナビ
├─────────────────────────────────────┤
│ 📁 folder3                          │
│ 📄 file1.txt                        │  ← ファイル一覧
│ 📄 file2.py                         │
│ ...                                 │
└─────────────────────────────────────┘
```

---

### 3. `FileSystemList.tsx` - ファイル一覧の表示部分
**場所:** `deep-agents-ui/src/app/components/FileSystemList.tsx`

**役割:**
- ファイルとフォルダを1つずつ表示
- アイコンを付ける（フォルダ、テキストファイル、コードファイルなど）
- ファイルサイズと更新日時を表示
- クリック時の動作を処理

**わかりやすい例え:**
ファイルマネージャーの中の「1行分」を担当しています。各ファイルに適切なアイコンを付けて、情報を見やすく表示します。

**表示例:**
```
📁 documents/           2024-12-13 15:30
📄 readme.txt          1.2 KB    2024-12-13 14:20
🐍 script.py           3.4 KB    2024-12-13 13:10
```

---

### 4. `page.tsx` - レイアウトの変更
**場所:** `deep-agents-ui/src/app/page.tsx`

**変更内容:**
- 2カラムから3カラムレイアウトに変更
- FileBrowserパネルを追加
- Filesトグルボタンを追加

**変更箇所のイメージ:**
```typescript
// 追加したボタン
<Button onClick={() => setFileBrowserOpen("1")}>
  <FolderOpen /> Files
</Button>

// 追加したパネル
{fileBrowserOpen && (
  <ResizablePanel id="file-browser">
    <FileBrowser onClose={() => setFileBrowserOpen(null)} />
  </ResizablePanel>
)}
```

---

## データの流れ

### 1. ファイル一覧の取得
```
ユーザー操作
    ↓
FileBrowser コンポーネント
    ↓
useFileBrowser フック
    ↓
FastAPI サーバー (http://localhost:8124/api/files)
    ↓
ファイルシステム（/workspace/ディレクトリ）
    ↓
ファイル一覧を返す
    ↓
FileSystemList で表示
```

### 2. リアルタイム更新
```
エージェントがファイル作成/変更
    ↓
watchdog がファイル変更を検知
    ↓
FastAPI サーバーが WebSocket で通知
    ↓
useFileBrowser がメッセージを受信
    ↓
ファイル一覧を自動で再取得
    ↓
画面が自動更新される
```

### 3. ファイルプレビュー
```
ユーザーがファイルをクリック
    ↓
FileBrowser で readFile() を呼び出し
    ↓
FastAPI サーバー (http://localhost:8124/api/files/{filepath})
    ↓
ファイル内容を取得
    ↓
FileViewDialog で内容を表示
```

---

## 使用している技術の説明

### React Hooks（フック）
**説明:** Reactの機能を使うための「道具」のようなもの

- `useState`: 画面の状態を記憶する（例: 現在のフォルダパス）
- `useEffect`: 画面が表示された時に何かをする（例: WebSocketに接続）
- `useCallback`: 関数を記憶して再利用する（パフォーマンス向上）

**例:**
```typescript
const [currentPath, setCurrentPath] = useState("");
// currentPath に現在のパスを保存
// setCurrentPath でパスを変更できる
```

---

### SWR (Stale-While-Revalidate)
**説明:** データ取得を簡単にするライブラリ

**メリット:**
- 自動でキャッシュ（一度取得したデータを記憶）
- 自動で再取得（画面に戻った時に最新データを取得）
- ローディング状態を自動管理

**例:**
```typescript
const { data, error, isLoading } = useSWR(
  ['file-browser', currentPath],
  async () => {
    // ファイル一覧を取得
  }
);
```

---

### WebSocket
**説明:** サーバーとリアルタイムで双方向通信する技術

**通常のHTTP:**
```
クライアント → サーバー: データください
クライアント ← サーバー: データをどうぞ
```

**WebSocket:**
```
クライアント ⇄ サーバー: 常に接続
サーバー → クライアント: ファイルが変更されました！
クライアント: すぐに画面を更新します
```

**メリット:**
- リアルタイムに更新を通知できる
- サーバーから自発的に情報を送れる
- ポーリング（定期的に確認）より効率的

---

### ResizablePanel
**説明:** パネルのサイズを変更できるUI部品

ユーザーがパネルの境界線をドラッグすると、サイズを自由に変更できます。

```
┌─────┬────────┬──────────┐
│     │        │          │
│  A  │   B    │    C     │  ← ドラッグでサイズ変更可能
│     │        │          │
└─────┴────────┴──────────┘
```

---

## 実装の詳細

### 1. useFileBrowserフックの仕組み

#### ファイル一覧の取得
```typescript
const { data, error, isLoading, mutate } = useSWR<FileBrowserResponse>(
  ['file-browser', currentPath],  // キャッシュのキー
  async ([_, path]) => {
    // FastAPI サーバーにリクエスト
    const params = new URLSearchParams({ path });
    const response = await fetch(`${FILE_API_URL}/api/files?${params}`);
    return response.json();
  }
);
```

**解説:**
1. `currentPath`が変わるたびに自動でデータを取得
2. 取得したデータは`data`に格納
3. `mutate()`を呼ぶと手動で再取得

#### WebSocket接続
```typescript
useEffect(() => {
  const ws = new WebSocket(`${wsUrl}/ws`);

  ws.onopen = () => {
    // 接続成功時
    setWsConnected(true);

    // 30秒ごとにpingを送信（接続維持）
    const pingInterval = setInterval(() => {
      ws.send('ping');
    }, 30000);
  };

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);

    // ファイル変更通知を受信したら
    if (['created', 'modified', 'deleted', 'moved'].includes(message.event)) {
      mutate(); // ファイル一覧を再取得
    }
  };

  return () => {
    ws.close(); // コンポーネントが消える時に切断
  };
}, [mutate]);
```

**解説:**
1. WebSocketサーバーに接続
2. ファイル変更通知が来たら`mutate()`で再取得
3. 30秒ごとにpingを送って接続を維持
4. コンポーネントがアンマウントされたら切断

---

### 2. FileBrowserコンポーネントの仕組み

#### パンくずナビゲーション
```typescript
const pathSegments = currentPath
  ? currentPath.split("/").filter(Boolean)
  : [];

// 表示: Home > folder1 > folder2
```

**解説:**
- `currentPath`を`/`で分割
- 各セグメントをクリック可能なリンクとして表示
- Homeをクリックするとルートに戻る

#### ファイルプレビュー
```typescript
const handleFileSelect = async (file: FileSystemItem) => {
  if (file.type === "file") {
    const content = await readFile(file.path);
    setSelectedFile({
      path: file.path,
      content: content.content,
    });
  }
};
```

**解説:**
1. ファイルがクリックされたら`readFile()`を呼び出し
2. ファイル内容を取得
3. `FileViewDialog`で表示

---

### 3. FileSystemListコンポーネントの仕組み

#### アイコンの選択
```typescript
const getFileIcon = (item: FileSystemItem) => {
  if (item.type === "directory") return Folder;

  const ext = item.extension?.toLowerCase();
  if (ext === "py") return FileCode;
  if (["js", "ts", "jsx", "tsx"].includes(ext || "")) return FileCode;
  if (["md", "txt"].includes(ext || "")) return FileText;

  return File;
};
```

**解説:**
- フォルダなら📁アイコン
- Pythonファイルならコードアイコン
- テキストファイルならテキストアイコン
- それ以外は汎用ファイルアイコン

#### ファイルサイズのフォーマット
```typescript
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
};
```

**解説:**
- 1024バイト未満: バイト表示
- 1MB未満: KB表示
- それ以上: MB表示

---

## 環境変数

### `.env.local`
```
NEXT_PUBLIC_FILE_API_URL=http://localhost:8124
```

**説明:**
- `NEXT_PUBLIC_`で始まる変数はブラウザでも使用可能
- FastAPIサーバーのURLを指定
- 本番環境では異なるURLに変更可能

---

## トラブルシューティング

### ファイル一覧が表示されない
**確認事項:**
1. FastAPIサーバーが起動しているか
2. `.env.local`にAPIのURLが設定されているか
3. ブラウザのコンソールにエラーが出ていないか

### リアルタイム更新が動かない
**確認事項:**
1. WebSocketが接続されているか（ブラウザコンソールで確認）
2. `[FileBrowser] WebSocket connected to ws://localhost:8124/ws`が表示されるか

### ファイルをクリックしてもプレビューが出ない
**確認事項:**
1. ファイルサイズが10MB以下か
2. テキストファイルか（バイナリファイルは非対応）
3. ブラウザコンソールにエラーが出ていないか

---

## まとめ

### 追加したファイル
- `useFileBrowser.ts` - データ管理
- `FileBrowser.tsx` - メイン画面
- `FileSystemList.tsx` - ファイル一覧表示
- `page.tsx` - レイアウト変更

### 使用している主な技術
- React Hooks (useState, useEffect, useCallback)
- SWR (データフェッチング)
- WebSocket (リアルタイム通信)
- ResizablePanel (サイズ変更可能なパネル)

### データの流れ
1. ユーザーがボタンをクリック
2. FastAPIサーバーからデータ取得
3. 画面に表示
4. WebSocketでリアルタイム更新

これにより、エージェントが作成・編集したファイルをリアルタイムで確認できるようになりました！
