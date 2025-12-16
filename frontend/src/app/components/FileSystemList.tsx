"use client";

import { File, Folder, ChevronRight, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { FileSystemItem } from "@/app/hooks/useFileBrowser";

interface FileSystemListProps {
  items: FileSystemItem[];
  onFileClick: (item: FileSystemItem) => void;
  onDirectoryClick: (item: FileSystemItem) => void;
  onDeleteClick?: (item: FileSystemItem) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

function formatDate(timestamp: number): string {
  const date = new Date(timestamp * 1000);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
  } else if (days === 1) {
    return '昨日';
  } else if (days < 7) {
    return `${days}日前`;
  } else {
    return date.toLocaleDateString('ja-JP', { month: 'short', day: 'numeric' });
  }
}

export function FileSystemList({ items, onFileClick, onDirectoryClick, onDeleteClick }: FileSystemListProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <Folder className="mb-2 h-12 w-12 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">このディレクトリは空です</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-border">
      {items.map((item) => (
        <div
          key={item.path}
          className={cn(
            "group flex w-full items-center gap-3 px-4 py-3 transition-colors",
            "hover:bg-accent"
          )}
        >
          <button
            type="button"
            onClick={() => item.type === "directory" ? onDirectoryClick(item) : onFileClick(item)}
            className="flex flex-1 items-center gap-3 text-left focus:outline-none"
          >
            {item.type === "directory" ? (
              <Folder className="h-5 w-5 flex-shrink-0 text-blue-500" />
            ) : (
              <File className="h-5 w-5 flex-shrink-0 text-muted-foreground" />
            )}

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="truncate text-sm font-medium">{item.name}</span>
                {item.type === "directory" && (
                  <ChevronRight className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                )}
              </div>
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                {item.type === "file" && (
                  <>
                    <span>{formatFileSize(item.size)}</span>
                    <span>•</span>
                  </>
                )}
                <span>{formatDate(item.modified)}</span>
              </div>
            </div>
          </button>

          {onDeleteClick && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 transition-opacity group-hover:opacity-100"
              onClick={(e) => {
                e.stopPropagation();
                if (confirm(`「${item.name}」を削除してもよろしいですか？`)) {
                  onDeleteClick(item);
                }
              }}
              title="削除"
            >
              <Trash2 className="h-4 w-4 text-destructive" />
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}