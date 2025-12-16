import os
from pathlib import Path
from typing import List, Dict
import asyncio
import json
from file_api.file_watcher import FileWatcher
from file_api.config import WATCH_DIR, CORS_ORIGINS, MAX_FILE_SIZE
import httpx

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Request, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# LangGraph へのプロキシ
# ========================================
# LangGraph Server URL
LANGGRAPH_URL = "http://localhost:2024"

@app.api_route("/agent/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_langgraph(path: str, request: Request):
    """LangGraph APIへのプロキシ"""
    try:
        async with httpx.AsyncClient() as client:
            # LangGraphのAPIエンドポイントに合わせてパスを調整
            # /threads へのGETリクエストは /threads/search へのPOSTに変換
            if path == "threads" and request.method == "GET":
                path = "threads/search"
                method = "POST"
                body = await request.body()
                # クエリパラメータをボディに変換
                if request.url.query:
                    from urllib.parse import parse_qs
                    params = parse_qs(request.url.query)
                    query_body = {}
                    if "limit" in params:
                        query_body["limit"] = int(params["limit"][0])
                    if "offset" in params:
                        query_body["offset"] = int(params["offset"][0])
                    if "status" in params:
                        query_body["status"] = params["status"][0]
                    body = json.dumps(query_body).encode() if query_body else b"{}"
            else:
                method = request.method
                body = await request.body()
            
            url = f"{LANGGRAPH_URL}/{path}"
            
            # クエリパラメータも転送（GETリクエストの場合のみ）
            if request.url.query and method != "POST":
                url = f"{url}?{request.url.query}"
            
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    content=body,
                    headers={
                        key: value 
                        for key, value in request.headers.items()
                        if key.lower() not in ["host", "content-length"]
                    },
                    timeout=300.0,  # 5分タイムアウト
                )
            except httpx.ConnectError:
                raise HTTPException(
                    status_code=503,
                    detail=f"LangGraph server is not available at {LANGGRAPH_URL}. Please ensure langgraph dev is running."
                )
            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=504,
                    detail="Request to LangGraph server timed out"
                )
            except httpx.HTTPError as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"Error connecting to LangGraph server: {str(e)}"
                )
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers={
                    key: value 
                    for key, value in response.headers.items()
                    if key.lower() not in ["content-encoding", "content-length", "transfer-encoding"]
                },
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Proxy error: {str(e)}"
        )

# ========================================
# ファイルエクスプローラー
# ========================================

# ファイル監視インスタンス（イベントループは後で設定）
file_watcher = None

@app.on_event("startup")
async def startup():
    """サーバー起動時にファイル監視を開始"""
    global file_watcher
    # イベントループを取得してFileWatcherに渡す
    loop = asyncio.get_event_loop()
    file_watcher = FileWatcher(WATCH_DIR, event_loop=loop)
    file_watcher.start()
    print(f"Server started. Watching directory: {WATCH_DIR}")


@app.on_event("shutdown")
async def shutdown():
    """サーバー停止時にファイル監視を停止"""
    if file_watcher is not None:
        file_watcher.stop()
    print("Server stopped")


def sanitize_path(relative_path: str, base_dir: Path) -> Path:
    """
    パスのサニタイゼーション（セキュリティ対策）

    Args:
        relative_path: 相対パス
        base_dir: ベースディレクトリ

    Returns:
        検証済みの絶対パス

    Raises:
        ValueError: パストラバーサル検出時
    """
    clean_path = Path(relative_path.lstrip("/"))
    full_path = (base_dir / clean_path).resolve()

    # ベースディレクトリ外へのアクセスを防止
    if not str(full_path).startswith(str(base_dir.resolve())):
        raise ValueError("Path traversal detected")

    return full_path


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "File Browser API",
        "watch_dir": str(WATCH_DIR)
    }


