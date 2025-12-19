\# フロントエンドアーキテクチャガイド



\## 概要



フロントエンドは \*\*Next.js 16 + React 19\*\* で構築されたシングルページアプリケーション (SPA) です。Radix UI/Shadcn UIコンポーネント、Tailwind CSSスタイリング、LangGraph SDKとのリアルタイム通信を特徴としています。



\## 目次



1\. \[プロジェクト構成](#プロジェクト構成)

2\. \[エントリーポイント](#エントリーポイント)

3\. \[コンポーネントアーキテクチャ](#コンポーネントアーキテクチャ)

4\. \[状態管理](#状態管理)

5\. \[カスタムフック](#カスタムフック)

6\. \[API通信](#api通信)

7\. \[スタイリング](#スタイリング)

8\. \[開発ワークフロー](#開発ワークフロー)



\## プロジェクト構成



```

frontend/

├── src/

│   ├── app/                          # Next.js App Router

│   │   ├── components/               # アプリケーションコンポーネント

│   │   │   ├── ChatInterface.tsx     # チャットUI

│   │   │   ├── ChatMessage.tsx       # メッセージ表示

│   │   │   ├── ThreadList.tsx        # スレッド一覧

│   │   │   ├── FileBrowser.tsx       # ファイルブラウザ

│   │   │   ├── FileSystemList.tsx    # ファイルツリー

│   │   │   ├── FileViewDialog.tsx    # ファイル表示モーダル

│   │   │   ├── ToolCallBox.tsx       # ツール実行表示

│   │   │   ├── ToolApprovalInterrupt.tsx  # ツール承認UI

│   │   │   ├── SubAgentIndicator.tsx # サブエージェント表示

│   │   │   ├── TasksFilesSidebar.tsx # タスク/ファイルサイドバー

│   │   │   ├── ConfigDialog.tsx      # 設定モーダル

│   │   │   └── MarkdownContent.tsx   # Markdownレンダリング

│   │   ├── hooks/                    # カスタムReactフック

│   │   │   ├── useChat.ts            # チャット状態管理 (167行)

│   │   │   ├── useThreads.ts         # スレッド管理

│   │   │   └── useFileBrowser.ts     # ファイル操作

│   │   ├── types/                    # TypeScript型定義

│   │   │   └── types.ts              # 共通型定義

│   │   ├── utils/                    # ユーティリティ関数

│   │   ├── layout.tsx                # ルートレイアウト

│   │   └── page.tsx                  # メインページ (322行)

│   ├── components/ui/                # Shadcn UIコンポーネント

│   │   ├── button.tsx                # ボタン

│   │   ├── dialog.tsx                # モーダル

│   │   ├── select.tsx                # セレクト

│   │   ├── tabs.tsx                  # タブ

│   │   ├── scroll-area.tsx           # スクロールエリア

│   │   └── ...                       # その他UIコンポーネント

│   └── providers/                    # Reactコンテキストプロバイダー

│       ├── ClientProvider.tsx        # LangGraphクライアント

│       └── ChatProvider.tsx          # チャット状態

├── public/                           # 静的アセット

├── package.json                      # 依存関係

├── tsconfig.json                     # TypeScript設定

├── next.config.ts                    # Next.js設定

├── tailwind.config.mjs               # Tailwindテーマ

└── components.json                   # Shadcn設定

```



\## エントリーポイント



\### メインページ: `src/app/page.tsx`



\*\*場所\*\*: `frontend/src/app/page.tsx:1`



このファイルはアプリケーションのメインエントリーポイントで、3つの主要セクションを含むレスポンシブレイアウトを定義します。



\*\*構造\*\*:

```typescript

export default function HomePage() {

&nbsp; // 1. LangGraph設定の取得 (1-50行目)

&nbsp; const { deploymentUrl, apiKey } = await fetchConfig()

&nbsp; const assistantId = await fetchDefaultAssistant()



&nbsp; return (

&nbsp;   <ClientProvider deploymentUrl={deploymentUrl} apiKey={apiKey}>

&nbsp;     <HomePageContent assistantId={assistantId} />

&nbsp;   </ClientProvider>

&nbsp; )

}

```



\*\*HomePageContent\*\*: `frontend/src/app/page.tsx:107`

\- ResizablePanelGroupを使用した3パネルレイアウト

\- パネルの表示/非表示をURL状態で管理



\*\*主要セクション\*\*:



1\. \*\*ヘッダー\*\* (116-171行目)

&nbsp;  ```typescript

&nbsp;  - タイトル: "Deep Agent UI"

&nbsp;  - スレッド/ファイル表示トグル

&nbsp;  - アシスタント選択表示

&nbsp;  - 設定ボタン

&nbsp;  - 新規スレッドボタン

&nbsp;  ```



2\. \*\*スレッドパネル\*\* (180-197行目)

&nbsp;  - ThreadListコンポーネント

&nbsp;  - 会話履歴の管理



3\. \*\*ファイルブラウザパネル\*\* (200-212行目)

&nbsp;  - FileBrowserコンポーネント

&nbsp;  - ファイルシステム操作



4\. \*\*チャットパネル\*\* (215-227行目)

&nbsp;  - ChatInterfaceコンポーネント

&nbsp;  - メッセージ表示と入力



\### レイアウト: `src/app/layout.tsx`



ルートレイアウトで、フォント設定とメタデータを定義します。



\## コンポーネントアーキテクチャ



\### 1. ChatInterface - チャットUI



\*\*場所\*\*: `frontend/src/app/components/ChatInterface.tsx`



\*\*責務\*\*:

\- メッセージの表示 (ストリーミング対応)

\- ユーザー入力フォーム

\- タスク/ファイルメタデータの表示

\- エージェント状態の可視化



\*\*使用フック\*\*:

\- `useChatContext()` - チャット状態とアクション



\*\*主要機能\*\*:

```typescript

const {

&nbsp; messages,           // 全メッセージ

&nbsp; sendMessage,        // メッセージ送信

&nbsp; isStreaming,        // ストリーミング中か

&nbsp; stopStream,         // ストリーミング停止

&nbsp; todos,              // タスクリスト

&nbsp; files               // ファイル辞書

} = useChatContext()

```



\### 2. ChatMessage - メッセージ表示



\*\*場所\*\*: `frontend/src/app/components/ChatMessage.tsx`



\*\*責務\*\*:

\- 人間/AIメッセージのレンダリング

\- Markdownとコードハイライト

\- ツール呼び出し表示



\*\*メッセージタイプ\*\*:

\- `human` - ユーザーメッセージ

\- `ai` - AIレスポンス

\- `tool` - ツール実行結果



\### 3. ToolCallBox - ツール実行表示



\*\*場所\*\*: `frontend/src/app/components/ToolCallBox.tsx`



\*\*責務\*\*:

\- ツール呼び出しの詳細表示

\- 引数と結果の展開可能な表示

\- ステータスアイコン (保留中、完了、エラー)



\*\*データ構造\*\*:

```typescript

interface ToolCall {

&nbsp; id: string

&nbsp; name: string                    // ツール名

&nbsp; args: Record<string, unknown>   // 引数

&nbsp; result?: string                 // 実行結果

&nbsp; status: "pending" | "completed" | "error" | "interrupted"

}

```



\### 4. ToolApprovalInterrupt - ツール承認UI



\*\*場所\*\*: `frontend/src/app/components/ToolApprovalInterrupt.tsx`



\*\*責務\*\*:

\- Human-in-the-Loop (HITL) ツール承認インターフェース

\- ツールパラメータの表示

\- 承認/拒否/自動承認オプション



\*\*承認フロー\*\*:

1\. エージェントがツール実行を要求

2\. UIに承認プロンプトを表示

3\. ユーザーが承認/拒否を選択

4\. `resumeInterrupt()` で応答を送信

5\. エージェントが実行を継続/中止



\### 5. ThreadList - スレッド一覧



\*\*場所\*\*: `frontend/src/app/components/ThreadList.tsx`



\*\*責備\*\*:

\- 会話スレッドの一覧表示

\- ステータスフィルター (idle, busy, interrupted, error)

\- スレッド作成/削除

\- アクティブスレッドのハイライト



\*\*使用フック\*\*:

\- `useThreads()` - スレッド管理



\### 6. FileBrowser - ファイルブラウザ



\*\*場所\*\*: `frontend/src/app/components/FileBrowser.tsx`



\*\*責務\*\*:

\- ファイルシステムのブラウジング

\- ディレクトリナビゲーション (パンくずリスト)

\- ファイルアップロード

\- リアルタイムファイル更新 (WebSocket)



\*\*使用フック\*\*:

\- `useFileBrowser()` - ファイル操作



\*\*主要機能\*\*:

```typescript

const {

&nbsp; files,              // ファイルツリー

&nbsp; currentPath,        // 現在のパス

&nbsp; navigateTo,         // ディレクトリ移動

&nbsp; uploadFiles,        // ファイルアップロード

&nbsp; deleteFile,         // ファイル削除

&nbsp; readFile,           // ファイル読み取り

&nbsp; updateFile          // ファイル更新

} = useFileBrowser()

```



\### 7. FileViewDialog - ファイル表示モーダル



\*\*場所\*\*: `frontend/src/app/components/FileViewDialog.tsx`



\*\*責務\*\*:

\- ファイル内容のモーダル表示

\- シンタックスハイライト

\- ファイル編集機能



\### 8. SubAgentIndicator - サブエージェント表示



\*\*場所\*\*: `frontend/src/app/components/SubAgentIndicator.tsx`



\*\*責務\*\*:

\- サブエージェント実行の可視化

\- 展開/折りたたみ可能な表示



\*\*データ構造\*\*:

```typescript

interface SubAgent {

&nbsp; id: string

&nbsp; name: string

&nbsp; subAgentName: string

&nbsp; input: Record<string, unknown>

&nbsp; output?: Record<string, unknown>

&nbsp; status: "pending" | "active" | "completed" | "error"

}

```



\### 9. ConfigDialog - 設定モーダル



\*\*場所\*\*: `frontend/src/app/components/ConfigDialog.tsx`



\*\*責務\*\*:

\- アシスタント設定

\- デプロイメントURL設定

\- LocalStorageへの保存



\## 状態管理



\### URL状態管理 (Nuqs)



\*\*場所\*\*: `frontend/src/app/page.tsx:70-90`



URL検索パラメータで状態を管理:



```typescript

const \[threadId, setThreadId] = useQueryState("threadId")

const \[assistantId, setAssistantId] = useQueryState("assistantId")

const \[showThreads, setShowThreads] = useQueryState("sidebar", parseAsBoolean.withDefault(true))

const \[showFiles, setShowFiles] = useQueryState("fileBrowser", parseAsBoolean.withDefault(true))

```



\*\*利点\*\*:

\- URLで状態を共有可能

\- ブラウザの戻る/進むが機能

\- リロード時に状態を保持



\### コンテキストプロバイダー



\#### 1. ClientProvider



\*\*場所\*\*: `frontend/src/providers/ClientProvider.tsx`



LangGraph SDK `Client` インスタンスをアプリケーション全体に提供します。



```typescript

const ClientProvider = ({ children, deploymentUrl, apiKey }) => {

&nbsp; const client = new Client({

&nbsp;   apiUrl: deploymentUrl,

&nbsp;   headers: {

&nbsp;     "Content-Type": "application/json",

&nbsp;     ...(apiKey \&\& { "X-Api-Key": apiKey })

&nbsp;   }

&nbsp; })



&nbsp; return (

&nbsp;   <ClientContext.Provider value={client}>

&nbsp;     {children}

&nbsp;   </ClientContext.Provider>

&nbsp; )

}

```



\*\*使用方法\*\*:

```typescript

const client = useClient()

```



\#### 2. ChatProvider



\*\*場所\*\*: `frontend/src/providers/ChatProvider.tsx`



`useChat()` フックをコンテキストでラップし、コンポーネント間でチャット状態を共有します。



```typescript

const ChatProvider = ({ children, threadId, assistantId }) => {

&nbsp; const chatState = useChat({ threadId, assistantId })



&nbsp; return (

&nbsp;   <ChatContext.Provider value={chatState}>

&nbsp;     {children}

&nbsp;   </ChatContext.Provider>

&nbsp; )

}

```



\*\*使用方法\*\*:

```typescript

const { messages, sendMessage, ... } = useChatContext()

```



\## カスタムフック



\### 1. useChat - チャット状態管理



\*\*場所\*\*: `frontend/src/app/hooks/useChat.ts:1`

\*\*行数\*\*: 167行



\*\*最重要フック\*\*: すべてのチャット機能を統合管理します。



\*\*パラメータ\*\*:

```typescript

interface UseChatProps {

&nbsp; threadId: string | null      // スレッドID (nullで新規作成)

&nbsp; assistantId: string          // アシスタントID

}

```



\*\*返り値\*\*:

```typescript

{

&nbsp; // 状態

&nbsp; messages: Message\[]          // 全メッセージ

&nbsp; todos: TodoItem\[]            // タスクリスト

&nbsp; files: Record<string, string>  // ファイル辞書

&nbsp; email?: EmailObject          // メールオブジェクト

&nbsp; ui?: any                     // カスタムUI状態

&nbsp; isStreaming: boolean         // ストリーミング中か

&nbsp; interrupt?: InterruptData    // 割り込みデータ



&nbsp; // アクション

&nbsp; sendMessage: (content: string) => Promise<void>

&nbsp; runSingleStep: () => Promise<void>

&nbsp; continueStream: () => Promise<void>

&nbsp; resumeInterrupt: (value: any) => Promise<void>

&nbsp; stopStream: () => Promise<void>

&nbsp; setFiles: (files: Record<string, string>) => Promise<void>

}

```



\*\*内部実装\*\*:



1\. \*\*ストリーミング設定\*\* (20-50行目)

```typescript

const { stream, stopStream } = useStream({

&nbsp; client,

&nbsp; threadId,

&nbsp; assistantId,

&nbsp; onUpdate: (update) => {

&nbsp;   // メッセージ、todos、filesを更新

&nbsp; },

&nbsp; onError: (error) => {

&nbsp;   // エラーハンドリング

&nbsp; }

})

```



2\. \*\*メッセージ送信\*\* (60-80行目)

```typescript

const sendMessage = async (content: string) => {

&nbsp; // 楽観的更新

&nbsp; setMessages(\[...messages, { role: "human", content }])



&nbsp; // ストリーミング開始

&nbsp; await stream({ messages: \[...messages, { role: "human", content }] })

}

```



3\. \*\*状態履歴取得\*\* (90-110行目)

```typescript

useEffect(() => {

&nbsp; if (threadId) {

&nbsp;   // スレッド状態を取得してtodos、filesを復元

&nbsp;   fetchThreadState(threadId)

&nbsp; }

}, \[threadId])

```



\*\*使用例\*\*:

```typescript

const { messages, sendMessage, todos, files, isStreaming } = useChat({

&nbsp; threadId: "thread-123",

&nbsp; assistantId: "assistant-456"

})



// メッセージ送信

await sendMessage("こんにちは")



// ストリーミング停止

stopStream()

```



\### 2. useThreads - スレッド管理



\*\*場所\*\*: `frontend/src/app/hooks/useThreads.ts`



\*\*責務\*\*:

\- スレッド一覧の取得 (ページネーション対応)

\- ステータスフィルター

\- スレッド削除



\*\*返り値\*\*:

```typescript

{

&nbsp; threads: Thread\[]            // スレッド配列

&nbsp; isLoading: boolean           // ロード中か

&nbsp; error?: Error                // エラー

&nbsp; deleteThread: (id: string) => Promise<void>

&nbsp; filterByStatus: (status: ThreadStatus) => void

}

```



\### 3. useFileBrowser - ファイル操作



\*\*場所\*\*: `frontend/src/app/hooks/useFileBrowser.ts`



\*\*責務\*\*:

\- ファイル/ディレクトリ一覧取得

\- ファイル読み取り/更新/削除

\- ファイルアップロード

\- WebSocketでリアルタイム更新



\*\*返り値\*\*:

```typescript

{

&nbsp; files: FileNode\[]            // ファイルツリー

&nbsp; currentPath: string          // 現在のパス

&nbsp; navigateTo: (path: string) => void

&nbsp; readFile: (path: string) => Promise<string>

&nbsp; updateFile: (path: string, content: string) => Promise<void>

&nbsp; deleteFile: (path: string) => Promise<void>

&nbsp; uploadFiles: (files: File\[], targetPath: string) => Promise<void>

}

```



\*\*WebSocket接続\*\* (内部実装):

```typescript

useEffect(() => {

&nbsp; const ws = new WebSocket(`${wsUrl}/ws`)



&nbsp; ws.onmessage = (event) => {

&nbsp;   const { type, path, data } = JSON.parse(event.data)



&nbsp;   // ファイル変更を状態に反映

&nbsp;   if (type === "created" || type === "modified") {

&nbsp;     updateFileInTree(path, data)

&nbsp;   } else if (type === "deleted") {

&nbsp;     removeFileFromTree(path)

&nbsp;   }

&nbsp; }

}, \[])

```



\## API通信



\### LangGraph SDK統合



\*\*クライアント作成\*\*: `frontend/src/providers/ClientProvider.tsx:10-20`



```typescript

import { Client } from "@langchain/langgraph-sdk"



const client = new Client({

&nbsp; apiUrl: "http://localhost:8124/agent",

&nbsp; headers: {

&nbsp;   "Content-Type": "application/json",

&nbsp;   "X-Api-Key": apiKey  // オプション

&nbsp; }

})

```



\### API エンドポイント



すべてのリクエストはFastAPIサーバー経由でプロキシされます。



\#### LangGraph プロキシ



\*\*ベースURL\*\*: `/agent/\*`



\- `POST /agent/threads/search` - スレッド検索

\- `GET /agent/threads/{thread\_id}` - スレッド取得

\- `POST /agent/threads` - スレッド作成

\- `DELETE /agent/threads/{thread\_id}` - スレッド削除

\- `GET /agent/assistants` - アシスタント一覧

\- `POST /agent/threads/{thread\_id}/runs/stream` - ストリーミング実行 (SSE)



\#### ファイルAPI



\*\*ベースURL\*\*: `/api/files`



```typescript

// ファイル一覧取得

GET /api/files?path=/some/dir

Response: FileNode\[]



// ファイル読み取り

GET /api/files/path/to/file.txt?raw=false

Response: { content: string, language: string }



// ファイル更新

PUT /api/files/path/to/file.txt

Body: { path: string, content: string }



// ファイル削除

DELETE /api/files/path/to/file.txt



// ファイルアップロード

POST /api/files/upload

Body: FormData { files: File\[], targetPath: string }

```



\#### WebSocket



```typescript

const ws = new WebSocket("ws://localhost:8124/ws")



ws.onmessage = (event) => {

&nbsp; const message = JSON.parse(event.data)

&nbsp; // { type: "created" | "modified" | "deleted" | "moved", path: string, data?: any }

}

```



\### データ型



\*\*場所\*\*: `frontend/src/app/types/types.ts`



```typescript

interface Message {

&nbsp; role: "human" | "ai" | "tool"

&nbsp; content: string

&nbsp; toolCalls?: ToolCall\[]

}



interface ToolCall {

&nbsp; id: string

&nbsp; name: string

&nbsp; args: Record<string, unknown>

&nbsp; result?: string

&nbsp; status: "pending" | "completed" | "error" | "interrupted"

}



interface TodoItem {

&nbsp; id: string

&nbsp; content: string

&nbsp; status: "pending" | "in\_progress" | "completed"

&nbsp; updatedAt?: Date

}



interface FileNode {

&nbsp; name: string

&nbsp; path: string

&nbsp; type: "file" | "directory"

&nbsp; size?: number

&nbsp; modifiedAt?: string

&nbsp; children?: FileNode\[]

}



interface Thread {

&nbsp; thread\_id: string

&nbsp; created\_at: string

&nbsp; updated\_at: string

&nbsp; metadata: Record<string, any>

&nbsp; status: "idle" | "busy" | "interrupted" | "error"

}

```



\## スタイリング



\### Tailwind CSS



\*\*設定ファイル\*\*: `frontend/tailwind.config.mjs`



\*\*テーマカスタマイズ\*\*:

```javascript

theme: {

&nbsp; extend: {

&nbsp;   colors: {

&nbsp;     background: "hsl(var(--background))",

&nbsp;     foreground: "hsl(var(--foreground))",

&nbsp;     primary: { ... },

&nbsp;     secondary: { ... },

&nbsp;     // ...

&nbsp;   }

&nbsp; }

}

```



\*\*ダークモード\*\*: クラスベース (`class` strategy)



\*\*使用例\*\*:

```tsx

<div className="bg-background text-foreground p-4 rounded-lg">

&nbsp; <h1 className="text-2xl font-bold text-primary">タイトル</h1>

</div>

```



\### Shadcn UI



\*\*設定ファイル\*\*: `frontend/components.json`



\*\*インストール済みコンポーネント\*\*:

\- Button, Dialog, Select, Tabs, ScrollArea, Tooltip, Label, Switch, など



\*\*コンポーネント追加\*\*:

```bash

npx shadcn@latest add \[component-name]

```



\*\*カスタマイズ\*\*:

`frontend/src/components/ui/` 内のファイルを直接編集できます。



\### CSS変数



\*\*場所\*\*: `frontend/src/app/globals.css`



```css

@layer base {

&nbsp; :root {

&nbsp;   --background: 0 0% 100%;

&nbsp;   --foreground: 222.2 84% 4.9%;

&nbsp;   --primary: 221.2 83.2% 53.3%;

&nbsp;   /\* ... \*/

&nbsp; }



&nbsp; .dark {

&nbsp;   --background: 222.2 84% 4.9%;

&nbsp;   --foreground: 210 40% 98%;

&nbsp;   /\* ... \*/

&nbsp; }

}

```



\## 開発ワークフロー



\### セットアップ



```bash

cd frontend

npm install

```



\### 開発サーバー



```bash

npm run dev

```



アクセス: http://localhost:3000



\*\*特徴\*\*:

\- ホットリロード (Turbopack)

\- 高速リフレッシュ

\- TypeScriptエラー表示



\### ビルド



```bash

npm run build

```



\*\*出力\*\*: `frontend/out/` (静的エクスポート)



\*\*設定\*\*: `frontend/next.config.ts:5` で `output: "export"` を指定



\### プロダクションサーバー



```bash

npm start

```



または静的ファイルサーバー:

```bash

npx serve out

```



\### コード品質



```bash

\# リント

npm run lint



\# 自動修正

npm run lint:fix



\# フォーマット

npm run format



\# フォーマットチェック

npm run format:check

```



\### 型チェック



```bash

npx tsc --noEmit

```



\## コンポーネント開発



\### 新しいコンポーネントを追加



1\. \*\*コンポーネントファイルを作成\*\*:

```bash

touch frontend/src/app/components/MyNewComponent.tsx

```



2\. \*\*テンプレート\*\*:

```typescript

"use client"



import { useState } from "react"



interface MyNewComponentProps {

&nbsp; title: string

}



export function MyNewComponent({ title }: MyNewComponentProps) {

&nbsp; const \[state, setState] = useState("")



&nbsp; return (

&nbsp;   <div className="p-4">

&nbsp;     <h2 className="text-xl font-bold">{title}</h2>

&nbsp;     {/\* コンポーネント内容 \*/}

&nbsp;   </div>

&nbsp; )

}

```



3\. \*\*親コンポーネントからインポート\*\*:

```typescript

import { MyNewComponent } from "./components/MyNewComponent"



export default function Page() {

&nbsp; return <MyNewComponent title="タイトル" />

}

```



\### カスタムフックを追加



1\. \*\*フックファイルを作成\*\*:

```bash

touch frontend/src/app/hooks/useMyHook.ts

```



2\. \*\*テンプレート\*\*:

```typescript

import { useState, useEffect } from "react"



export function useMyHook() {

&nbsp; const \[data, setData] = useState(null)



&nbsp; useEffect(() => {

&nbsp;   // 初期化ロジック

&nbsp; }, \[])



&nbsp; return { data }

}

```



\### Shadcn UIコンポーネント追加



```bash

npx shadcn@latest add \[component-name]

```



例:

```bash

npx shadcn@latest add dropdown-menu

```



\## デバッグ



\### React DevTools



ブラウザ拡張機能をインストール:

\- \[React Developer Tools](https://react.dev/learn/react-developer-tools)



\### コンソールログ



```typescript

console.log("Debug:", { messages, todos, files })

```



\### ネットワークタブ



1\. ブラウザのDevToolsを開く (F12)

2\. Networkタブを選択

3\. API リクエスト/レスポンスを確認



\### エラーバウンダリ



`layout.tsx` または個別コンポーネントでエラーバウンダリを追加:

```typescript

import { ErrorBoundary } from "react-error-boundary"



<ErrorBoundary fallback={<div>エラーが発生しました</div>}>

&nbsp; <MyComponent />

</ErrorBoundary>

```



\## パフォーマンス最適化



\### メモ化



```typescript

import { memo, useMemo, useCallback } from "react"



// コンポーネントメモ化

export const MyComponent = memo(({ data }) => {

&nbsp; // ...

})



// 値のメモ化

const expensiveValue = useMemo(() => {

&nbsp; return computeExpensiveValue(data)

}, \[data])



// 関数のメモ化

const handleClick = useCallback(() => {

&nbsp; doSomething(data)

}, \[data])

```



\### 仮想化 (長いリスト)



大量のアイテムを表示する場合、仮想化を検討:

```bash

npm install @tanstack/react-virtual

```



\### 画像最適化



Next.js Image コンポーネントを使用:

```typescript

import Image from "next/image"



<Image src="/image.png" width={500} height={300} alt="説明" />

```



\## トラブルシューティング



\### バックエンドに接続できない



1\. `page.tsx:25-35` のデプロイメントURL設定を確認

2\. バックエンドが起動しているか確認: `curl http://localhost:8124/health`

3\. CORSエラーがないかブラウザコンソールを確認



\### メッセージが表示されない



1\. `useChat` フックが正しく初期化されているか確認

2\. `threadId` が正しく設定されているか確認

3\. ネットワークタブでストリーミングレスポンスを確認



\### ファイル変更が反映されない



1\. WebSocket接続が確立されているか確認

2\. ブラウザコンソールでWebSocketメッセージを確認

3\. バックエンドのファイルウォッチャーが起動しているか確認



\### スタイルが適用されない



1\. Tailwind CSSクラスが正しいか確認

2\. `globals.css` がインポートされているか確認: `layout.tsx:2`

3\. ビルド後に `npm run dev` を再起動



\## 参考資料



\- \[Next.js App Router](https://nextjs.org/docs/app)

\- \[React 19 ドキュメント](https://react.dev/)

\- \[Tailwind CSS](https://tailwindcss.com/docs)

\- \[Shadcn UI](https://ui.shadcn.com/)

\- \[Radix UI](https://www.radix-ui.com/)

\- \[LangGraph SDK](https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python\_sdk\_ref/)

\- \[TypeScript](https://www.typescriptlang.org/docs/)



\[← アーキテクチャ概要に戻る](../../ARCHITECTURE.md)

