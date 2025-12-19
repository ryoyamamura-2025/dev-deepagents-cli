/**
 * アプリケーション設定
 * 
 * 本番環境では静的ファイルがバックエンドから同じオリジンで配信されるため、
 * 相対パスを使用します（環境変数不要）。
 * 
 * 開発環境（docker-compose）では、フロントエンドとバックエンドが異なるポートで
 * 動作するため、絶対パスが必要です。
 * 
 * 環境ごとの動作:
 * - 本番環境（Cloud Run、ローカルデプロイ）: 相対パス（環境変数不要）
 * - 開発環境（docker-compose）: 絶対パス（NEXT_PUBLIC_BACKEND_URLが必要）
 */

/**
 * Backend API のベースURLを取得
 * 
 * 本番環境では相対パス（空文字列）を返し、
 * 開発環境では絶対パスを返します。
 * 
 * 判定ロジック:
 * 1. 環境変数が設定されている場合 → 開発環境（絶対パスが必要）
 * 2. それ以外 → 本番環境（相対パスでOK、静的ファイルがバックエンドから配信される）
 * 
 * 開発環境での優先順位:
 * 1. NEXT_PUBLIC_BACKEND_URL
 * 2. NEXT_PUBLIC_FILE_API_URL (後方互換性)
 * 3. デフォルト値 (http://localhost:8124)
 */
export function getBackendUrl(): string {
  // ブラウザ環境でのみ実行
  if (typeof window !== 'undefined') {
    // Next.jsでは、NEXT_PUBLIC_*環境変数はビルド時に文字列リテラルに置き換えられる
    // 開発環境（docker-compose）では環境変数が設定される
    // 本番環境では環境変数が設定されない（相対パスを使用）
    
    // 環境変数の取得
    // @ts-ignore - Next.jsではprocess.envは利用可能
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;
    // @ts-ignore - Next.jsではprocess.envは利用可能
    const fileApiUrl = process.env.NEXT_PUBLIC_FILE_API_URL;
    
    if (backendUrl || fileApiUrl) {
      // 開発環境: 絶対パスが必要
      // 1. NEXT_PUBLIC_BACKEND_URLを優先
      if (backendUrl) {
        return backendUrl;
      }
      
      // 2. NEXT_PUBLIC_FILE_API_URLをフォールバック（後方互換性）
      if (fileApiUrl) {
        return fileApiUrl;
      }
    }
    
    // 本番環境: 相対パスを使用（環境変数不要）
    // 静的ファイルがバックエンドから同じオリジンで配信されるため
    // 例: /api/files/... のように相対パスでアクセス
    return '';
  }

  // サーバーサイドレンダリング時は空文字列を返す
  return '';
}

/**
 * File API のベースURL（後方互換性のため残す）
 * @deprecated getBackendUrl() を使用してください
 */
export function getFileApiUrl(): string {
  return getBackendUrl();
}

/**
 * Backend API のベースURL（キャッシュ版）
 * パフォーマンス向上のため、一度計算した値をキャッシュします。
 */
let cachedBackendUrl: string | null = null;

export const BACKEND_URL = (() => {
  if (cachedBackendUrl === null) {
    cachedBackendUrl = getBackendUrl();
  }
  return cachedBackendUrl;
})();

/**
 * File API のベースURL（後方互換性のため残す）
 * @deprecated BACKEND_URL を使用してください
 */
export const FILE_API_URL = BACKEND_URL;

export interface StandaloneConfig {
  deploymentUrl: string;
  assistantId: string;
  langsmithApiKey?: string;
  userId?: string;
}

const CONFIG_KEY = "deep-agent-config";

export function getConfig(): StandaloneConfig | null {
  if (typeof window === "undefined") return null;

  const stored = localStorage.getItem(CONFIG_KEY);
  if (!stored) return null;

  try {
    return JSON.parse(stored);
  } catch {
    return null;
  }
}

export function saveConfig(config: StandaloneConfig): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(CONFIG_KEY, JSON.stringify(config));
}

/**
 * バックエンドからユーザーIDを取得
 * IAP認証を通過したユーザーのメールアドレスから生成されたuser_idを取得します。
 *
 * @returns ユーザーID、取得できない場合はnull
 */
export async function fetchUserId(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  try {
    const backendUrl = getBackendUrl();
    const response = await fetch(`${backendUrl}/api/user/me`);

    if (!response.ok) {
      console.error("Failed to fetch user info:", response.statusText);
      return null;
    }

    const data = await response.json();
    return data.user_id || null;
  } catch (error) {
    console.error("Error fetching user ID:", error);
    return null;
  }
}