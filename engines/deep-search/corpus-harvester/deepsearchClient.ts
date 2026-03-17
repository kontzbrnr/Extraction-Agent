import { SearchResult } from "./types";

// Thin adapter only. Contract logic belongs in the harvester runtime, not in DeepSearcher.

type UnknownRecord = Record<string, unknown>;

function normalizeResult(item: UnknownRecord): SearchResult {
  const teamContext = item.teamContext;
  const narrativeTags = item.narrativeTags;

  return {
    title: String(item.title ?? item.source_title ?? "untitled"),
    publication: String(item.publication ?? item.outlet ?? "unknown_publication"),
    author: String(item.author ?? ""),
    datePublished: String(item.datePublished ?? item.date_published ?? item.date ?? ""),
    url: String(item.url ?? ""),
    rawText: String(item.rawText ?? item.content ?? item.text ?? ""),
    teamContext: Array.isArray(teamContext)
      ? teamContext.map((value) => String(value))
      : [],
    narrativeTags: Array.isArray(narrativeTags)
      ? narrativeTags.map((value) => String(value))
      : [],
  };
}

function toResultArray(payload: unknown): SearchResult[] {
  // Vendor DeepSearcher response shape: { result: string, consume_token: number }
  if (payload && typeof payload === "object" && !Array.isArray(payload)) {
    const record = payload as UnknownRecord;
    if (typeof record.result === "string") {
      return [
        {
          title: "DeepSearch Result",
          publication: "unknown_publication",
          author: "",
          datePublished: "",
          url: "",
          rawText: record.result,
          teamContext: [],
          narrativeTags: [],
        },
      ];
    }

    const results = record.results;
    if (Array.isArray(results)) {
      return results
        .filter((item): item is UnknownRecord => !!item && typeof item === "object")
        .map(normalizeResult);
    }

    const data = record.data;
    if (Array.isArray(data)) {
      return data
        .filter((item): item is UnknownRecord => !!item && typeof item === "object")
        .map(normalizeResult);
    }
  }

  if (Array.isArray(payload)) {
    return payload
      .filter((item): item is UnknownRecord => !!item && typeof item === "object")
      .map(normalizeResult);
  }

  return [];
}

async function tryEndpoint(baseUrl: string, query: string): Promise<SearchResult[]> {
  const url = `${baseUrl}/query?original_query=${encodeURIComponent(query)}`;
  const response = await fetch(url, { method: "GET" });

  if (!response.ok) {
    throw new Error(`GET /query failed with status ${response.status}`);
  }

  const payload = await response.json();
  return toResultArray(payload);
}

async function tryRawEndpoint(baseUrl: string, query: string): Promise<SearchResult[]> {
  const url = `${baseUrl}/query_raw?original_query=${encodeURIComponent(query)}`;
  const response = await fetch(url, { method: "GET" });

  if (!response.ok) {
    throw new Error(`GET /query_raw failed with status ${response.status}`);
  }

  const payload = (await response.json()) as UnknownRecord;
  const results = Array.isArray(payload.results) ? payload.results : [];

  return results
    .filter((item): item is UnknownRecord => !!item && typeof item === "object")
    .map((item) => ({
      title: String(item.title ?? ""),
      publication: "",
      author: "",
      datePublished: "",
      url: String(item.url ?? ""),
      rawText: String(item.rawText ?? ""),
      teamContext: [],
      narrativeTags: [],
    }));
}

export function getDeepSearchBaseUrl(): string {
  return process.env.DEEPSEARCH_BASE_URL ?? "http://localhost:8000";
}

export async function runDeepSearchQuery(query: string): Promise<SearchResult[]> {
  const baseUrl = getDeepSearchBaseUrl();
  return tryEndpoint(baseUrl, query);
}

export async function runDeepSearchRawQuery(query: string): Promise<SearchResult[]> {
  const { braveSearch } = await import("./braveClient");

  const results = await braveSearch(query);

  console.log(`Brave results for query "${query}":`, results.length);

  return results.map((r) => ({
    title: r.title,
    publication: "",
    author: "",
    datePublished: "",
    url: r.url,
    rawText: r.description,
    teamContext: [],
    narrativeTags: [],
  }));
}
