/**
 * ファイルがプレビュー可能かどうかを判定
 */
export function isPreviewableFile(extension: string | null | undefined): boolean {
  if (!extension) return false;
  
  const ext = extension.toLowerCase();
  
  // プレビュー可能な拡張子リスト
  const previewableExtensions = [
    // テキストファイル
    "txt", "log", "env", "gitignore",
    // Markdown
    "md", "markdown",
    // コードファイル
    "py", "js", "ts", "jsx", "tsx", "json", "yaml", "yml", "toml", "ini",
    "xml", "html", "css", "scss", "sass", "less", "sql",
    "sh", "bash", "zsh", "dockerfile", "makefile",
    "rb", "go", "rs", "java", "cpp", "c", "cs", "php", "swift", "kt", "scala",
    // 画像
    "png", "jpg", "jpeg", "gif", "svg", "webp", "bmp", "ico",
    // PDF
    "pdf",
  ];
  
  return previewableExtensions.includes(ext);
}

/**
 * ファイルパスから拡張子を取得
 */
export function getFileExtension(filePath: string): string {
  const parts = filePath.split(".");
  return parts.length > 1 ? parts[parts.length - 1].toLowerCase() : "";
}

