import os
from pathlib import Path
from typing import List, Dict, Optional
from pydantic import BaseModel
import asyncio
import json
import logging

from file_api.file_watcher import FileWatcher
from file_api.config import WATCH_DIR, WATCH_DIR_BASE, get_user_watch_dir, CORS_ORIGINS, MAX_FILE_SIZE
from file_api.user_utils import get_user_id_from_request, get_user_id_from_websocket
from deepagents_cli.config import current_user_id
import httpx

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect, Request, UploadFile, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from file_api import cloud_storage as cs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# LangGraph dev subprocess handle (optional autostart)
_langgraph_proc: Optional[asyncio.subprocess.Process] = None

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
LANGGRAPH_API_URL = os.getenv("LANGGRAPH_API_URL", "http://localhost:2024")

# グローバルなhttpxクライアント（ストリーミング対応のため接続を維持）
_httpx_client: Optional[httpx.AsyncClient] = None

async def _start_langgraph_dev_background() -> None:
    """
    APIサーバーのstartup完了後に、langgraph dev をバックグラウンド起動する。
    ※ create_task で呼び出し、startup をブロックしない。
    """
    global _langgraph_proc

    if _langgraph_proc is not None and _langgraph_proc.returncode is None:
        return

    argv = ["uv", "run", "langgraph", "dev", "--allow-blocking", "--host", "0.0.0.0", "--port", "2024"]

    try:
        _langgraph_proc = await asyncio.create_subprocess_exec(
            *argv,
            # 標準出力/標準エラーは親プロセスに流してログを見えるようにする
            env=os.environ.copy(),
        )
        logger.info("Started langgraph dev (pid=%s)", _langgraph_proc.pid)
    except FileNotFoundError as e:
        logger.error("Failed to start langgraph dev (command not found): %s", e)
    except Exception as e:
        logger.exception("Failed to start langgraph dev: %s", e)

