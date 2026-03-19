import { SearchResult } from "./types";

export interface ExtractedMetadata {
  publication?: string;
  author?: string;
  datePublished?: string;
}

function decodeHtml(value: string): string {
  return value
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .trim();
}

function firstMetaContent(html: string, selectors: RegExp[]): string {
  for (const selector of selectors) {
    const match = html.match(selector);
    if (match?.[1]) {
      return decodeHtml(match[1]);
    }
  }
  return "";
}

function domainPublication(url: string): string {
  try {
    const host = new URL(url).hostname.replace(/^www\./, "");
    if (!host) {
      return "";
    }
    const label = host.split(".")[0] ?? host;
    return label
      .split(/[-_]/g)
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(" ");
  } catch {
    return "";
  }
}

function extractBylineAuthor(html: string): string {
  const bylinePatterns = [
    /<[^>]+class=["'][^"']*byline[^"']*["'][^>]*>([\s\S]{0,200}?)<\/[^>]+>/i,
    /\bby\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\b/i,
  ];

  for (const pattern of bylinePatterns) {
    const match = html.match(pattern);
    if (match?.[1]) {
      const clean = match[1].replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
      if (clean.length > 1 && clean.length < 80) {
        return clean.replace(/^by\s+/i, "");
      }
    }
  }

  return "";
}

function extractDateFromUrl(url: string): string {
  const patterns = [
    /\b(20\d{2})[\/-](0[1-9]|1[0-2])[\/-]([0-2]\d|3[01])\b/,
    /\b(20\d{2})(0[1-9]|1[0-2])([0-2]\d|3[01])\b/,
  ];

  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) {
      return `${match[1]}-${match[2]}-${match[3]}`;
    }
  }
  return "";
}

export function extractMetadataFromHtml(url: string, html: string): ExtractedMetadata {
  const publication = firstMetaContent(html, [
    /<meta[^>]+property=["']og:site_name["'][^>]+content=["']([^"']+)["'][^>]*>/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:site_name["'][^>]*>/i,
  ]);

  const author = firstMetaContent(html, [
    /<meta[^>]+name=["']author["'][^>]+content=["']([^"']+)["'][^>]*>/i,
    /<meta[^>]+content=["']([^"']+)["'][^>]+name=["']author["'][^>]*>/i,
    /<meta[^>]+property=["']article:author["'][^>]+content=["']([^"']+)["'][^>]*>/i,
  ]) || extractBylineAuthor(html);

  const datePublished = firstMetaContent(html, [
    /<meta[^>]+property=["']article:published_time["'][^>]+content=["']([^"']+)["'][^>]*>/i,
    /<meta[^>]+name=["']pubdate["'][^>]+content=["']([^"']+)["'][^>]*>/i,
    /<time[^>]+datetime=["']([^"']+)["'][^>]*>/i,
  ]) || extractDateFromUrl(url);

  return {
    publication: publication || domainPublication(url),
    author,
    datePublished,
  };
}

export function enrichResultMetadata(
  result: SearchResult,
  html: string,
): SearchResult {
  const extracted = extractMetadataFromHtml(result.url, html);

  return {
    ...result,
    publication: (result.publication || extracted.publication || "").trim(),
    author: (result.author || extracted.author || "").trim(),
    datePublished: (result.datePublished || extracted.datePublished || "").trim(),
  };
}
