\# バックエンドアーキテクチャガイド



\## 概要



バックエンドは \*\*Python 3.13\*\* で構築され、\*\*FastAPI\*\* (ファイルAPI) と \*\*LangGraph\*\* (AIエージェントランタイム) の2つのサーバーから構成されています。DeepAgentsフレームワークを使用して、高度なAIエージェント機能 (長期記憶、スキルシステム、ツール承認など) を提供します。



\## 目次



1\. \[プロジェクト構成](#プロジェクト構成)

2\. \[アーキテクチャ概要](#アーキテクチャ概要)

3\. \[FastAPI サーバー](#fastapi-サーバー)

4\. \[LangGraph エージェント](#langgraph-エージェント)

5\. \[コアサービス](#コアサービス)

6\. \[ミドルウェア](#ミドルウェア)

7\. \[開発ワークフロー](#開発ワークフロー)



\## プロジェクト構成



```

backend/

├── backend\_agent\_main.py         # LangGraphエージェント定義 (546行)

├── file\_main.py                  # FastAPIサーバー (550行)

├── test.py                       # テストスイート (18,682行)

├── pyproject.toml                # 依存関係定義

├── uv.lock                       # ロックファイル

├── langgraph.json                # LangGraph設定

├── deepagents\_cli/               # コアライブラリ

│   ├── agent.py                  # エージェント作成 (466行)

│   ├── agent\_memory.py           # 長期記憶システム (327行)

│   ├── config.py                 # 設定と定数 (414行)

│   ├── execution.py              # 実行エンジン (681行)

│   ├── file\_ops.py               # ファイル操作 (441行)

│   ├── input.py                  # ユーザー入力 (322行)

│   ├── main.py                   # CLI エントリー (431行)

│   ├── shell.py                  # シェル実行 (137行)

│   ├── tools.py                  # カスタムツール (182行)

│   ├── ui.py                     # CLI UI (638行)

│   ├── skills/                   # スキルシステム

│   │   ├── middleware.py         # スキルミドルウェア

│   │   ├── commands.py           # スキルコマンド

│   │   └── load.py               # スキルローダー

│   └── default\_agent\_prompt\*.md  # デフォルトプロンプト

├── file\_api/                     # ファイルAPI

│   ├── config.py                 # API設定

│   ├── file\_watcher.py           # ファイル監視

│   └── cloud\_storage.py          # GCS統合

└── workspace/                    # エージェント作業ディレクトリ

```



\## アーキテクチャ概要



\### サーバー構成



```

\[ブラウザ/CLI]

&nbsp;    ↓

\[FastAPI Server - Port 8080/8124]

&nbsp;    ↓ (プロキシ /agent/\*)

\[LangGraph Server - Port 2024]

&nbsp;    ↓

\[DeepAgents エージェント]

&nbsp;    ↓

\[ミドルウェアスタック]

&nbsp; - AgentMemoryMiddleware

&nbsp; - SkillsMiddleware

&nbsp; - ShellMiddleware

&nbsp; - InterruptOnConfig

&nbsp;    ↓

\[LLM (Claude/Gemini)]

```



\### データフロー



1\. \*\*ユーザーリクエスト\*\* → FastAPI

2\. \*\*プロキシ\*\* → LangGraph Server

3\. \*\*エージェント実行\*\* → ミドルウェア処理

4\. \*\*LLM呼び出し\*\* → Claude/Gemini API

5\. \*\*レスポンス\*\* → ストリーミング (SSE) → フロントエンド



\## FastAPI サーバー



\*\*エントリーポイント\*\*: `backend/file\_main.py:1`



\### 主要機能



1\. \*\*LangGraph プロキシ\*\* - LangGraph APIへのリクエストを転送

2\. \*\*ファイルAPI\*\* - ファイルシステム操作

3\. \*\*WebSocket\*\* - リアルタイムファイルイベント

4\. \*\*CORS\*\* - クロスオリジン対応



\### 初期化



\*\*場所\*\*: `backend/file\_main.py:1-37`



```python

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from file\_api.config import settings

from file\_api.file\_watcher import FileWatcher

from file\_api.cloud\_storage import ensure\_agent\_config



app = FastAPI()



\# CORS設定

app.add\_middleware(

&nbsp;   CORSMiddleware,

&nbsp;   allow\_origins=settings.cors\_origins,

&nbsp;   allow\_credentials=True,

&nbsp;   allow\_methods=\["\*"],

&nbsp;   allow\_headers=\["\*"]

)



\# 起動時処理

@app.on\_event("startup")

async def startup\_event():

&nbsp;   # GCSから設定をダウンロード

&nbsp;   await ensure\_agent\_config()

&nbsp;   # ファイルウォッチャー起動

&nbsp;   file\_watcher.start()

```



\### LangGraph プロキシ



\*\*場所\*\*: `backend/file\_main.py:45-200`



すべての `/agent/\*` リクエストをLangGraph Server (Port 2024) に転送します。



\*\*実装\*\*:

```python

@app.api\_route("/agent/{path:path}", methods=\["GET", "POST", "PUT", "DELETE", "PATCH"])

async def proxy\_langgraph(path: str, request: Request):

&nbsp;   langgraph\_url = f"http://localhost:2024/{path}"



&nbsp;   # GETリクエストをPOSTに変換 (threads検索用)

&nbsp;   if request.method == "GET" and path == "threads":

&nbsp;       langgraph\_url = f"http://localhost:2024/threads/search"

&nbsp;       method = "POST"

&nbsp;   else:

&nbsp;       method = request.method



&nbsp;   # ヘッダーとボディを転送

&nbsp;   headers = dict(request.headers)

&nbsp;   body = await request.body()



&nbsp;   # ストリーミングレスポンス対応

&nbsp;   async with httpx.AsyncClient() as client:

&nbsp;       response = await client.request(

&nbsp;           method,

&nbsp;           langgraph\_url,

&nbsp;           headers=headers,

&nbsp;           content=body,

&nbsp;           timeout=None

&nbsp;       )



&nbsp;       # Server-Sent Events (SSE) の場合はストリーミング

&nbsp;       if "text/event-stream" in response.headers.get("content-type", ""):

&nbsp;           return StreamingResponse(

&nbsp;               response.aiter\_bytes(),

&nbsp;               media\_type="text/event-stream"

&nbsp;           )

&nbsp;       else:

&nbsp;           return Response(

&nbsp;               content=response.content,

&nbsp;               status\_code=response.status\_code,

&nbsp;               headers=dict(response.headers)

&nbsp;           )

```



\*\*重要なポイント\*\*:

\- `GET /agent/threads` → `POST /agent/threads/search` に変換

\- SSE (Server-Sent Events) ストリーミング対応

\- タイムアウトなし (`timeout=None`)



\### ファイルAPI エンドポイント



\#### 1. ファイルリスト取得



\*\*場所\*\*: `backend/file\_main.py:211-268`



```python

@app.get("/api/files")

async def list\_files(path: str = ""):

&nbsp;   """

&nbsp;   指定パスのファイル/ディレクトリリストを返す

&nbsp;   """

&nbsp;   base\_path = settings.watch\_dir

&nbsp;   target\_path = os.path.join(base\_path, path)



&nbsp;   if not os.path.exists(target\_path):

&nbsp;       raise HTTPException(status\_code=404, detail="Path not found")



&nbsp;   files = \[]

&nbsp;   for item in os.listdir(target\_path):

&nbsp;       item\_path = os.path.join(target\_path, item)

&nbsp;       stat = os.stat(item\_path)



&nbsp;       files.append({

&nbsp;           "name": item,

&nbsp;           "path": os.path.relpath(item\_path, base\_path),

&nbsp;           "type": "directory" if os.path.isdir(item\_path) else "file",

&nbsp;           "size": stat.st\_size if os.path.isfile(item\_path) else None,

&nbsp;           "modifiedAt": datetime.fromtimestamp(stat.st\_mtime).isoformat()

&nbsp;       })



&nbsp;   return files

```



\#### 2. ファイル読み取り



\*\*場所\*\*: `backend/file\_main.py:268-348`



```python

@app.get("/api/files/{file\_path:path}")

async def read\_file(file\_path: str, raw: bool = False):

&nbsp;   """

&nbsp;   ファイル内容を返す (オプションでシンタックスハイライト)

&nbsp;   """

&nbsp;   full\_path = os.path.join(settings.watch\_dir, file\_path)



&nbsp;   if not os.path.exists(full\_path):

&nbsp;       raise HTTPException(status\_code=404, detail="File not found")



&nbsp;   with open(full\_path, "r", encoding="utf-8") as f:

&nbsp;       content = f.read()



&nbsp;   if raw:

&nbsp;       return {"content": content}



&nbsp;   # 言語検出とシンタックスハイライト

&nbsp;   language = detect\_language(file\_path)



&nbsp;   return {

&nbsp;       "content": content,

&nbsp;       "language": language,

&nbsp;       "path": file\_path

&nbsp;   }

```



\#### 3. ファイル更新/作成



\*\*場所\*\*: `backend/file\_main.py:348-394`



```python

@app.put("/api/files/{file\_path:path}")

async def update\_file(file\_path: str, request: FileUpdateRequest):

&nbsp;   """

&nbsp;   ファイルを作成または更新

&nbsp;   """

&nbsp;   full\_path = os.path.join(settings.watch\_dir, file\_path)



&nbsp;   # ディレクトリを作成

&nbsp;   os.makedirs(os.path.dirname(full\_path), exist\_ok=True)



&nbsp;   # ファイルに書き込み

&nbsp;   with open(full\_path, "w", encoding="utf-8") as f:

&nbsp;       f.write(request.content)



&nbsp;   return {"success": True, "path": file\_path}

```



\#### 4. ファイル削除



\*\*場所\*\*: `backend/file\_main.py:394-435`



```python

@app.delete("/api/files/{file\_path:path}")

async def delete\_file(file\_path: str):

&nbsp;   """

&nbsp;   ファイルまたはディレクトリを削除

&nbsp;   """

&nbsp;   full\_path = os.path.join(settings.watch\_dir, file\_path)



&nbsp;   if not os.path.exists(full\_path):

&nbsp;       raise HTTPException(status\_code=404, detail="File not found")



&nbsp;   if os.path.isdir(full\_path):

&nbsp;       shutil.rmtree(full\_path)

&nbsp;   else:

&nbsp;       os.remove(full\_path)



&nbsp;   return {"success": True}

```



\#### 5. ファイルアップロード



\*\*場所\*\*: `backend/file\_main.py:435-491`



```python

@app.post("/api/files/upload")

async def upload\_files(files: List\[UploadFile], targetPath: str = ""):

&nbsp;   """

&nbsp;   複数ファイルをアップロード

&nbsp;   """

&nbsp;   target\_dir = os.path.join(settings.watch\_dir, targetPath)

&nbsp;   os.makedirs(target\_dir, exist\_ok=True)



&nbsp;   uploaded = \[]

&nbsp;   for file in files:

&nbsp;       file\_path = os.path.join(target\_dir, file.filename)



&nbsp;       with open(file\_path, "wb") as f:

&nbsp;           content = await file.read()

&nbsp;           f.write(content)



&nbsp;       uploaded.append({

&nbsp;           "filename": file.filename,

&nbsp;           "path": os.path.relpath(file\_path, settings.watch\_dir)

&nbsp;       })



&nbsp;   return {"uploaded": uploaded}

```



\### WebSocket エンドポイント



\*\*場所\*\*: `backend/file\_main.py:491+`



リアルタイムファイルシステムイベントをクライアントに通知します。



```python

@app.websocket("/ws")

async def websocket\_endpoint(websocket: WebSocket):

&nbsp;   await websocket.accept()



&nbsp;   # ファイルイベントリスナーを登録

&nbsp;   async def send\_event(event\_type: str, path: str, data: Any = None):

&nbsp;       await websocket.send\_json({

&nbsp;           "type": event\_type,

&nbsp;           "path": path,

&nbsp;           "data": data

&nbsp;       })



&nbsp;   file\_watcher.add\_listener(send\_event)



&nbsp;   try:

&nbsp;       # 接続を維持

&nbsp;       while True:

&nbsp;           await websocket.receive\_text()

&nbsp;   except WebSocketDisconnect:

&nbsp;       file\_watcher.remove\_listener(send\_event)

```



\*\*イベントタイプ\*\*:

\- `created` - ファイル/ディレクトリ作成

\- `modified` - ファイル変更

\- `deleted` - ファイル/ディレクトリ削除

\- `moved` - ファイル移動



\### 設定



\*\*場所\*\*: `backend/file\_api/config.py`



```python

class Settings:

&nbsp;   watch\_dir: str = os.getenv("WATCH\_DIR", "/app/workspace")

&nbsp;   cors\_origins: List\[str] = os.getenv("CORS\_ORIGINS", "\*").split(",")

&nbsp;   max\_file\_size: int = 10 \* 1024 \* 1024  # 10MB



settings = Settings()

```



\## LangGraph エージェント



\*\*エントリーポイント\*\*: `backend/backend\_agent\_main.py:1`



\### エージェント定義



\*\*場所\*\*: `backend/backend\_agent\_main.py:73-100`



```python

from deepagents\_cli.agent import create\_deep\_agent

from deepagents\_cli.agent\_memory import AgentMemoryMiddleware

from deepagents\_cli.skills.middleware import SkillsMiddleware

from deepagents\_cli.shell import ShellMiddleware

from langgraph.checkpoint.memory import InMemorySaver



\# カスタムバックエンド (UIファイル追跡用)

class CustomFilesystemBackend(FilesystemBackend):

&nbsp;   def files\_update(self, files: Dict\[str, str]) -> Dict\[str, str]:

&nbsp;       """LangGraph UIにファイル変更を通知"""

&nbsp;       return {"files": files}



\# エージェント作成

agent = create\_deep\_agent(

&nbsp;   recursion\_limit=1000,

&nbsp;   checkpointer=InMemorySaver(),

&nbsp;   backends=\[CustomFilesystemBackend(), CompositeBackend()],

&nbsp;   middlewares=\[

&nbsp;       ShellMiddleware(),

&nbsp;       SkillsMiddleware(),

&nbsp;       AgentMemoryMiddleware(),

&nbsp;       InterruptOnConfig()

&nbsp;   ]

)

```



\*\*エクスポート\*\*: `agent` グラフオブジェクトは `langgraph.json` で参照されます。



\### LangGraph 設定



\*\*場所\*\*: `backend/langgraph.json`



```json

{

&nbsp; "python\_version": "3.13",

&nbsp; "graphs": {

&nbsp;   "agent": "./backend\_agent\_main.py:agent"

&nbsp; },

&nbsp; "env": ".env"

}

```



\### エージェント状態



LangGraphエージェントは以下の状態を管理します:



```python

class AgentState(TypedDict):

&nbsp;   messages: List\[Message]              # 会話履歴

&nbsp;   todos: List\[TodoItem]                # タスク追跡

&nbsp;   files: Dict\[str, str]                # ファイル辞書 (path → content)

&nbsp;   email: Optional\[EmailObject]         # メールメタデータ

&nbsp;   ui: Optional\[Any]                    # カスタムUI状態

```



\*\*状態更新\*\*:

\- `messages`: 新しいメッセージを追加

\- `todos`: タスクステータスを更新

\- `files`: ファイル読み取り/書き込み時に更新

\- `ui`: カスタムUIコンポーネントのデータ



\## コアサービス



\### 1. Agent - エージェント作成



\*\*場所\*\*: `backend/deepagents\_cli/agent.py:1`

\*\*行数\*\*: 466行



\*\*主要関数\*\*: `create\_deep\_agent()`



```python

def create\_deep\_agent(

&nbsp;   recursion\_limit: int = 1000,

&nbsp;   checkpointer: Checkpointer = None,

&nbsp;   backends: List\[Backend] = None,

&nbsp;   middlewares: List\[Middleware] = None,

&nbsp;   tools: List\[Tool] = None

) -> CompiledGraph:

&nbsp;   """

&nbsp;   DeepAgentsエージェントを作成



&nbsp;   Args:

&nbsp;       recursion\_limit: 最大再帰深度

&nbsp;       checkpointer: 状態永続化 (InMemorySaver, SqliteSaver, など)

&nbsp;       backends: ファイルシステム/データベースバックエンド

&nbsp;       middlewares: ミドルウェアスタック

&nbsp;       tools: カスタムツール



&nbsp;   Returns:

&nbsp;       コンパイル済みLangGraphグラフ

&nbsp;   """

&nbsp;   # エージェントグラフを構築

&nbsp;   graph = create\_graph(

&nbsp;       agent\_state=AgentState,

&nbsp;       tools=tools or default\_tools,

&nbsp;       middlewares=middlewares or \[]

&nbsp;   )



&nbsp;   # コンパイル

&nbsp;   compiled = graph.compile(

&nbsp;       checkpointer=checkpointer,

&nbsp;       interrupt\_before=\["tools"]  # ツール実行前に中断

&nbsp;   )



&nbsp;   return compiled

```



\*\*使用例\*\*:

```python

from langgraph.checkpoint.memory import InMemorySaver



agent = create\_deep\_agent(

&nbsp;   recursion\_limit=500,

&nbsp;   checkpointer=InMemorySaver(),

&nbsp;   middlewares=\[AgentMemoryMiddleware(), SkillsMiddleware()]

)

```



\### 2. Agent Memory - 長期記憶システム



\*\*場所\*\*: `backend/deepagents\_cli/agent\_memory.py:1`

\*\*行数\*\*: 327行



\*\*ミドルウェアクラス\*\*: `AgentMemoryMiddleware`



```python

class AgentMemoryMiddleware:

&nbsp;   """

&nbsp;   エージェントに長期記憶を注入するミドルウェア



&nbsp;   記憶の階層:

&nbsp;   1. エンタープライズレベル: /enterprise/.deepagents/agent.md

&nbsp;   2. プロジェクトレベル: {project\_root}/.deepagents/agent.md

&nbsp;   3. ユーザーレベル: ~/.deepagents/{agent\_name}/agent.md

&nbsp;   """



&nbsp;   def \_\_init\_\_(self, agent\_name: str = "agent"):

&nbsp;       self.agent\_name = agent\_name

&nbsp;       self.enterprise\_memory = self.\_load\_enterprise\_memory()

&nbsp;       self.project\_memory = self.\_load\_project\_memory()

&nbsp;       self.user\_memory = self.\_load\_user\_memory()



&nbsp;   def \_load\_user\_memory(self) -> str:

&nbsp;       """ユーザーレベル記憶を読み込み"""

&nbsp;       path = Path.home() / ".deepagents" / self.agent\_name / "agent.md"

&nbsp;       if path.exists():

&nbsp;           return path.read\_text()

&nbsp;       return ""



&nbsp;   def \_load\_project\_memory(self) -> str:

&nbsp;       """プロジェクトレベル記憶を読み込み"""

&nbsp;       git\_root = find\_git\_root()

&nbsp;       if git\_root:

&nbsp;           path = git\_root / ".deepagents" / "agent.md"

&nbsp;           if path.exists():

&nbsp;               return path.read\_text()

&nbsp;       return ""



&nbsp;   def inject\_memory(self, messages: List\[Message]) -> List\[Message]:

&nbsp;       """システムメッセージに記憶を注入"""

&nbsp;       memory\_content = "\\n\\n".join(\[

&nbsp;           self.enterprise\_memory,

&nbsp;           self.project\_memory,

&nbsp;           self.user\_memory

&nbsp;       ]).strip()



&nbsp;       if memory\_content:

&nbsp;           # 最初のシステムメッセージに追加

&nbsp;           messages\[0]\["content"] += f"\\n\\n# Long-term Memory\\n\\n{memory\_content}"



&nbsp;       return messages

```



\*\*記憶ファイル例\*\*:

```markdown

---

agent: agent

version: 1.0

---



\# プロジェクト記憶



このプロジェクトは...



\## 重要な制約

\- Python 3.13を使用

\- テストは pytest で実行



\## コーディング規約

\- Black でフォーマット

\- 型ヒントを使用

```



\### 3. Skills - スキルシステム



\*\*場所\*\*: `backend/deepagents\_cli/skills/`



\#### スキルミドルウェア



\*\*場所\*\*: `backend/deepagents\_cli/skills/middleware.py`



```python

class SkillsMiddleware:

&nbsp;   """

&nbsp;   スキルを動的にロードしてプロンプトに注入



&nbsp;   スキルの場所:

&nbsp;   - ユーザーレベル: ~/.deepagents/{agent}/skills/

&nbsp;   - プロジェクトレベル: .deepagents/skills/

&nbsp;   """



&nbsp;   def \_\_init\_\_(self, agent\_name: str = "agent"):

&nbsp;       self.agent\_name = agent\_name

&nbsp;       self.skills = self.\_load\_skills()



&nbsp;   def \_load\_skills(self) -> List\[Skill]:

&nbsp;       """すべてのスキルを読み込み"""

&nbsp;       skills = \[]



&nbsp;       # ユーザーレベルスキル

&nbsp;       user\_skills\_dir = Path.home() / ".deepagents" / self.agent\_name / "skills"

&nbsp;       skills.extend(load\_skills\_from\_dir(user\_skills\_dir))



&nbsp;       # プロジェクトレベルスキル

&nbsp;       git\_root = find\_git\_root()

&nbsp;       if git\_root:

&nbsp;           project\_skills\_dir = git\_root / ".deepagents" / "skills"

&nbsp;           skills.extend(load\_skills\_from\_dir(project\_skills\_dir))



&nbsp;       return skills



&nbsp;   def inject\_skills(self, messages: List\[Message]) -> List\[Message]:

&nbsp;       """スキルメタデータをシステムプロンプトに注入"""

&nbsp;       skill\_descriptions = \[]



&nbsp;       for skill in self.skills:

&nbsp;           skill\_descriptions.append(f"- \*\*{skill.name}\*\*: {skill.description}")



&nbsp;       skills\_content = "\\n".join(skill\_descriptions)

&nbsp;       messages\[0]\["content"] += f"\\n\\n# Available Skills\\n\\n{skills\_content}"



&nbsp;       return messages

```



\#### スキルローダー



\*\*場所\*\*: `backend/deepagents\_cli/skills/load.py`



```python

def load\_skills\_from\_dir(skills\_dir: Path) -> List\[Skill]:

&nbsp;   """ディレクトリからスキルを読み込み"""

&nbsp;   skills = \[]



&nbsp;   if not skills\_dir.exists():

&nbsp;       return skills



&nbsp;   for skill\_dir in skills\_dir.iterdir():

&nbsp;       if not skill\_dir.is\_dir():

&nbsp;           continue



&nbsp;       skill\_file = skill\_dir / "SKILL.md"

&nbsp;       if not skill\_file.exists():

&nbsp;           continue



&nbsp;       # YAMLフロントマターを解析

&nbsp;       content = skill\_file.read\_text()

&nbsp;       metadata, body = parse\_frontmatter(content)



&nbsp;       skills.append(Skill(

&nbsp;           name=metadata.get("name", skill\_dir.name),

&nbsp;           description=metadata.get("description", ""),

&nbsp;           content=body,

&nbsp;           path=skill\_dir

&nbsp;       ))



&nbsp;   return skills

```



\*\*スキルファイル例\*\* (`auto-brainstorming/SKILL.md`):

```markdown

---

name: auto-brainstorming

description: Automated brainstorming for creative ideas

---



\# Auto Brainstorming Skill



This skill helps you brainstorm ideas...



\## Usage



Use this skill when...

```



\### 4. Execution - 実行エンジン



\*\*場所\*\*: `backend/deepagents\_cli/execution.py:1`

\*\*行数\*\*: 681行



\*\*主要関数\*\*: `execute\_task()`



```python

async def execute\_task(

&nbsp;   agent: CompiledGraph,

&nbsp;   thread\_id: str,

&nbsp;   user\_input: str,

&nbsp;   config: Dict\[str, Any]

) -> AsyncIterator\[StreamEvent]:

&nbsp;   """

&nbsp;   タスクを実行してイベントをストリーミング



&nbsp;   Args:

&nbsp;       agent: コンパイル済みエージェント

&nbsp;       thread\_id: スレッドID

&nbsp;       user\_input: ユーザー入力

&nbsp;       config: 実行設定



&nbsp;   Yields:

&nbsp;       StreamEvent: イベント (メッセージ、ツール呼び出し、中断、など)

&nbsp;   """

&nbsp;   # 初期メッセージ

&nbsp;   messages = \[{"role": "human", "content": user\_input}]



&nbsp;   # エージェント実行 (ストリーミング)

&nbsp;   async for event in agent.astream\_events(

&nbsp;       {"messages": messages},

&nbsp;       config={"configurable": {"thread\_id": thread\_id}, \*\*config}

&nbsp;   ):

&nbsp;       # イベントタイプに応じて処理

&nbsp;       if event\["event"] == "on\_chat\_model\_stream":

&nbsp;           # LLMトークンストリーム

&nbsp;           yield {"type": "token", "content": event\["data"]\["chunk"]}



&nbsp;       elif event\["event"] == "on\_tool\_start":

&nbsp;           # ツール実行開始

&nbsp;           yield {"type": "tool\_start", "name": event\["name"], "args": event\["data"]}



&nbsp;       elif event\["event"] == "on\_tool\_end":

&nbsp;           # ツール実行完了

&nbsp;           yield {"type": "tool\_end", "name": event\["name"], "result": event\["data"]}



&nbsp;       elif event\["event"] == "\_\_interrupt\_\_":

&nbsp;           # Human-in-the-Loop中断

&nbsp;           yield {"type": "interrupt", "data": event\["data"]}

```



\*\*ツール承認処理\*\*:

```python

def prompt\_for\_tool\_approval(tool\_call: ToolCall) -> bool:

&nbsp;   """

&nbsp;   対話的にツール実行を承認



&nbsp;   Returns:

&nbsp;       True: 承認, False: 拒否

&nbsp;   """

&nbsp;   # ツール詳細を表示

&nbsp;   print(f"\\n{Colors.YELLOW}Tool Approval Required{Colors.RESET}")

&nbsp;   print(f"Tool: {tool\_call\['name']}")

&nbsp;   print(f"Args: {json.dumps(tool\_call\['args'], indent=2)}")



&nbsp;   # ファイル操作の場合、差分を表示

&nbsp;   if tool\_call\["name"] in \["edit\_file", "write\_file"]:

&nbsp;       show\_file\_diff(tool\_call)



&nbsp;   # 承認プロンプト

&nbsp;   choices = \["Approve", "Reject", "Auto-approve all"]

&nbsp;   selected = prompt\_with\_arrow\_keys(choices)



&nbsp;   if selected == "Approve":

&nbsp;       return True

&nbsp;   elif selected == "Auto-approve all":

&nbsp;       # 以降すべて自動承認

&nbsp;       set\_auto\_approve(True)

&nbsp;       return True

&nbsp;   else:

&nbsp;       return False

```



\### 5. File Operations - ファイル操作



\*\*場所\*\*: `backend/deepagents\_cli/file\_ops.py:1`

\*\*行数\*\*: 441行



\*\*主要クラス\*\*: `ApprovalPreview`



```python

class ApprovalPreview:

&nbsp;   """HITL承認用のプレビューデータ"""



&nbsp;   tool\_name: str

&nbsp;   args: Dict\[str, Any]

&nbsp;   preview: str  # 差分やファイル内容



def build\_approval\_preview(tool\_call: ToolCall) -> ApprovalPreview:

&nbsp;   """ツール呼び出しの承認プレビューを生成"""

&nbsp;   if tool\_call\["name"] == "edit\_file":

&nbsp;       # ファイル編集の差分を計算

&nbsp;       old\_content = read\_file(tool\_call\["args"]\["file\_path"])

&nbsp;       new\_content = apply\_edit(old\_content, tool\_call\["args"])

&nbsp;       diff = compute\_unified\_diff(old\_content, new\_content)



&nbsp;       return ApprovalPreview(

&nbsp;           tool\_name="edit\_file",

&nbsp;           args=tool\_call\["args"],

&nbsp;           preview=diff

&nbsp;       )

&nbsp;   # ... 他のツール

```



\*\*差分計算\*\*:

```python

def compute\_unified\_diff(old: str, new: str, filename: str = "file") -> str:

&nbsp;   """Unified diff形式の差分を計算"""

&nbsp;   import difflib



&nbsp;   old\_lines = old.splitlines(keepends=True)

&nbsp;   new\_lines = new.splitlines(keepends=True)



&nbsp;   diff = difflib.unified\_diff(

&nbsp;       old\_lines,

&nbsp;       new\_lines,

&nbsp;       fromfile=f"a/{filename}",

&nbsp;       tofile=f"b/{filename}",

&nbsp;       lineterm=""

&nbsp;   )



&nbsp;   return "".join(diff)

```



\### 6. Tools - カスタムツール



\*\*場所\*\*: `backend/deepagents\_cli/tools.py:1`

\*\*行数\*\*: 182行



\*\*定義済みツール\*\*:



```python

@tool

def http\_request(

&nbsp;   url: str,

&nbsp;   method: str = "GET",

&nbsp;   headers: Optional\[Dict\[str, str]] = None,

&nbsp;   params: Optional\[Dict\[str, str]] = None,

&nbsp;   json\_body: Optional\[Dict\[str, Any]] = None,

&nbsp;   timeout: int = 30

) -> str:

&nbsp;   """

&nbsp;   HTTPリクエストを実行



&nbsp;   Args:

&nbsp;       url: リクエストURL

&nbsp;       method: HTTPメソッド (GET, POST, PUT, DELETE)

&nbsp;       headers: リクエストヘッダー

&nbsp;       params: クエリパラメータ

&nbsp;       json\_body: JSONボディ

&nbsp;       timeout: タイムアウト (秒)



&nbsp;   Returns:

&nbsp;       レスポンスボディ (JSON文字列)

&nbsp;   """

&nbsp;   import requests



&nbsp;   response = requests.request(

&nbsp;       method=method,

&nbsp;       url=url,

&nbsp;       headers=headers,

&nbsp;       params=params,

&nbsp;       json=json\_body,

&nbsp;       timeout=timeout

&nbsp;   )



&nbsp;   response.raise\_for\_status()

&nbsp;   return response.text





@tool

def fetch\_url(url: str) -> str:

&nbsp;   """

&nbsp;   URLからHTMLを取得してMarkdownに変換



&nbsp;   Args:

&nbsp;       url: 取得するURL



&nbsp;   Returns:

&nbsp;       Markdown形式のコンテンツ

&nbsp;   """

&nbsp;   import requests

&nbsp;   from markdownify import markdownify



&nbsp;   response = requests.get(url, timeout=30)

&nbsp;   response.raise\_for\_status()



&nbsp;   # HTMLをMarkdownに変換

&nbsp;   markdown = markdownify(response.text)

&nbsp;   return markdown

```



\*\*ツール追加方法\*\*:

```python

from langchain.tools import tool



@tool

def my\_custom\_tool(arg1: str, arg2: int) -> str:

&nbsp;   """

&nbsp;   カスタムツールの説明



&nbsp;   Args:

&nbsp;       arg1: 引数1の説明

&nbsp;       arg2: 引数2の説明



&nbsp;   Returns:

&nbsp;       戻り値の説明

&nbsp;   """

&nbsp;   # ツールロジック

&nbsp;   result = do\_something(arg1, arg2)

&nbsp;   return result



\# エージェント作成時に追加

agent = create\_deep\_agent(tools=\[my\_custom\_tool])

```



\### 7. Shell - シェル実行



\*\*場所\*\*: `backend/deepagents\_cli/shell.py:1`

\*\*行数\*\*: 137行



\*\*ミドルウェアクラス\*\*: `ShellMiddleware`



```python

class ShellMiddleware:

&nbsp;   """シェルコマンド実行ミドルウェア"""



&nbsp;   def execute\_command(self, command: str, cwd: str = None) -> str:

&nbsp;       """

&nbsp;       シェルコマンドを実行



&nbsp;       Args:

&nbsp;           command: 実行するコマンド

&nbsp;           cwd: 作業ディレクトリ



&nbsp;       Returns:

&nbsp;           コマンド出力

&nbsp;       """

&nbsp;       import subprocess



&nbsp;       result = subprocess.run(

&nbsp;           command,

&nbsp;           shell=True,

&nbsp;           cwd=cwd,

&nbsp;           capture\_output=True,

&nbsp;           text=True,

&nbsp;           timeout=300

&nbsp;       )



&nbsp;       if result.returncode != 0:

&nbsp;           raise Exception(f"Command failed: {result.stderr}")



&nbsp;       return result.stdout

```



\*\*使用例\*\*:

```python

\# エージェントプロンプトから

"Run the command: `ls -la`"



\# ShellMiddlewareが自動的に実行

```



\## ミドルウェア



\### ミドルウェアスタック



ミドルウェアは以下の順序で実行されます:



```python

middlewares = \[

&nbsp;   ShellMiddleware(),           # 1. シェルコマンド実行

&nbsp;   SkillsMiddleware(),          # 2. スキル注入

&nbsp;   AgentMemoryMiddleware(),     # 3. 長期記憶注入

&nbsp;   InterruptOnConfig()          # 4. ツール承認

]

```



\### カスタムミドルウェア作成



```python

class MyCustomMiddleware:

&nbsp;   """カスタムミドルウェア"""



&nbsp;   def \_\_init\_\_(self, config: Dict\[str, Any]):

&nbsp;       self.config = config



&nbsp;   async def \_\_call\_\_(

&nbsp;       self,

&nbsp;       messages: List\[Message],

&nbsp;       config: RunnableConfig

&nbsp;   ) -> List\[Message]:

&nbsp;       """

&nbsp;       ミドルウェアロジック



&nbsp;       Args:

&nbsp;           messages: 現在のメッセージリスト

&nbsp;           config: ランタイム設定



&nbsp;       Returns:

&nbsp;           変更後のメッセージリスト

&nbsp;       """

&nbsp;       # メッセージに何かを追加

&nbsp;       messages.append({

&nbsp;           "role": "system",

&nbsp;           "content": "Custom middleware message"

&nbsp;       })



&nbsp;       return messages

```



\*\*追加方法\*\*:

```python

agent = create\_deep\_agent(

&nbsp;   middlewares=\[

&nbsp;       MyCustomMiddleware(config={"key": "value"}),

&nbsp;       # ... 他のミドルウェア

&nbsp;   ]

)

```



\## 開発ワークフロー



\### セットアップ



```bash

cd backend



\# UV パッケージマネージャーで依存関係をインストール

uv sync --locked

```



\### 開発サーバー起動



\*\*FastAPI サーバー\*\*:

```bash

uv run python file\_main.py

```



\*\*LangGraph サーバー\*\*:

```bash

uv run langgraph dev --allow-blocking --host 0.0.0.0 --port 2024

```



\*\*または両方同時に (Docker Compose)\*\*:

```bash

cd ..

docker compose up backend

```



\### CLI モード



```bash

\# 対話モード

uv run deepagents-cli



\# コマンド

uv run deepagents-cli list      # エージェント一覧

uv run deepagents-cli reset     # エージェントリセット

uv run deepagents-cli skills    # スキル管理

uv run deepagents-cli help      # ヘルプ

```



\### テスト実行



```bash

uv run python test.py

```



\### 依存関係管理



\*\*追加\*\*:

```bash

uv add <package-name>

```



\*\*削除\*\*:

```bash

uv remove <package-name>

```



\*\*更新\*\*:

```bash

uv sync

```



\## API開発



\### 新しいエンドポイントを追加



1\. \*\*`file\_main.py` にエンドポイント関数を追加\*\*:

```python

@app.get("/api/my-endpoint")

async def my\_endpoint(param: str):

&nbsp;   """エンドポイントの説明"""

&nbsp;   # ロジック

&nbsp;   return {"result": "success"}

```



2\. \*\*フロントエンドから呼び出し\*\*:

```typescript

const response = await fetch("/api/my-endpoint?param=value")

const data = await response.json()

```



\## ツール開発



\### 新しいツールを追加



1\. \*\*`tools.py` にツール関数を追加\*\*:

```python

@tool

def my\_new\_tool(input\_text: str) -> str:

&nbsp;   """

&nbsp;   ツールの説明



&nbsp;   Args:

&nbsp;       input\_text: 入力テキスト



&nbsp;   Returns:

&nbsp;       処理結果

&nbsp;   """

&nbsp;   # ツールロジック

&nbsp;   result = process(input\_text)

&nbsp;   return result

```



2\. \*\*`backend\_agent\_main.py` でツールを登録\*\*:

```python

from deepagents\_cli.tools import my\_new\_tool



agent = create\_deep\_agent(

&nbsp;   tools=\[my\_new\_tool]

)

```



\## スキル開発



\### 新しいスキルを作成



1\. \*\*スキルディレクトリを作成\*\*:

```bash

mkdir -p agent\_config/.deepagents/agent/skills/my-skill

```



2\. \*\*`SKILL.md` ファイルを作成\*\*:

```markdown

---

name: my-skill

description: My custom skill for...

---



\# My Custom Skill



This skill helps you...



\## When to Use



Use this skill when...



\## Example



User: "Do something with my-skill"

Assistant: \[Uses this skill to...]

```



3\. \*\*再起動して確認\*\*:

```bash

uv run deepagents-cli skills

```



\## ミドルウェア開発



\### 新しいミドルウェアを追加



1\. \*\*`deepagents\_cli/` に新しいファイルを作成\*\*:

```bash

touch backend/deepagents\_cli/my\_middleware.py

```



2\. \*\*ミドルウェアクラスを実装\*\*:

```python

class MyMiddleware:

&nbsp;   """カスタムミドルウェア"""



&nbsp;   def \_\_init\_\_(self):

&nbsp;       pass



&nbsp;   async def \_\_call\_\_(self, messages, config):

&nbsp;       # ミドルウェアロジック

&nbsp;       return messages

```



3\. \*\*`backend\_agent\_main.py` で登録\*\*:

```python

from deepagents\_cli.my\_middleware import MyMiddleware



agent = create\_deep\_agent(

&nbsp;   middlewares=\[MyMiddleware(), ...]

)

```



\## トラブルシューティング



\### LangGraphサーバーが起動しない



1\. `langgraph.json` のグラフ定義を確認

2\. Python依存関係が正しくインストールされているか確認: `uv sync`

3\. 環境変数 `GOOGLE\_APPLICATION\_CREDENTIALS` が設定されているか確認



\### エージェントが応答しない



1\. LLM API認証情報を確認: `.env` ファイル

2\. LangGraphサーバーログを確認: `docker compose logs backend`

3\. リクエストがプロキシされているか確認: FastAPIログ



\### ファイル操作が失敗する



1\. `WATCH\_DIR` 環境変数が正しいか確認

2\. ファイルパーミッションを確認

3\. ファイルパスが `WATCH\_DIR` 内にあるか確認



\### スキルが読み込まれない



1\. スキルディレクトリパスを確認: `~/.deepagents/agent/skills/` または `.deepagents/skills/`

2\. `SKILL.md` ファイルが存在するか確認

3\. YAMLフロントマターの形式を確認



\## 参考資料



\- \[FastAPI ドキュメント](https://fastapi.tiangolo.com/)

\- \[LangGraph ドキュメント](https://langchain-ai.github.io/langgraph/)

\- \[LangChain ドキュメント](https://python.langchain.com/)

\- \[Python 3.13 ドキュメント](https://docs.python.org/3.13/)

\- \[UV パッケージマネージャー](https://github.com/astral-sh/uv)

\- \[Google Cloud ドキュメント](https://cloud.google.com/docs)



\[← アーキテクチャ概要に戻る](../../ARCHITECTURE.md)

