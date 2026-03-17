import { SearchResult } from "./types";
import { normalizeDateToYYYYMMDD, safeString, slugify } from "./utils";

export function buildDuplicateKey(result: SearchResult): string {
  const urlValue = safeString(result.url).toLowerCase();
  const urlNorm = urlValue.length > 0 ? urlValue : "unknown_url";

  const titleValue = safeString(result.title);
  const titleNorm = titleValue.length > 0 ? slugify(titleValue) : "unknown_title";

  const publicationValue = safeString(result.publication);
  const publicationNorm =
    publicationValue.length > 0 ? slugify(publicationValue) : "unknown_publication";

  const dateNorm = normalizeDateToYYYYMMDD(result.datePublished);

  return `${urlNorm}|${titleNorm}|${publicationNorm}|${dateNorm}`;
}

export function shouldAcceptResult(
  result: SearchResult,
  seenKeys: Set<string>
): boolean {
  const key = buildDuplicateKey(result);
  if (seenKeys.has(key)) {
    return false;
  }
  seenKeys.add(key);
  return true;
}
