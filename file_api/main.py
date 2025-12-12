"""FastAPI server for file browsing with WebSocket support."""
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Dict
from file_watcher import FileWatcher
from config import WATCH_DIR, CORS_ORIGINS, MAX_FILE_SIZE

app = FastAPI(title="File Browser API", version="1.0.0")

# CORS設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ファイル監視インスタンス
file_watcher = FileWatcher(WATCH_DIR)


@app.on_event("startup")
async def startup():
    """サーバー起動時にファイル監視を開始"""
    file_watcher.start()
    print(f"Server started. Watching directory: {WATCH_DIR}")


@app.on_event("shutdown")
async def shutdown():
    """サーバー停止時にファイル監視を停止"""
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


@app.get("/")
async def root():
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
        file_watcher.remove_listener(on_change)
