"use client";

import { useState } from "react";
import { ChevronRight, Home, RefreshCw, Wifi, WifiOff, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useFileBrowser, type FileSystemItem } from "@/app/hooks/useFileBrowser";
import { FileSystemList } from "@/app/components/FileSystemList";
import { FileViewDialog } from "@/app/components/FileViewDialog";

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
    refreshDirectory,
  } = useFileBrowser();

  const [selectedFile, setSelectedFile] = useState<{
    path: string;
    content: string;
  } | null>(null);
  const [loadingFile, setLoadingFile] = useState(false);

  // パンくずナビゲーション用のパス分割
  const pathSegments = currentPath && currentPath !== "."
    ? currentPath.split("/").filter(Boolean)
    : [];

  const handleDirectoryClick = (item: FileSystemItem) => {
    navigateTo(item.path);
  };

  const handleFileClick = async (item: FileSystemItem) => {
    setLoadingFile(true);
    try {
      const fileData = await readFile(item.path);
      setSelectedFile({
        path: item.path,
        content: fileData.content,
      });
    } catch (error) {
      console.error("Failed to read file:", error);
      // TODO: Show error toast
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
            />
          )}
        </ScrollArea>
      </div>

      {/* File preview dialog */}
      {selectedFile && (
        <FileViewDialog
          file={{
            path: selectedFile.path,
            content: selectedFile.content,
          }}
          onSaveFile={async () => {
            // TODO: Implement file saving if needed
            console.log("Save file not implemented in read-only mode");
          }}
          onClose={() => setSelectedFile(null)}
          editDisabled={true} // Read-only mode
        />
      )}
    </>
  );
}
