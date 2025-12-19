\# Deep Agent UI アーキテクチャガイド



\## 目次

1\. \[概要](#概要)

2\. \[全体構造](#全体構造)

3\. \[ディレクトリ構造](#ディレクトリ構造)

4\. \[データフロー](#データフロー)

5\. \[主要コンポーネントの説明](#主要コンポーネントの説明)

6\. \[状態管理](#状態管理)

7\. \[通信の仕組み](#通信の仕組み)

8\. \[機能追加・カスタマイズガイド](#機能追加カスタマイズガイド)



---



\## 概要



Deep Agent UIは、LangGraphベースのAIエージェント（Deep Agents）と対話するためのウェブインターフェースです。



\### 技術スタック

\- \*\*フロントエンド\*\*: Next.js 16 + React 19 + TypeScript

\- \*\*スタイリング\*\*: Tailwind CSS

\- \*\*UI コンポーネント\*\*: Radix UI (アクセシブルなプリミティブ)

\- \*\*状態管理\*\*: React Context + カスタムhooks + SWR (データフェッチング)

\- \*\*通信\*\*: LangGraph SDK (ストリーミング) + WebSocket (ファイル監視)



---



\## 全体構造



Deep Agent UIは以下の3つの主要な部分で構成されています：



```

┌─────────────────────────────────────────────────────────┐

│                    Deep Agent UI                         │

│                  (Next.js フロントエンド)                │

└─────────────┬───────────────────────────┬───────────────┘

&nbsp;             │                           │

&nbsp;             │ LangGraph SDK             │ HTTP + WebSocket

&nbsp;             │ (ストリーミング)          │ (ファイル監視)

&nbsp;             ▼                           ▼

&nbsp;   ┌──────────────────┐        ┌──────────────────┐

&nbsp;   │  LangGraph API   │        │  ファイルAPI      │

&nbsp;   │  (port: 2024)    │        │  (port: 8124)    │

&nbsp;   └──────────────────┘        └──────────────────┘

&nbsp;             │

&nbsp;             ▼

&nbsp;       ┌──────────┐

&nbsp;       │  Agent   │

&nbsp;       │  (AI)    │

&nbsp;       └──────────┘

```



\### 主な機能

1\. \*\*チャットインターフェース\*\*: AIエージェントとメッセージのやり取り

2\. \*\*スレッド管理\*\*: 複数の会話履歴の管理

3\. \*\*TODOトラッキング\*\*: エージェントのタスク進捗表示

4\. \*\*ファイルブラウザ\*\*: エージェントが操作するファイルの閲覧・編集

5\. \*\*ツール実行の可視化\*\*: エージェントが使うツールの実行状況表示



---



\## ディレクトリ構造



```

deep-agents-ui/

├── src/

│   ├── app/                    # Next.js App Router

│   │   ├── components/         # UIコンポーネント

│   │   │   ├── ChatInterface.tsx      # チャット画面のメイン

│   │   │   ├── ChatMessage.tsx        # 個別のメッセージ表示

│   │   │   ├── ThreadList.tsx         # スレッド一覧

│   │   │   ├── FileBrowser.tsx        # ファイルブラウザ

│   │   │   ├── ConfigDialog.tsx       # 設定ダイアログ

│   │   │   └── ...

│   │   ├── hooks/              # カスタムhooks

│   │   │   ├── useChat.ts             # チャット機能のロジック

│   │   │   ├── useThreads.ts          # スレッド管理

│   │   │   └── useFileBrowser.ts      # ファイルブラウザ

│   │   ├── types/              # TypeScript型定義

│   │   │   └── types.ts

│   │   ├── utils/              # ユーティリティ関数

│   │   └── page.tsx            # ルートページ

│   │

│   ├── components/ui/          # 再利用可能なUIコンポーネント

│   │   ├── button.tsx

│   │   ├── dialog.tsx

│   │   └── ...

│   │

│   ├── providers/              # React Context Providers

│   │   ├── ClientProvider.tsx         # LangGraph Clientの提供

│   │   └── ChatProvider.tsx           # チャット状態の提供

│   │

│   └── lib/                    # ライブラリ・設定

│       ├── config.ts                  # アプリ設定

│       └── utils.ts                   # 汎用ユーティリティ

│

├── public/                     # 静的ファイル

├── package.json

└── next.config.ts

```



---



\## データフロー



\### 1. アプリケーション起動時のフロー



```

1\. ユーザーがアプリを開く

&nbsp;  ↓

2\. page.tsx (HomePage) がレンダリング

&nbsp;  ↓

3\. ローカルストレージから設定を読み込み (lib/config.ts)

&nbsp;  - deploymentUrl (LangGraph APIのURL)

&nbsp;  - assistantId (使用するエージェントのID)

&nbsp;  - langsmithApiKey (認証用)

&nbsp;  ↓

4\. 設定がない場合 → ConfigDialogを表示

&nbsp;  設定がある場合 → ClientProviderでLangGraph Clientを初期化

&nbsp;  ↓

5\. HomePageInner がレンダリング

&nbsp;  - ThreadListでスレッド一覧を取得

&nbsp;  - ChatProviderでチャット機能を初期化

&nbsp;  - FileBrowserでファイルシステムと接続

```



\### 2. メッセージ送信のフロー



```

1\. ユーザーがメッセージを入力

&nbsp;  ↓

2\. ChatInterface → handleSubmit()

&nbsp;  ↓

3\. useChatContext() → sendMessage(content)

&nbsp;  ↓

4\. useChat hook → stream.submit()

&nbsp;  ↓

5\. LangGraph SDK → APIにリクエスト送信

&nbsp;  ↓

6\. LangGraph API → Agentにメッセージを渡す

&nbsp;  ↓

7\. Agentから応答がストリーミングで返ってくる

&nbsp;  ↓

8\. useStream hook → stream.messages が更新される

&nbsp;  ↓

9\. ChatInterface → processedMessages が再計算

&nbsp;  ↓

10\. ChatMessage コンポーネントが新しいメッセージを表示

```



\### 3. ストリーミングされるデータの種類



LangGraph APIからストリーミングで以下のデータが送られてきます：



```typescript

{

&nbsp; messages: Message\[],      // チャットメッセージ

&nbsp; todos: TodoItem\[],         // TODO リスト

&nbsp; files: Record<string, string>, // ファイルの内容（キー：パス、値：内容）

&nbsp; ui: any,                   // カスタムUI情報

&nbsp; email: any                 // メール関連（オプション）

}

```



---



\## 主要コンポーネントの説明



\### 1. page.tsx (HomePage)

\*\*役割\*\*: アプリケーションのエントリーポイント



```

HomePage (Suspense wrapper)

&nbsp; └─ HomePageContent

&nbsp;     ├─ ConfigDialog を表示（設定がない場合）

&nbsp;     └─ ClientProvider でラップ

&nbsp;         └─ HomePageInner

&nbsp;             ├─ Header (設定ボタン、新規スレッドボタン)

&nbsp;             └─ ResizablePanelGroup (3カラムレイアウト)

&nbsp;                 ├─ ThreadList (左サイドバー)

&nbsp;                 ├─ FileBrowser (中央サイドバー)

&nbsp;                 └─ ChatProvider

&nbsp;                     └─ ChatInterface (メインチャット)

```



\*\*ポイント\*\*:

\- `nuqs` を使ってURLパラメータで状態管理（threadId、sidebar表示など）

\- 設定は `localStorage` に保存



\### 2. ClientProvider

\*\*役割\*\*: LangGraph SDKのClientインスタンスを全体で共有



```typescript

// providers/ClientProvider.tsx

const client = new Client({

&nbsp; apiUrl: deploymentUrl,      // 例: http://127.0.0.1:2024

&nbsp; defaultHeaders: {

&nbsp;   "X-Api-Key": apiKey,      // 認証キー

&nbsp; },

});

```



\*\*使い方\*\*:

```typescript

// どのコンポーネントからでもClientを取得できる

const client = useClient();

await client.threads.list();

```



\### 3. ChatProvider + useChat hook

\*\*役割\*\*: チャット機能の中核。メッセージ送受信、ストリーミングを管理



\*\*useChat hookの主な機能\*\*:



```typescript

export function useChat({

&nbsp; activeAssistant,

&nbsp; onHistoryRevalidate,

}) {

&nbsp; // LangGraph SDKのuseStreamを使用

&nbsp; const stream = useStream<StateType>({

&nbsp;   assistantId: activeAssistant?.assistant\_id,

&nbsp;   client: client,

&nbsp;   threadId: threadId,

&nbsp;   // ...

&nbsp; });



&nbsp; return {

&nbsp;   // 状態

&nbsp;   messages: stream.messages,

&nbsp;   todos: stream.values.todos,

&nbsp;   files: stream.values.files,

&nbsp;   isLoading: stream.isLoading,



&nbsp;   // 操作

&nbsp;   sendMessage,      // メッセージ送信

&nbsp;   continueStream,   // ストリーミング継続

&nbsp;   stopStream,       // ストリーミング停止

&nbsp;   // ...

&nbsp; };

}

```



\*\*データの流れ\*\*:

1\. `useStream` がLangGraph APIと接続

2\. ストリーミングでデータを受信

3\. `stream.values` にエージェントの状態が入る

4\. `stream.messages` にメッセージ履歴が入る

5\. これらをreactのstateとして公開



\### 4. ChatInterface

\*\*役割\*\*: チャット画面のUI表示



\*\*主な機能\*\*:

\- メッセージの表示

\- 入力フォーム

\- TODO表示

\- ファイル状態の表示



\*\*メッセージ処理の仕組み\*\*:

```typescript

// messagesを加工してツール呼び出しと結果を紐付ける

const processedMessages = useMemo(() => {

&nbsp; const messageMap = new Map();



&nbsp; // AIメッセージ → ツール呼び出しを抽出

&nbsp; // ツールメッセージ → 対応するツール呼び出しに結果を紐付け



&nbsp; return Array.from(messageMap.values());

}, \[messages, interrupt]);

```



\### 5. useFileBrowser hook

\*\*役割\*\*: ファイルシステムとの通信



\*\*通信方法\*\*:

\- HTTP API (ポート8124): ファイル一覧取得、ファイル読み込み

\- WebSocket: ファイル変更の監視（リアルタイム更新）



```typescript

export function useFileBrowser(initialPath = "") {

&nbsp; // SWRでファイル一覧をキャッシング

&nbsp; const { data, mutate } = useSWR(

&nbsp;   \['file-browser', currentPath],

&nbsp;   async (\[\_, path]) => {

&nbsp;     const response = await fetch(`${FILE\_API\_URL}/api/files?path=${path}`);

&nbsp;     return response.json();

&nbsp;   }

&nbsp; );



&nbsp; // WebSocketでファイル変更を監視

&nbsp; useEffect(() => {

&nbsp;   const ws = new WebSocket(`${wsUrl}/ws`);

&nbsp;   ws.onmessage = (event) => {

&nbsp;     // ファイル変更イベント → mutate()で再取得

&nbsp;     if (\['created', 'modified', 'deleted'].includes(message.event)) {

&nbsp;       mutate();

&nbsp;     }

&nbsp;   };

&nbsp; }, \[]);



&nbsp; return {

&nbsp;   items: data?.items,

&nbsp;   readFile,

&nbsp;   navigateTo,

&nbsp;   // ...

&nbsp; };

}

```



---



\## 状態管理



\### 1. グローバル状態 (Context)



| Context | 提供する値 | 使用場所 |

|---------|-----------|---------|

| ClientProvider | LangGraph SDK Client | API呼び出しが必要な全てのコンポーネント |

| ChatProvider | チャット状態 (messages, todos, files等) | ChatInterface配下 |



\### 2. ローカル状態 (useState)



\- 各コンポーネント内のUI状態（ダイアログの開閉、入力値など）

\- 例: `ChatInterface`の`input`（メッセージ入力値）



\### 3. URL状態 (nuqs)



\- `threadId`: 現在のスレッドID

\- `sidebar`: サイドバーの表示/非表示

\- `fileBrowser`: ファイルブラウザの表示/非表示

\- `assistantId`: アシスタントID



\*\*メリット\*\*: URLを共有するだけで同じ状態を再現できる



\### 4. ローカルストレージ



\- アプリの設定 (deploymentUrl, assistantId, apiKey)

\- パネルのサイズ（Resizable componentsが自動保存）



---



\## 通信の仕組み



\### 1. LangGraph API との通信



\*\*プロトコル\*\*: Server-Sent Events (SSE) によるストリーミング



```typescript

// useStreamフックが内部で行っていること

const eventSource = new EventSource(

&nbsp; `${apiUrl}/threads/${threadId}/runs/stream`

);



eventSource.onmessage = (event) => {

&nbsp; const data = JSON.parse(event.data);

&nbsp; // messages, todos, files などを更新

};

```



\*\*主なエンドポイント\*\*:

\- `POST /threads`: 新規スレッド作成

\- `POST /threads/{thread\_id}/runs/stream`: メッセージ送信 \& ストリーミング受信

\- `GET /threads/{thread\_id}/state`: スレッドの状態取得

\- `PATCH /threads/{thread\_id}/state`: 状態の更新（filesなど）



\### 2. ファイルAPI との通信



\*\*HTTPエンドポイント\*\* (ポート8124):

\- `GET /api/files?path={path}`: ファイル一覧取得

\- `GET /api/files/{filepath}`: ファイル内容取得



\*\*WebSocketエンドポイント\*\* (ポート8124):

\- `WS /ws`: ファイル変更通知の受信



```javascript

// ファイル変更イベントの例

{

&nbsp; "event": "modified",

&nbsp; "path": "/path/to/file.txt",

&nbsp; "timestamp": 1234567890

}

```



---



\## 機能追加・カスタマイズガイド



フロントエンドの知識が少ない方でも、以下のガイドに従えば機能追加やカスタマイズができます。



\### 🎨 1. UIの見た目を変える



\#### 色を変更する

Tailwind CSSの設定ファイルを編集:



\*\*ファイル\*\*: `tailwind.config.mjs`



```javascript

theme: {

&nbsp; extend: {

&nbsp;   colors: {

&nbsp;     // ここを変更すると全体の色が変わります

&nbsp;     primary: '#2F6868',    // メインカラー

&nbsp;     success: '#4ade80',    // 成功時の色

&nbsp;     warning: '#fbbf24',    // 警告の色

&nbsp;     // ...

&nbsp;   }

&nbsp; }

}

```



\#### ボタンのスタイルを変更する

\*\*ファイル\*\*: `src/components/ui/button.tsx`



```typescript

// variant="default"のボタンのスタイル

default: "bg-primary text-primary-foreground hover:bg-primary/90",



// ここを変更すると全てのボタンに適用される

```



\### ➕ 2. 新しいメッセージタイプを追加する



エージェントから特別な種類のメッセージを表示したい場合:



\*\*ステップ1\*\*: 型定義を追加

```typescript

// src/app/types/types.ts

export interface CustomMessageType {

&nbsp; type: "custom";

&nbsp; content: string;

&nbsp; metadata?: any;

}

```



\*\*ステップ2\*\*: メッセージ処理に追加

```typescript

// src/app/components/ChatMessage.tsx

if (message.type === "custom") {

&nbsp; return <div className="custom-message">{message.content}</div>;

}

```



\### 📊 3. 新しいサイドバーを追加する



例: グラフ表示用のサイドバーを追加



\*\*ステップ1\*\*: コンポーネントを作成

```typescript

// src/app/components/GraphViewer.tsx

export function GraphViewer({ onClose }: { onClose: () => void }) {

&nbsp; return (

&nbsp;   <div className="flex flex-col h-full">

&nbsp;     <div className="flex items-center justify-between p-4 border-b">

&nbsp;       <h2>グラフ</h2>

&nbsp;       <button onClick={onClose}>×</button>

&nbsp;     </div>

&nbsp;     <div className="flex-1 p-4">

&nbsp;       {/\* グラフの内容 \*/}

&nbsp;     </div>

&nbsp;   </div>

&nbsp; );

}

```



\*\*ステップ2\*\*: page.tsxに追加

```typescript

// src/app/page.tsx

const \[graphOpen, setGraphOpen] = useQueryState("graph");



// ResizablePanelGroup内に追加

{graphOpen \&\& (

&nbsp; <>

&nbsp;   <ResizablePanel id="graph" defaultSize={25}>

&nbsp;     <GraphViewer onClose={() => setGraphOpen(null)} />

&nbsp;   </ResizablePanel>

&nbsp;   <ResizableHandle />

&nbsp; </>

)}

```



\### 🔧 4. カスタムツールの実行結果を表示する



エージェントが新しいツールを使う場合、その結果を特別に表示したい場合:



\*\*ファイル\*\*: `src/app/components/ToolCallBox.tsx`を作成/編集



```typescript

export function ToolCallBox({ toolCall }: { toolCall: ToolCall }) {

&nbsp; // ツールごとに表示を変える

&nbsp; if (toolCall.name === "my\_custom\_tool") {

&nbsp;   return (

&nbsp;     <div className="border rounded p-4">

&nbsp;       <h3>カスタムツールの結果</h3>

&nbsp;       <pre>{JSON.stringify(toolCall.result, null, 2)}</pre>

&nbsp;     </div>

&nbsp;   );

&nbsp; }



&nbsp; // デフォルトの表示

&nbsp; return <div>{toolCall.name}: {toolCall.status}</div>;

}

```



\### 📁 5. エージェントの状態に新しいフィールドを追加する



例: エージェントが生成した画像を表示したい



\*\*ステップ1\*\*: 型定義を追加

```typescript

// src/app/hooks/useChat.ts

export type StateType = {

&nbsp; messages: Message\[];

&nbsp; todos: TodoItem\[];

&nbsp; files: Record<string, string>;

&nbsp; images?: string\[];  // ← 追加

};

```



\*\*ステップ2\*\*: 状態をhookから公開

```typescript

// src/app/hooks/useChat.ts

return {

&nbsp; // ...

&nbsp; images: stream.values.images ?? \[],  // ← 追加

};

```



\*\*ステップ3\*\*: ChatProviderで公開

```typescript

// src/providers/ChatProvider.tsx

export type ChatContextType = ReturnType<typeof useChat>;

// これだけでOK（useChatの返り値がそのまま使える）

```



\*\*ステップ4\*\*: UIで表示

```typescript

// src/app/components/ChatInterface.tsx

const { images } = useChatContext();



// UIに追加

{images.map(img => (

&nbsp; <img key={img} src={img} alt="Generated" />

))}

```



\### 🔌 6. 別のバックエンドAPIを追加する



ファイルAPI以外の独自APIと連携したい場合:



\*\*ステップ1\*\*: カスタムhookを作成

```typescript

// src/app/hooks/useCustomAPI.ts

export function useCustomAPI() {

&nbsp; const \[data, setData] = useState(null);



&nbsp; const fetchData = async () => {

&nbsp;   const response = await fetch('http://localhost:9000/api/custom');

&nbsp;   const json = await response.json();

&nbsp;   setData(json);

&nbsp; };



&nbsp; return { data, fetchData };

}

```



\*\*ステップ2\*\*: コンポーネントで使用

```typescript

// 任意のコンポーネントで

const { data, fetchData } = useCustomAPI();



useEffect(() => {

&nbsp; fetchData();

}, \[]);

```



\### 💡 7. 設定項目を追加する



アプリの設定に新しい項目を追加したい場合:



\*\*ステップ1\*\*: 型定義を更新

```typescript

// src/lib/config.ts

export interface StandaloneConfig {

&nbsp; deploymentUrl: string;

&nbsp; assistantId: string;

&nbsp; langsmithApiKey?: string;

&nbsp; customOption?: string;  // ← 追加

}

```



\*\*ステップ2\*\*: ConfigDialogに入力フィールドを追加

```typescript

// src/app/components/ConfigDialog.tsx

<div>

&nbsp; <Label>カスタムオプション</Label>

&nbsp; <Input

&nbsp;   value={config.customOption || ''}

&nbsp;   onChange={(e) => setConfig({

&nbsp;     ...config,

&nbsp;     customOption: e.target.value

&nbsp;   })}

&nbsp; />

</div>

```



---



\## よくあるカスタマイズパターン



\### パターン1: メッセージの見た目を変える

→ `src/app/components/ChatMessage.tsx` を編集



\### パターン2: 新しいボタンやメニューを追加

→ `src/app/page.tsx` のヘッダー部分を編集



\### パターン3: エージェントから送られてくる新しいデータを表示

→ 1. `useChat.ts`の`StateType`に型を追加

→ 2. `ChatInterface.tsx`で`useChatContext()`から取得して表示



\### パターン4: サイドバーに新しいタブを追加

→ 1. 新しいコンポーネントを`src/app/components/`に作成

→ 2. `page.tsx`の`ResizablePanelGroup`に追加



\### パターン5: ファイル以外のデータソースを追加

→ 1. `src/app/hooks/`に新しいhookを作成

→ 2. 対応するコンポーネントで使用



---



\## デバッグのコツ



\### 1. コンソールでデータを確認する



```typescript

// useChat hookで受信しているデータを確認

const { messages, todos, files } = useChatContext();

console.log('Messages:', messages);

console.log('Todos:', todos);

console.log('Files:', files);

```



\### 2. React Developer Toolsを使う



ブラウザの拡張機能をインストールすると、Reactの状態やPropsが見えるようになります。



\### 3. ネットワークタブで通信を確認



\- ブラウザの開発者ツール → ネットワークタブ

\- LangGraph APIへのリクエストや、ファイルAPIへのリクエストが見える



---



\## まとめ



Deep Agent UIの構造をまとめると:



1\. \*\*Next.js + React\*\*: モダンなフロントエンドフレームワーク

2\. \*\*Provider パターン\*\*: Context APIで状態を共有

3\. \*\*Custom Hooks\*\*: ロジックをコンポーネントから分離

4\. \*\*LangGraph SDK\*\*: エージェントとのストリーミング通信

5\. \*\*ファイルAPI\*\*: ファイルシステムとの連携



\### 初心者が最初に触るべきファイル



1\. `src/app/components/ChatInterface.tsx` - チャットのUIを理解

2\. `src/app/hooks/useChat.ts` - データの流れを理解

3\. `src/app/page.tsx` - 全体のレイアウトを理解

4\. `tailwind.config.mjs` - 見た目のカスタマイズ



これらのファイルから読み始めて、少しずつカスタマイズしていくと理解が深まります！