@app.api_route("/agent/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_langgraph(path: str, request: Request):
    """LangGraph APIへのプロキシ"""
    # ユーザーIDを取得してコンテキストに設定
    user_id = get_user_id_from_request(request)
    current_user_id.set(user_id)

    if _httpx_client is None:
        raise HTTPException(
            status_code=503,
            detail="HTTP client not initialized. Server may be starting up."
        )

    try:
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

        url = f"{LANGGRAPH_API_URL}/{path}"

        # クエリパラメータも転送（GETリクエストの場合のみ）
        if request.url.query and method != "POST":
            url = f"{url}?{request.url.query}"

        try:
            # まずヘッダーを取得するためにリクエストを開始
            response = await _httpx_client.send(
                _httpx_client.build_request(
                    method=method,
                    url=url,
                    content=body,
                    headers={
                        key: value
                        for key, value in request.headers.items()
                        if key.lower() not in ["host", "content-length"]
                    },
                ),
                stream=True,
            )

            # ストリーミングレスポンスの場合
            if response.headers.get("content-type", "").startswith("text/event-stream"):
                async def stream_generator():
                    try:
                        async for chunk in response.aiter_bytes():
                            yield chunk
                    finally:
                        await response.aclose()

                return StreamingResponse(
                    stream_generator(),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type="text/event-stream",
                )

            # 非ストリーミングレスポンスの場合は全体を読み込む
            try:
                content = await response.aread()
                return Response(
                    content=content,
                    status_code=response.status_code,
                    headers={
                        key: value
                        for key, value in response.headers.items()
                        if key.lower() not in ["content-encoding", "content-length", "transfer-encoding"]
                    },
                )
            finally:
                await response.aclose()

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"LangGraph server is not available at {LANGGRAPH_API_URL}. Please ensure langgraph dev is running."
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

# ユーザーIDごとのファイル監視インスタンス
file_watchers: Dict[str, FileWatcher] = {}

def get_or_create_file_watcher(user_id: str) -> FileWatcher:
    """
    Get or create a FileWatcher for a specific user.

    Args:
        user_id: User ID

    Returns:
        FileWatcher instance for the user
    """
    if user_id not in file_watchers:
        user_watch_dir = get_user_watch_dir(user_id)
        loop = asyncio.get_event_loop()
        watcher = FileWatcher(user_watch_dir, event_loop=loop)
        watcher.start()
        file_watchers[user_id] = watcher
        logger.info(f"Started file watcher for user {user_id} at {user_watch_dir}")
    return file_watchers[user_id]

@app.on_event("startup")
async def startup():
    # httpxクライアントを初期化
    global _httpx_client
    _httpx_client = httpx.AsyncClient(timeout=300.0)
    logger.info("Initialized httpx client for LangGraph proxy")

    # GCS との同期
    # /root/.deepagentsの作成
    logger.info("Ensuring agent_config is available...")
    bucket_name = os.getenv("GCS_BUCKET")
    source_prefix = os.getenv("GCS_AGENT_CONFIG_PREFIX", "/for-deepagents/agent_config")
    destination_dir = os.getenv("AGENT_CONFIG_DEST_DIR", "/root")

    if not cs.download_from_gcs(
        bucket_name=bucket_name,
        source_prefix=source_prefix,
        destination_dir=destination_dir,
    ):
        logger.warning("Could not ensure agent_config availability. Agent may not function properly.")
    else:
        logger.info("agent_config is ready")

    # /app/workspaceの作成（デフォルトユーザー用）
    # 注: ユーザーIDベースのworkspaceは各ユーザーのアクセス時に動的に作成される
    logger.info("Downloading default workspace files...")
    destination_dir = os.getenv("WORKSPACE_DEST_DIR", "/app/workspace/default")

    if not cs.download_user_workspace_from_gcs(
        user_id="default",
        destination_dir=destination_dir,
    ):
        logger.warning("Could not download default workspace files.")
    else:
        logger.info("Default workspace files are ready")

    # ファイル監視はユーザーアクセス時に動的に作成される
    logger.info(f"Server started. File watchers will be created per user.")

    # APIサーバー起動（startup処理）完了後に langgraph dev を起動（startup自体はブロックしない）
    asyncio.create_task(_start_langgraph_dev_background())


@app.on_event("shutdown")
async def shutdown():
    """サーバー停止時にファイル監視を停止"""
    # httpxクライアントをクローズ
    global _httpx_client
    if _httpx_client is not None:
        await _httpx_client.aclose()
        logger.info("Closed httpx client")
        _httpx_client = None

    # すべてのfile_watchersを停止
    for user_id, watcher in file_watchers.items():
        try:
            watcher.stop()
            logger.info(f"Stopped file watcher for user {user_id}")
        except Exception as e:
            logger.error(f"Error stopping file watcher for user {user_id}: {e}")

    # langgraph dev をこのプロセスから起動している場合は停止
    global _langgraph_proc
    if _langgraph_proc is not None and _langgraph_proc.returncode is None:
        try:
            _langgraph_proc.terminate()
            await asyncio.wait_for(_langgraph_proc.wait(), timeout=5.0)
            logger.info("Stopped langgraph dev (pid=%s)", _langgraph_proc.pid)
        except asyncio.TimeoutError:
            _langgraph_proc.kill()
            await _langgraph_proc.wait()
            logger.warning("Killed langgraph dev (pid=%s) after timeout", _langgraph_proc.pid)
        except Exception as e:
            logger.exception("Error stopping langgraph dev: %s", e)
        finally:
            _langgraph_proc = None

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
    # 空のパスや"."の場合はベースディレクトリを返す
    if not relative_path or relative_path == "." or relative_path == "":
        return base_dir.resolve()
    
    # 先頭のスラッシュを削除（相対パスとして扱う）
    clean_path = relative_path.lstrip("/")
    
    # 空になった場合はベースディレクトリを返す
    if not clean_path:
        return base_dir.resolve()
    
    clean_path = Path(clean_path)
    full_path = (base_dir / clean_path).resolve()

    # ベースディレクトリ外へのアクセスを防止
    base_resolved = base_dir.resolve()
    if not str(full_path).startswith(str(base_resolved)):
        raise ValueError(f"Path traversal detected: {relative_path} -> {full_path} (base: {base_resolved})")

    return full_path


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "File Browser API",
        "watch_dir": str(WATCH_DIR)
    }


