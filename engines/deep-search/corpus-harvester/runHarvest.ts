import "dotenv/config";
import {SEASON_CORPUS_HARVEST, runHarvest } from "./harvestController";
async function main(): Promise<void> {
  const summary = await runHarvest(SEASON_CORPUS_HARVEST);
  console.log("packetsWritten:", summary.packetsWritten);
  console.log("queriesRun:", summary.queriesRun);
  console.log("skippedDuplicates:", summary.skippedDuplicates);
}

main().catch((error) => {
  console.error("Harvest runtime failed:", error);
  process.exit(1);
});