@app.get("/api/files")
async def list_files(path: str = ""):
    """
    ファイル一覧を取得

    Args:
        path: 相対パス（オプション、デフォルトはルート）

    Returns:
        {
            "success": bool,
            "items": [
                {
                    "name": str,
                    "path": str,
                    "type": "file" | "directory",
                    "size": int,
                    "modified": float (timestamp),
                    "extension": str | null
                }
            ],
            "current_path": str
        }
    """
    try:
        target_dir = sanitize_path(path, WATCH_DIR)

        if not target_dir.exists():
            raise HTTPException(status_code=404, detail="Directory not found")

        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        items = []

        for item in sorted(target_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            stat = item.stat()
            items.append({
                "name": item.name,
                "path": str(item.relative_to(WATCH_DIR)),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime,
                "extension": item.suffix[1:] if item.is_file() and item.suffix else None
            })

        return {
            "success": True,
            "items": items,
            "current_path": str(target_dir.relative_to(WATCH_DIR))
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/api/files/{file_path:path}")
async def read_file(file_path: str):
    """
    ファイル内容を取得

    Args:
        file_path: 相対ファイルパス

    Returns:
        {
            "success": bool,
            "content": str,
            "path": str,
            "size": int,
            "modified": float (timestamp)
        }
    """
    try:
        target_file = sanitize_path(file_path, WATCH_DIR)

        if not target_file.exists():
            raise HTTPException(status_code=404, detail="File not found")

        if not target_file.is_file():
            raise HTTPException(status_code=400, detail="Path is not a file")

        # ファイルサイズ制限
        file_size = target_file.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_FILE_SIZE / 1024 / 1024}MB)"
            )

        # ファイル内容読み取り
        try:
            content = target_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Binary file not supported")

        stat = target_file.stat()

        return {
            "success": True,
            "content": content,
            "path": str(target_file.relative_to(WATCH_DIR)),
            "size": stat.st_size,
            "modified": stat.st_mtime
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocketエンドポイント（ファイル変更通知）

    クライアント接続時:
    - ファイル監視を登録
    - 変更イベントをリアルタイム送信

    送信メッセージ形式:
    {
        "event": "created" | "modified" | "deleted" | "moved",
        "path": str,
        "is_directory": bool
    }
    """
    await websocket.accept()
    print("WebSocket client connected")

    async def on_change(event_type: str, src_path: str, is_directory: bool):
        """ファイル変更時のコールバック"""
        try:
            relative_path = str(Path(src_path).relative_to(WATCH_DIR))
            await websocket.send_json({
                "event": event_type,
                "path": relative_path,
                "is_directory": is_directory
            })
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")

    # ファイル監視にコールバック登録
    if file_watcher is not None:
        file_watcher.add_listener(on_change)

    try:
        # WebSocket接続を維持（pingメッセージで接続確認）
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # クライアント切断時にリスナー削除
        if file_watcher is not None:
            file_watcher.remove_listener(on_change)

# フロントエンド配信（本番環境用）
frontend_out_dir = Path(__file__).parent / "frontend" / "out"
if frontend_out_dir.exists():
    # Next.jsの静的アセットを配信
    _next_static_dir = frontend_out_dir / "_next" / "static"
    if _next_static_dir.exists():
        app.mount("/_next/static", StaticFiles(directory=str(_next_static_dir)), name="next-static")
    
    # カスタムアセットがある場合
    assets_dir = frontend_out_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/")
    async def serve_index():
        index_html = frontend_out_dir / "index.html"
        if index_html.exists():
            return FileResponse(str(index_html))
        raise HTTPException(status_code=404, detail="Frontend index.html not found")

    # その他の静的ファイルとSPAフォールバック
    @app.get("/{full_path:path}")
    async def serve_frontend_files(full_path: str):
        # APIエンドポイント、WebSocket、ヘルスチェックは除外
        if full_path.startswith(("api/", "agent/", "ws", "health")):
            raise HTTPException(status_code=404, detail="Not found")

        file_path = frontend_out_dir / full_path.lstrip("/")

        # セキュリティ: パストラバーサル防止
        try:
            # resolve()で絶対パスに変換
            resolved_path = file_path.resolve()
            # frontend_out_dirの外へのアクセスでないことを確認
            if not str(resolved_path).startswith(str(frontend_out_dir.resolve())):
                raise HTTPException(status_code=403, detail="Forbidden")
        except (ValueError, OSError):
            raise HTTPException(status_code=403, detail="Forbidden")

        # ファイルが存在すればそれを返す
        if resolved_path.exists() and resolved_path.is_file():
            return FileResponse(str(resolved_path))
        
        # SPAフォールバック: 存在しないパスの場合はindex.htmlを返す
        index_html = frontend_out_dir / "index.html"
        if index_html.exists():
            return FileResponse(str(index_html))
        
        raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8124)