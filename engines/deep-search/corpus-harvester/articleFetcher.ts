import fetch from "node-fetch";

export type FetchErrorCategory = "rate_limit_or_forbidden" | "network_error" | "content_error";

export interface FetchSuccess {
  ok: true;
  html: string;
  statusCode: number;
  attempts: number;
}

export interface FetchFailure {
  ok: false;
  html: "";
  statusCode?: number;
  attempts: number;
  category: FetchErrorCategory;
  errorType: string;
}

export type FetchResult = FetchSuccess | FetchFailure;

const MAX_ATTEMPTS = 3;
const BASE_BACKOFF_MS = 250;

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function logFetchFailure(url: string, payload: {
  attempt: number;
  statusCode?: number;
  category: FetchErrorCategory;
  errorType: string;
  message: string;
}): void {
  console.warn("[ArticleFetchError]", JSON.stringify({ url, ...payload }));
}

export async function fetchArticleDetailed(url: string): Promise<FetchResult> {
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    try {
      const res = await fetch(url, {
        headers: {
          "User-Agent": "Mozilla/5.0 HarvestBot",
        },
      });

      if (!res.ok) {
        const category: FetchErrorCategory =
          res.status === 403 || res.status === 429
            ? "rate_limit_or_forbidden"
            : "content_error";

        logFetchFailure(url, {
          attempt,
          statusCode: res.status,
          category,
          errorType: `http_${res.status}`,
          message: `HTTP ${res.status}`,
        });

        if (attempt < MAX_ATTEMPTS) {
          await wait(BASE_BACKOFF_MS * 2 ** (attempt - 1));
          continue;
        }

        return {
          ok: false,
          html: "",
          statusCode: res.status,
          attempts: attempt,
          category,
          errorType: `http_${res.status}`,
        };
      }

      const html = await res.text();
      if (!html || html.trim().length === 0) {
        logFetchFailure(url, {
          attempt,
          statusCode: res.status,
          category: "content_error",
          errorType: "empty_body",
          message: "HTTP body was empty",
        });

        if (attempt < MAX_ATTEMPTS) {
          await wait(BASE_BACKOFF_MS * 2 ** (attempt - 1));
          continue;
        }

        return {
          ok: false,
          html: "",
          statusCode: res.status,
          attempts: attempt,
          category: "content_error",
          errorType: "empty_body",
        };
      }

      return { ok: true, html, statusCode: res.status, attempts: attempt };
    } catch (error) {
      const message = error instanceof Error ? error.message : "unknown_error";
      const errorType = error instanceof Error ? error.name : "NonErrorThrow";
      logFetchFailure(url, {
        attempt,
        category: "network_error",
        errorType,
        message,
      });

      if (attempt < MAX_ATTEMPTS) {
        await wait(BASE_BACKOFF_MS * 2 ** (attempt - 1));
        continue;
      }

      return {
        ok: false,
        html: "",
        attempts: attempt,
        category: "network_error",
        errorType,
      };
    }
  }

  return {
    ok: false,
    html: "",
    attempts: MAX_ATTEMPTS,
    category: "network_error",
    errorType: "max_attempts_exhausted",
  };
}

export async function fetchArticle(url: string): Promise<string> {
  const result = await fetchArticleDetailed(url);
  return result.ok ? result.html : "";
}
