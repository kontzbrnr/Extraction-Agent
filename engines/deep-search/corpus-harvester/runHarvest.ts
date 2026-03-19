import "dotenv/config";
import { readFileSync } from "fs";
import path from "path";
import { loadHarvestRuntimeConfig } from "./harvestConfig";
import { runHarvest } from "./harvestController";

function summarizeMetadataCoverage(packetPaths: string[]): { publicationCoverage: number; dateCoverage: number } {
  if (packetPaths.length === 0) {
    return { publicationCoverage: 0, dateCoverage: 0 };
  }

  let publicationFilled = 0;
  let dateFilled = 0;

  for (const packetPath of packetPaths) {
    const packetJsonPath = path.join(packetPath, "packet.json");
    const parsed = JSON.parse(readFileSync(packetJsonPath, "utf-8")) as Record<string, unknown>;

    const publication = String(parsed.publication ?? "").trim();
    const datePublished = String(parsed.date_published ?? "").trim();

    if (publication.length > 0 && publication !== "unknown_publication") {
      publicationFilled += 1;
    }
    if (datePublished.length > 0 && datePublished !== "unknown_date") {
      dateFilled += 1;
    }
  }

  const publicationCoverage = publicationFilled / packetPaths.length;
  const dateCoverage = dateFilled / packetPaths.length;
  return { publicationCoverage, dateCoverage };
}

async function main(): Promise<void> {
  const config = loadHarvestRuntimeConfig();
  console.log("harvestConfig:", config);

  const summary = await runHarvest(config.directive, config.rateLimits);
  console.log("packetsWritten:", summary.packetsWritten);
  console.log("queriesRun:", summary.queriesRun);
  console.log("skippedDuplicates:", summary.skippedDuplicates);

  const totalFetches = summary.fetchStats.success + summary.fetchStats.failures;
  const successRate = totalFetches > 0 ? summary.fetchStats.success / totalFetches : 0;
  console.log("fetchStats:", {
    ...summary.fetchStats,
    successRate,
  });

  const coverage = summarizeMetadataCoverage(summary.packetPaths);
  console.log("metadataCoverage:", {
    publicationCoverage: coverage.publicationCoverage,
    dateCoverage: coverage.dateCoverage,
    publicationTargetMet: coverage.publicationCoverage >= 0.7,
    dateTargetMet: coverage.dateCoverage >= 0.7,
  });
}

main().catch((error) => {
  console.error("Harvest runtime failed:", error);
  process.exit(1);
});
