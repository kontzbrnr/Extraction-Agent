import { buildQueriesForSeason } from "./HARVEST_QUERIES_V1";
import { runDeepSearchRawQuery } from "./deepsearchClient";
import { shouldAcceptResult } from "./duplicateGuard";
import { buildPacket } from "./packetBuilder";
import { artifactGate } from "./artifactGate";
import { writePacket } from "./packetWriter";
import { fetchArticleDetailed, FetchErrorCategory } from "./articleFetcher";
import { enrichResultMetadata } from "./metadataExtractor";
import { extractArticle } from "./extractArticle";
import { cleanText } from "./cleanText";
import { isAllowedSource } from "./sourceFilter";
import { HarvestDirective, SearchResult } from "./types";
import { PerDomainCooldownLimiter, RequestPerMinuteLimiter, runWithConcurrency } from "./rateLimiter";

export interface HarvestRateLimits {
  braveRequestsPerMinute: number;
  articleFetchMaxConcurrent: number;
  articleFetchPerDomainCooldownMs: number;
}

export interface HarvestSummary {
  packetsWritten: number;
  queriesRun: number;
  skippedDuplicates: number;
  packetPaths: string[];
  fetchStats: {
    attempts: number;
    success: number;
    failures: number;
    rateLimitOrForbidden: number;
    network: number;
    content: number;
  };
}

const DEFAULT_RATE_LIMITS: HarvestRateLimits = {
  braveRequestsPerMinute: 20,
  articleFetchMaxConcurrent: 4,
  articleFetchPerDomainCooldownMs: 1000,
};

export async function runHarvest(
  directive: HarvestDirective,
  rateLimits: HarvestRateLimits = DEFAULT_RATE_LIMITS,
): Promise<HarvestSummary> {
  const seenKeys = new Set<string>();
  const packetPaths: string[] = [];

  let packetsWritten = 0;
  let queriesRun = 0;
  let skippedDuplicates = 0;
  let ordinal = 1;
  let pendingWriteReservations = 0;

  const fetchStats = {
    attempts: 0,
    success: 0,
    failures: 0,
    rateLimitOrForbidden: 0,
    network: 0,
    content: 0,
  };

  const failureMap: Record<FetchErrorCategory, keyof typeof fetchStats> = {
    rate_limit_or_forbidden: "rateLimitOrForbidden",
    network_error: "network",
    content_error: "content",
  };

  const braveLimiter = new RequestPerMinuteLimiter(rateLimits.braveRequestsPerMinute);
  const articleDomainLimiter = new PerDomainCooldownLimiter(rateLimits.articleFetchPerDomainCooldownMs);

  const querySets = buildQueriesForSeason(directive.seasonWindow);

  function reserveWriteSlot(): number | null {
    if (packetsWritten + pendingWriteReservations >= directive.targetMaxSources) {
      return null;
    }
    pendingWriteReservations += 1;
    const reservedOrdinal = ordinal;
    ordinal += 1;
    return reservedOrdinal;
  }

  function releaseWriteReservation(committed: boolean): void {
    pendingWriteReservations = Math.max(0, pendingWriteReservations - 1);
    if (committed) {
      packetsWritten += 1;
    }
  }

  async function processResult(result: SearchResult): Promise<void> {
    if (packetsWritten >= directive.targetMaxSources) {
      return;
    }

    await articleDomainLimiter.waitTurn(result.url);

    const fetchResult = await fetchArticleDetailed(result.url);
    fetchStats.attempts += fetchResult.attempts;
    if (!fetchResult.ok) {
      fetchStats.failures += 1;
      fetchStats[failureMap[fetchResult.category]] += 1;
      skippedDuplicates += 1;
      return;
    }

    fetchStats.success += 1;

    const enrichedMetadataResult = enrichResultMetadata(result, fetchResult.html);
    const articleText = extractArticle(fetchResult.html, result.url);
    const cleanedText = cleanText(articleText);

    if (!cleanedText || cleanedText.length < 500) {
      console.log("Skipping low-content page:", result.url);
      skippedDuplicates += 1;
      return;
    }

    const reservedOrdinal = reserveWriteSlot();
    if (reservedOrdinal === null) {
      return;
    }

    let committed = false;
    try {
      const enrichedResult = {
        ...enrichedMetadataResult,
        rawText: cleanedText,
      };

      const packet = buildPacket(
        enrichedResult,
        directive.seasonWindow,
        directive.harvesterVersion,
        reservedOrdinal,
      );

      const decision = artifactGate(packet);
      if (decision === "reject") {
        skippedDuplicates += 1;
        return;
      }

      const packetPath = await writePacket(packet, directive.seasonWindow, directive.outputRoot);
      packetPaths.push(packetPath);
      committed = true;
    } finally {
      releaseWriteReservation(committed);
    }
  }

  for (const querySet of querySets) {
    for (const query of querySet.queries) {
      if (packetsWritten >= directive.targetMaxSources) {
        return {
          packetsWritten,
          queriesRun,
          skippedDuplicates,
          packetPaths,
          fetchStats,
        };
      }

      await braveLimiter.waitTurn("brave_search_query");
      queriesRun += 1;
      const results = await runDeepSearchRawQuery(query);

      const candidates: SearchResult[] = [];
      for (const result of results) {
        if (!isAllowedSource(result.url)) {
          console.log("Skipping blocked source:", result.url);
          skippedDuplicates += 1;
          continue;
        }

        const accepted = shouldAcceptResult(result, seenKeys);
        if (!accepted) {
          skippedDuplicates += 1;
          continue;
        }

        candidates.push(result);
      }

      await runWithConcurrency(candidates, rateLimits.articleFetchMaxConcurrent, processResult);
    }
  }

  return {
    packetsWritten,
    queriesRun,
    skippedDuplicates,
    packetPaths,
    fetchStats,
  };
}
