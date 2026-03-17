import { BuiltSourcePacket, SearchResult } from "./types";
import {
  currentTimestampISO,
  ensureArray,
  normalizeDateToYYYYMMDD,
  safeString,
  slugify,
} from "./utils";

export function buildPacket(
  result: SearchResult,
  seasonWindow: string,
  harvesterVersion: string,
  ordinal: number
): BuiltSourcePacket {
  const seasonSlug = slugify(seasonWindow);
  const publicationValue = safeString(result.publication);
  const publicationSlug =
    publicationValue.length > 0 ? slugify(publicationValue) : "unknown_publication";

  const packetId = `${seasonSlug}_${publicationSlug}_${String(ordinal).padStart(4, "0")}`;
  const packetDirName = packetId;

  const metadata = {
    packet_id: packetId,
    source_title: safeString(result.title),
    publication: publicationValue,
    author: safeString(result.author),
    date_published: normalizeDateToYYYYMMDD(result.datePublished),
    url: safeString(result.url),
    season_window: safeString(seasonWindow),
    team_context: ensureArray(result.teamContext),
    narrative_tags: ensureArray(result.narrativeTags),
    harvest_timestamp: currentTimestampISO(),
    harvester_version: safeString(harvesterVersion),
  };

  return {
    packetDirName,
    metadata,
    rawText: (result.rawText ?? "").trim(),
  };
}
