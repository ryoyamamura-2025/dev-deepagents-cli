"""File system watcher using watchdog library."""
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from pathlib import Path
from typing import Callable, List
import asyncio


class FileWatcher:
    """
    ファイルシステム監視クラス

    watchdogライブラリを使用してファイル変更を検知
    複数のリスナー（WebSocketクライアント）に通知
    """

    def __init__(self, watch_path: Path, event_loop=None):
        self.watch_path = watch_path
        self.observer = Observer()
        self.listeners: List[Callable] = []
        self.event_handler = self._create_handler()
        self.event_loop = event_loop

    def _create_handler(self):
        """イベントハンドラーの作成"""
        watcher = self

        class Handler(FileSystemEventHandler):
            def on_created(self, event: FileSystemEvent):
                watcher._notify("created", event.src_path, event.is_directory)

            def on_modified(self, event: FileSystemEvent):
                watcher._notify("modified", event.src_path, event.is_directory)

            def on_deleted(self, event: FileSystemEvent):
                watcher._notify("deleted", event.src_path, event.is_directory)

            def on_moved(self, event: FileSystemEvent):
                watcher._notify("moved", event.dest_path, event.is_directory)

        return Handler()

    def _notify(self, event_type: str, path: str, is_directory: bool):
        """全リスナーに通知"""
        for listener in self.listeners:
            try:
                # 非同期関数の場合はメインスレッドのイベントループで実行
                if asyncio.iscoroutinefunction(listener):
                    if self.event_loop is None:
                        # イベントループが設定されていない場合は取得を試みる
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            print(f"Error: No event loop available for async listener")
                            continue
                    else:
                        loop = self.event_loop
                    
                    # 別スレッドからメインスレッドのイベントループでコルーチンを実行
                    asyncio.run_coroutine_threadsafe(
                        listener(event_type, path, is_directory),
                        loop
                    )
                else:
                    listener(event_type, path, is_directory)
            except Exception as e:
                print(f"Error notifying listener: {e}")

    def add_listener(self, callback: Callable):
        """リスナー追加"""
        self.listeners.append(callback)

    def remove_listener(self, callback: Callable):
        """リスナー削除"""
        if callback in self.listeners:
            self.listeners.remove(callback)

    def start(self):
        """ファイル監視開始"""
        self.observer.schedule(self.event_handler, str(self.watch_path), recursive=True)
        self.observer.start()
        print(f"File watcher started for: {self.watch_path}")

    def stop(self):
        """ファイル監視停止"""
        self.observer.stop()
        self.observer.join()
        print("File watcher stopped")
