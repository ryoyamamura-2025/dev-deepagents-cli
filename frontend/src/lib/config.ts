export interface StandaloneConfig {
  deploymentUrl: string;
  assistantId: string;
  langsmithApiKey?: string;
  userId: string;
}

const CONFIG_STORAGE_KEY = "deepagents-config";

/**
 * Generate a unique user ID using UUID v4
 */
function generateUserId(): string {
  // Simple UUID v4 generator for browser environment
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Get configuration from localStorage
 * If userId doesn't exist, generate a new one
 */
export function getConfig(): StandaloneConfig | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const stored = localStorage.getItem(CONFIG_STORAGE_KEY);
    if (!stored) {
      return null;
    }

    const config = JSON.parse(stored) as StandaloneConfig;

    // Ensure userId exists, generate if missing
    if (!config.userId) {
      config.userId = generateUserId();
      localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(config));
    }

    return config;
  } catch (error) {
    console.error("Failed to get config from localStorage:", error);
    return null;
  }
}

/**
 * Save configuration to localStorage
 * If userId doesn't exist in the config, generate a new one
 */
export function saveConfig(config: Omit<StandaloneConfig, "userId"> & { userId?: string }): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    const configWithUserId: StandaloneConfig = {
      ...config,
      userId: config.userId || generateUserId(),
    };

    localStorage.setItem(CONFIG_STORAGE_KEY, JSON.stringify(configWithUserId));
  } catch (error) {
    console.error("Failed to save config to localStorage:", error);
  }
}

/**
 * Clear configuration from localStorage
 */
export function clearConfig(): void {
  if (typeof window === "undefined") {
    return;
  }

  try {
    localStorage.removeItem(CONFIG_STORAGE_KEY);
  } catch (error) {
    console.error("Failed to clear config from localStorage:", error);
  }
}
