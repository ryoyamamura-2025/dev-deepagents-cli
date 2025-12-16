"use client";

import useSWR from 'swr';
import { useState, useEffect, useCallback } from 'react';

const FILE_API_URL = process.env.NEXT_PUBLIC_FILE_API_URL || 'http://localhost:8124';

export interface FileSystemItem {
  name: string;
  path: string;
  type: "file" | "directory";
  size: number;
  modified: number;
  extension?: string | null;
}

interface FileBrowserResponse {
  success: boolean;
  items: FileSystemItem[];
  current_path: string;
}

interface FileContentResponse {
  success: boolean;
  content: string;
  path: string;
  size: number;
  modified: number;
}

export function useFileBrowser(initialPath: string = "") {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [wsConnected, setWsConnected] = useState(false);

  // ファイル一覧取得（SWRでキャッシング）
  const { data, error, isLoading, mutate } = useSWR<FileBrowserResponse>(
    ['file-browser', currentPath],
    async ([_, path]: [string, string]) => {
      const params = new URLSearchParams({ path });
      const response = await fetch(`${FILE_API_URL}/api/files?${params}`);
      if (!response.ok) throw new Error('Failed to fetch files');
      return response.json();
    },
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
    }
  );

  // WebSocket接続（ファイル変更通知）
  useEffect(() => {
    const wsUrl = FILE_API_URL.replace('http', 'ws').replace('https', 'wss');
    let ws: WebSocket;
    let pingInterval: NodeJS.Timeout;
    let hasConnected = false;

    try {
      ws = new WebSocket(`${wsUrl}/ws`);

      ws.onopen = () => {
        console.log('[FileBrowser] WebSocket connected to', wsUrl);
        hasConnected = true;
        setWsConnected(true);

        // Keep-alive ping
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        // Handle pong response
        if (event.data === 'pong') {
          return;
        }

        try {
          const message = JSON.parse(event.data);

          // ファイル変更イベント受信時に再取得
          if (['created', 'modified', 'deleted', 'moved'].includes(message.event)) {
            console.log('[FileBrowser] File changed:', message);
            mutate(); // SWRキャッシュを再検証
          }
        } catch (e) {
          console.warn('[FileBrowser] Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (error) => {
        // Only log errors if we were previously connected
        if (hasConnected) {
          console.error('[FileBrowser] WebSocket connection error:', error);
        }
        setWsConnected(false);
      };

      ws.onclose = (event) => {
        if (hasConnected) {
          console.log('[FileBrowser] WebSocket disconnected', event.code, event.reason);
        }
        setWsConnected(false);
        if (pingInterval) {
          clearInterval(pingInterval);
        }
      };
    } catch (error) {
      console.error('[FileBrowser] Failed to create WebSocket:', error);
      setWsConnected(false);
    }

    return () => {
      if (ws) {
        ws.close();
      }
      if (pingInterval) {
        clearInterval(pingInterval);
      }
    };
  }, [mutate]);

  // ファイル読み取り
  const readFile = useCallback(async (filePath: string): Promise<FileContentResponse> => {
    const response = await fetch(`${FILE_API_URL}/api/files/${filePath}`);
    if (!response.ok) throw new Error('Failed to read file');
    return response.json();
  }, []);

  // ディレクトリナビゲーション
  const navigateTo = useCallback((path: string) => {
    setCurrentPath(path);
  }, []);

  return {
    items: data?.items || [],
    currentPath: data?.current_path || currentPath,
    isLoading,
    error,
    wsConnected,
    navigateTo,
    readFile,
    refreshDirectory: () => mutate(),
  };
}
