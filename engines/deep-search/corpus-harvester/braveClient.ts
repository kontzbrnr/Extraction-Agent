import fetch from "node-fetch";

const BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search";

export interface BraveSearchResult {
  title: string;
  url: string;
  description: string;
}

export async function braveSearch(query: string): Promise<BraveSearchResult[]> {
  const url = `${BRAVE_ENDPOINT}?q=${encodeURIComponent(query)}&count=10`;
  const headers = {
    Accept: "application/json",
    "X-Subscription-Token": process.env.BRAVE_API_KEY ?? "",
  };

  console.log("Brave query:", query);
  console.log("API key present:", !!process.env.BRAVE_API_KEY);
  console.log("Brave request URL:", url);
  console.log("Brave request headers:", headers);

  const res = await fetch(url, {
    headers,
  });

  if (!res.ok) {
    const responseBody = await res.text();
    console.error("Brave response status:", res.status);
    console.error("Brave response body:", responseBody);
    throw new Error(
      `Brave API error: ${res.status} for query "${query}". Response: ${responseBody}`
    );
  }

  const data = (await res.json()) as { web?: { results?: Array<{ title: string; url: string; description?: string }> } };

  if (!data.web || !data.web.results) {
    return [];
  }

  return data.web.results.map((r) => ({
    title: r.title,
    url: r.url,
    description: r.description ?? "",
  }));
}
