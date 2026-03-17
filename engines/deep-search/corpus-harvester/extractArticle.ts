import { JSDOM } from "jsdom";
import { Readability } from "@mozilla/readability";
import * as cheerio from "cheerio";

export function extractArticle(html: string, url: string): string {
  try {
    const dom = new JSDOM(html, { url });
    const reader = new Readability(dom.window.document);
    const article = reader.parse();

    if (article && article.textContent) {
      return article.textContent.trim();
    }
  } catch {}

  const $ = cheerio.load(html);
  const paragraphs: string[] = [];

  $("p").each((_, el) => {
    const text = $(el).text().trim();
    if (text.length > 80) {
      paragraphs.push(text);
    }
  });

  return paragraphs.join("\n\n");
}