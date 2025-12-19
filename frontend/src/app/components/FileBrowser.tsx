"use client";

import { useState, useRef } from "react";
import { ChevronRight, Home, RefreshCw, Wifi, WifiOff, X, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useFileBrowser, type FileSystemItem } from "@/app/hooks/useFileBrowser";
import { FileSystemList } from "@/app/components/FileSystemList";
import { FileViewDialog } from "@/app/components/FileViewDialog";
import { isPreviewableFile } from "@/app/utils/filePreview";
import { FILE_API_URL } from "@/lib/config";

interface FileBrowserProps {
  onClose?: () => void;
}

function LoadingState() {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: 5 }).map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <p className="text-sm text-red-600">ファイル一覧の取得に失敗しました</p>
      <p className="mt-1 text-xs text-muted-foreground">{message}</p>
      <Button
        variant="outline"
        size="sm"
        onClick={onRetry}
        className="mt-4"
      >
        <RefreshCw className="mr-2 h-4 w-4" />
        再試行
      </Button>
    </div>
  );
}

export function FileBrowser({ onClose }: FileBrowserProps) {
  const {
    items,
    currentPath,
    isLoading,
    error,
    wsConnected,
    navigateTo,
    readFile,
    updateFile,
    deleteFile,
    uploadFiles,
    refreshDirectory,
  } = useFileBrowser();

  const [selectedFile, setSelectedFile] = useState<{
    path: string;
    content: string;
    name: string;
  } | null>(null);
  const [loadingFile, setLoadingFile] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // パンくずナビゲーション用のパス分割
  const pathSegments = currentPath && currentPath !== "."
    ? currentPath.split("/").filter(Boolean)
    : [];

  const handleDirectoryClick = (item: FileSystemItem) => {
    navigateTo(item.path);
  };

  const downloadFile = async (filePath: string, fileName: string) => {
    try {
      // パスのエンコード処理
      // FastAPIのパスパラメータは自動的にデコードされるため、URLエンコードが必要
      // ただし、/は保持する必要がある
      let encodedPath = filePath;
      if (filePath && filePath.trim() !== '') {
        // パスの各セグメントを個別にエンコード（/は保持）
        const pathSegments = filePath.split('/').map(segment => {
          // 空のセグメントはそのまま返す（先頭や末尾の/を保持）
          if (segment === '') return '';
          return encodeURIComponent(segment);
        });
        encodedPath = pathSegments.join('/');
      }
      
      const url = `${FILE_API_URL}/api/files/${encodedPath}?raw=true`;
      console.log('[FileBrowser] Downloading file:', { filePath, encodedPath, url });
      
      const response = await fetch(url);
      
      if (!response.ok) {
        // エラーレスポンスの詳細を取得
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.text();
          if (errorData) {
            // JSONエラーの場合はパースを試みる
            try {
              const errorJson = JSON.parse(errorData);
              errorMessage = errorJson.detail || errorJson.message || errorMessage;
            } catch {
              errorMessage += ` - ${errorData}`;
            }
          }
        } catch (e) {
          // エラーレスポンスの読み取りに失敗した場合は無視
        }
        console.error('[FileBrowser] Download failed:', {
          status: response.status,
          statusText: response.statusText,
          url,
          filePath,
          encodedPath,
          errorMessage
        });
        throw new Error(`ファイルのダウンロードに失敗しました: ${errorMessage}`);
      }
      
      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error("[FileBrowser] Failed to download file:", error);
      const errorMessage = error instanceof Error ? error.message : 'ファイルのダウンロードに失敗しました';
      alert(errorMessage);
    }
  };

  const handleFileClick = async (item: FileSystemItem) => {
    const extension = item.extension?.toLowerCase() || "";
    
    // プレビュー不可能なファイルの場合は確認ダイアログを表示
    if (!isPreviewableFile(extension)) {
      const shouldDownload = window.confirm(
        `「${item.name}」は現在プレビューできない形式のファイルです。\n\nダウンロードしますか？`
      );
      
      if (shouldDownload) {
        await downloadFile(item.path, item.name);
      }
      return;
    }

    setLoadingFile(true);
    try {
      // 画像やPDFなどのバイナリファイルは内容を読み込まずにプレビュー
      const isBinaryFile = ["png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico", "pdf"].includes(extension);

      if (isBinaryFile) {
        setSelectedFile({
          path: item.path,
          content: "", // バイナリファイルは内容を空にする
          name: item.name,
        });
      } else {
        const fileData = await readFile(item.path);
        setSelectedFile({
          path: item.path,
          content: fileData.content,
          name: item.name,
        });
      }
    } catch (error) {
      console.error("Failed to read file:", error);
      // テキストファイルの読み込みに失敗した場合もダウンロードを提案
      const shouldDownload = window.confirm(
        `「${item.name}」の読み込みに失敗しました。\n\nダウンロードしますか？`
      );
      
      if (shouldDownload) {
        await downloadFile(item.path, item.name);
      }
    } finally {
      setLoadingFile(false);
    }
  };

  const handleBreadcrumbClick = (index: number) => {
    if (index === -1) {
      // ルートに戻る
      navigateTo("");
    } else {
      // 指定されたパスセグメントまで戻る
      const newPath = pathSegments.slice(0, index + 1).join("/");
      navigateTo(newPath);
    }
  };

  const handleSaveFile = async (fileName: string, content: string) => {
    try {
      await updateFile(fileName, content);
      // Update the selected file with new content
      if (selectedFile) {
        setSelectedFile({
          ...selectedFile,
          content,
        });
      }
    } catch (error) {
      console.error("Failed to save file:", error);
      throw error;
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileInputChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    try {
      await uploadFiles(Array.from(files), currentPath);
      // Clear the input so the same file can be uploaded again
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      console.error("Failed to upload files:", error);
      // TODO: Show error toast
    }
  };

  const handleDeleteClick = async (item: FileSystemItem) => {
    try {
      await deleteFile(item.path);
    } catch (error) {
      console.error("Failed to delete file:", error);
      // TODO: Show error toast
    }
  };

  return (
    <>
      <div className="absolute inset-0 flex flex-col">
        {/* Header */}
        <div className="flex flex-shrink-0 items-center justify-between border-b border-border p-4">
          <h2 className="text-lg font-semibold tracking-tight">Files</h2>
          <div className="flex items-center gap-2">
            {/* WebSocket connection status */}
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              {wsConnected ? (
                <>
                  <Wifi className="h-3 w-3 text-green-500" />
                  <span className="hidden sm:inline">Live</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-3 w-3 text-orange-500" />
                  <span className="hidden sm:inline">Offline</span>
                </>
              )}
            </div>

            {/* Upload button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleUploadClick}
              className="h-8 w-8"
              title="ファイルをアップロード"
            >
              <Upload className="h-4 w-4" />
            </Button>

            {/* Refresh button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={refreshDirectory}
              className="h-8 w-8"
              disabled={isLoading}
            >
              <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
            </Button>

            {/* Close button */}
            {onClose && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="h-8 w-8"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Breadcrumb navigation */}
        <div className="flex flex-shrink-0 items-center gap-1 border-b border-border px-4 py-2 text-sm">
          <button
            type="button"
            onClick={() => handleBreadcrumbClick(-1)}
            className={cn(
              "flex items-center gap-1 rounded px-2 py-1 transition-colors",
              "hover:bg-accent",
              currentPath === "" || currentPath === "." ? "font-semibold" : ""
            )}
          >
            <Home className="h-4 w-4" />
            <span>workspace</span>
          </button>

          {pathSegments.map((segment, index) => (
            <div key={index} className="flex items-center gap-1">
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
              <button
                type="button"
                onClick={() => handleBreadcrumbClick(index)}
                className={cn(
                  "rounded px-2 py-1 transition-colors hover:bg-accent",
                  index === pathSegments.length - 1 ? "font-semibold" : ""
                )}
              >
                {segment}
              </button>
            </div>
          ))}
        </div>

        {/* File list */}
        <ScrollArea className="h-0 flex-1">
          {error && <ErrorState message={error.message} onRetry={refreshDirectory} />}

          {!error && isLoading && <LoadingState />}

          {!error && !isLoading && (
            <FileSystemList
              items={items}
              onFileClick={handleFileClick}
              onDirectoryClick={handleDirectoryClick}
              onDeleteClick={handleDeleteClick}
            />
          )}
        </ScrollArea>
      </div>

      {/* Hidden file input for upload */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileInputChange}
      />

      {/* File preview dialog */}
      {selectedFile && (
        <FileViewDialog
          file={{
            name: selectedFile.name,
            path: selectedFile.path,
            content: selectedFile.content,
          }}
          onSaveFile={handleSaveFile}
          onClose={() => setSelectedFile(null)}
          editDisabled={false}
        />
      )}
    </>
  );
}