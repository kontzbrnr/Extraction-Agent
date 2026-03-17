import fetch from "node-fetch";

export async function fetchArticle(url: string): Promise<string> {
  try {
    const res = await fetch(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 HarvestBot",
      },
    });

    return await res.text();
  } catch (err) {
    console.warn("Article fetch failed:", url);
    return "";
  }
}