@app.get("/api/user/me")
async def get_current_user(request: Request):
    """
    Get current user information from IAP headers.

    Returns:
        {
            "user_id": str,
            "email": str | null
        }
    """
    from file_api.user_utils import get_email_from_iap_headers

    user_id = get_user_id_from_request(request)
    email = get_email_from_iap_headers(request)

    return {
        "user_id": user_id,
        "email": email
    }


@app.get("/api/files")
async def list_files(request: Request, path: str = ""):
    """
    ファイル一覧を取得

    Args:
        request: FastAPI Request object
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
        # ユーザーIDを取得してコンテキストに設定
        user_id = get_user_id_from_request(request)
        current_user_id.set(user_id)
        user_watch_dir = get_user_watch_dir(user_id)

        target_dir = sanitize_path(path, user_watch_dir)

        if not target_dir.exists():
            raise HTTPException(status_code=404, detail="Directory not found")

        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="Path is not a directory")

        items = []

        for item in sorted(target_dir.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            stat = item.stat()
            items.append({
                "name": item.name,
                "path": str(item.relative_to(user_watch_dir)),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime,
                "extension": item.suffix[1:] if item.is_file() and item.suffix else None
            })

        return {
            "success": True,
            "items": items,
            "current_path": str(target_dir.relative_to(user_watch_dir))
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/api/files/{file_path:path}")
async def read_file(request: Request, file_path: str, raw: bool = False):
    """
    ファイル内容を取得

    Args:
        request: FastAPI Request object
        file_path: 相対ファイルパス
        raw: Trueの場合、バイナリファイルとして配信（画像・PDF用）

    Returns:
        raw=False (デフォルト):
        {
            "success": bool,
            "content": str,
            "path": str,
            "size": int,
            "modified": float (timestamp)
        }

        raw=True:
        バイナリファイルを直接配信（Content-Type自動設定）
    """
    try:
        # ユーザーIDを取得してコンテキストに設定
        user_id = get_user_id_from_request(request)
        current_user_id.set(user_id)
        user_watch_dir = get_user_watch_dir(user_id)

        target_file = sanitize_path(file_path, user_watch_dir)

        # ファイルサイズ制限
        file_size = target_file.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_FILE_SIZE / 1024 / 1024}MB)"
            )

        # ファイル内容読み取り
        # rawモードの場合はバイナリファイルとして配信
        if raw:
            import mimetypes
            
            # ファイル拡張子を取得してファイルタイプを判定
            file_ext = target_file.suffix.lower()
            is_pdf = file_ext == ".pdf"
            # 画像ファイルの拡張子リスト
            image_exts = [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".ico"]
            is_image = file_ext in image_exts
            
            # MIMEタイプを取得（PDFの場合は明示的に設定）
            if is_pdf:
                mime_type = "application/pdf"
            else:
                mime_type, _ = mimetypes.guess_type(str(target_file))
                if not mime_type:
                    mime_type = "application/octet-stream"
            
            # ファイルを読み込む
            file_content = target_file.read_bytes()
            
            # レスポンスヘッダーを設定
            headers = {}
            
            # ファイル名のエンコード（日本語対応）
            # RFC 5987形式でエンコード（UTF-8）
            from urllib.parse import quote
            
            # Content-Dispositionヘッダーを設定（日本語ファイル名対応）
            disposition_type = "inline" if (is_pdf or is_image) else "attachment"
            
            # ASCII文字のみの場合は通常形式、非ASCII文字の場合はRFC 5987形式を使用
            if all(ord(c) < 128 for c in target_file.name):
                # ASCII文字のみの場合は通常形式
                headers["Content-Disposition"] = f'{disposition_type}; filename="{target_file.name}"'
            else:
                # 非ASCII文字（日本語など）を含む場合はRFC 5987形式
                # filename* パラメータでUTF-8エンコードされたファイル名を指定
                # filename パラメータにはASCII文字のみを使用（互換性のため）
                filename_ascii = target_file.name.encode('ascii', 'ignore').decode('ascii')
                if not filename_ascii:
                    filename_ascii = "file"  # ASCII文字がない場合はデフォルト名
                filename_utf8_encoded = quote(target_file.name, safe='')
                headers["Content-Disposition"] = (
                    f'{disposition_type}; filename="{filename_ascii}"; '
                    f'filename*=UTF-8\'\'{filename_utf8_encoded}'
                )
            
            # CORSヘッダーを明示的に設定（クラウドデプロイ時の問題対策）
            headers["Access-Control-Allow-Origin"] = "*"
            headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            headers["Access-Control-Allow-Headers"] = "*"
            
            return Response(
                content=file_content,
                media_type=mime_type,
                headers=headers
            )

        # テキストファイルとして読み取り
        try:
            content = target_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Binary file not supported. Use ?raw=true for binary files"
            )

        stat = target_file.stat()

        return {
            "success": True,
            "content": content,
            "path": str(target_file.relative_to(user_watch_dir)),
            "size": stat.st_size,
            "modified": stat.st_mtime
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

class FileUpdateRequest(BaseModel):
    """ファイル更新リクエストモデル"""
    content: str


@app.put("/api/files/{file_path:path}")
async def update_file(http_request: Request, file_path: str, request: FileUpdateRequest):
    """
    ファイル内容を更新

    Args:
        http_request: FastAPI Request object
        file_path: 相対ファイルパス
        request: 更新内容を含むリクエストボディ

    Returns:
        {
            "success": bool,
            "message": str,
            "path": str
        }
    """
    try:
        # ユーザーIDを取得してコンテキストに設定
        user_id = get_user_id_from_request(http_request)
        current_user_id.set(user_id)
        user_watch_dir = get_user_watch_dir(user_id)

        target_file = sanitize_path(file_path, user_watch_dir)

        # 親ディレクトリが存在するか確認
        if not target_file.parent.exists():
            raise HTTPException(status_code=404, detail="Parent directory not found")

        # ファイルが存在しない場合は新規作成
        if not target_file.exists():
            target_file.touch()

        # ファイル書き込み（fsync()で同期）
        try:
            target_file.write_text(request.content, encoding="utf-8")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

        return {
            "success": True,
            "message": "File updated successfully",
            "path": str(target_file.relative_to(user_watch_dir))
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.delete("/api/files/{file_path:path}")
async def delete_file(request: Request, file_path: str):
    """
    ファイルまたはディレクトリを削除

    Args:
        request: FastAPI Request object
        file_path: 相対ファイルパス

    Returns:
        {
            "success": bool,
            "message": str,
            "path": str
        }
    """
    try:
        # ユーザーIDを取得してコンテキストに設定
        user_id = get_user_id_from_request(request)
        current_user_id.set(user_id)
        user_watch_dir = get_user_watch_dir(user_id)

        target_path = sanitize_path(file_path, user_watch_dir)

        if not target_path.exists():
            raise HTTPException(status_code=404, detail="File or directory not found")

        # ディレクトリの場合は再帰的に削除
        if target_path.is_dir():
            import shutil
            shutil.rmtree(target_path)
        else:
            target_path.unlink()

        return {
            "success": True,
            "message": "File deleted successfully",
            "path": str(target_path.relative_to(user_watch_dir))
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/api/files/upload")
async def upload_files(
    request: Request,
    files: List[UploadFile],
    path: str = Form("")
):
    """
    ファイルをアップロード

    Args:
        request: FastAPI Request object
        files: アップロードするファイルのリスト
        path: アップロード先の相対パス（オプション）

    Returns:
        {
            "success": bool,
            "message": str,
            "uploaded_files": List[str]
        }
    """
    try:
        # ユーザーIDを取得してコンテキストに設定
        user_id = get_user_id_from_request(request)
        current_user_id.set(user_id)
        user_watch_dir = get_user_watch_dir(user_id)

        target_dir = sanitize_path(path, user_watch_dir)

        if not target_dir.exists():
            raise HTTPException(status_code=404, detail="Target directory not found")

        if not target_dir.is_dir():
            raise HTTPException(status_code=400, detail="Target path is not a directory")

        uploaded_files = []

        for file in files:
            if not file.filename:
                continue

            # ファイル名をサニタイズ（パストラバーサル防止）
            safe_filename = Path(file.filename).name
            target_file = target_dir / safe_filename

            # ファイルを保存（fsync()で同期）
            content = await file.read()
            target_file.write_bytes(content)

            uploaded_files.append(str(target_file.relative_to(user_watch_dir)))

        return {
            "success": True,
            "message": f"Uploaded {len(uploaded_files)} file(s)",
            "uploaded_files": uploaded_files
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/api/workspace/save")
async def save_workspace_to_gcs(request: Request):
    """
    Save current user's workspace to Google Cloud Storage.

    This endpoint uploads all files in the user's workspace directory to GCS.
    Files are saved to: gs://{GCS_BUCKET}/{GCS_WORKSPACE_PREFIX}/workspace_{user_id}/

    Args:
        request: FastAPI Request object

    Returns:
        {
            "success": bool,
            "message": str,
            "user_id": str
        }
    """
    try:
        # Get user ID from request headers
        user_id = get_user_id_from_request(request)
        current_user_id.set(user_id)
        user_watch_dir = get_user_watch_dir(user_id)

        logger.info(f"Saving workspace to GCS for user {user_id}")

        # Upload workspace to GCS
        if cs.upload_user_workspace_to_gcs(user_id, str(user_watch_dir)):
            return {
                "success": True,
                "message": f"Workspace saved successfully for user {user_id}",
                "user_id": user_id
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to save workspace to Cloud Storage. Check server logs for details."
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error saving workspace to GCS: {e}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocketエンドポイント（ファイル変更通知）

    クライアント接続時:
    - ユーザーIDを取得
    - ユーザー専用のファイル監視を登録
    - 変更イベントをリアルタイム送信

    送信メッセージ形式:
    {
        "event": "created" | "modified" | "deleted" | "moved",
        "path": str,
        "is_directory": bool
    }
    """
    await websocket.accept()

    # ユーザーIDを取得してコンテキストに設定
    user_id = get_user_id_from_websocket(websocket)
    current_user_id.set(user_id)
    logger.info(f"WebSocket client connected for user {user_id}")

    # ユーザー専用のFileWatcherを取得または作成
    user_watcher = get_or_create_file_watcher(user_id)
    user_watch_dir = get_user_watch_dir(user_id)

    async def on_change(event_type: str, src_path: str, is_directory: bool):
        """ファイル変更時のコールバック"""
        try:
            relative_path = str(Path(src_path).relative_to(user_watch_dir))
            await websocket.send_json({
                "event": event_type,
                "path": relative_path,
                "is_directory": is_directory
            })
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")

    # ファイル監視にコールバック登録
    user_watcher.add_listener(on_change)

    try:
        # WebSocket接続を維持（pingメッセージで接続確認）
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # クライアント切断時にリスナー削除
        user_watcher.remove_listener(on_change)

# フロントエンド配信（本番環境用）
STATIC_DIR = os.getenv("STATIC_DIR", "../static-build")
if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
else:
    print(f"Warning: Static directory {STATIC_DIR} not found")

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.environ.get("PORT", 8124))
    uvicorn.run(app, host="0.0.0.0", port=PORT)