import { buildQueriesForSeason } from "./HARVEST_QUERIES_V1";
import { runDeepSearchRawQuery } from "./deepsearchClient";
import { shouldAcceptResult } from "./duplicateGuard";
import { buildPacket } from "./packetBuilder";
import { artifactGate } from "./artifactGate";
import { writePacket } from "./packetWriter";
import { fetchArticle } from "./articleFetcher";
import { extractArticle } from "./extractArticle";
import { cleanText } from "./cleanText";
import { isAllowedSource } from "./sourceFilter";
import { HarvestDirective } from "./types";

export const SEASON_CORPUS_HARVEST: HarvestDirective = {
  seasonWindow: "2000-2001",
  targetMinSources: 30,
  targetMaxSources: 40,
  outputRoot: "shared-corpus",
  harvesterVersion: "DeepSearcher-V1",
};

export async function runHarvest(
  directive: HarvestDirective
): Promise<{
  packetsWritten: number;
  queriesRun: number;
  skippedDuplicates: number;
  packetPaths: string[];
}> {
  const seenKeys = new Set<string>();
  const packetPaths: string[] = [];

  let packetsWritten = 0;
  let queriesRun = 0;
  let skippedDuplicates = 0;
  let ordinal = 1;

  const querySets = buildQueriesForSeason(directive.seasonWindow);

  for (const querySet of querySets) {
    for (const query of querySet.queries) {
      if (packetsWritten >= directive.targetMaxSources) {
        return {
          packetsWritten,
          queriesRun,
          skippedDuplicates,
          packetPaths,
        };
      }

      queriesRun += 1;
      const results = await runDeepSearchRawQuery(query);

      for (const result of results) {
        if (packetsWritten >= directive.targetMaxSources) {
          break;
        }

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

        const html = await fetchArticle(result.url);
        const articleText = extractArticle(html, result.url);
        const cleanedText = cleanText(articleText);

        if (!cleanedText || cleanedText.length < 500) {
          console.log("Skipping low-content page:", result.url);
          skippedDuplicates += 1;
          continue;
        }

        const enrichedResult = {
          ...result,
          rawText: cleanedText,
        };

        const packet = buildPacket(
          enrichedResult,
          directive.seasonWindow,
          directive.harvesterVersion,
          ordinal
        );

        const decision = artifactGate(packet);
        if (decision === "reject") {
          skippedDuplicates += 1;
          continue;
        }

        const packetPath = await writePacket(
          packet,
          directive.seasonWindow,
          directive.outputRoot
        );

        ordinal += 1;
        packetsWritten += 1;
        packetPaths.push(packetPath);
      }
    }
  }

  return {
    packetsWritten,
    queriesRun,
    skippedDuplicates,
    packetPaths,
  };
}
