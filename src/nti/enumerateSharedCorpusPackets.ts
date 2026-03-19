import fs from "fs";
import path from "path";

function candidateSeasonPaths(season: string): string[] {
  const normalized = season.replace(/-/g, "_");
  const denormalized = season.replace(/_/g, "-");
  return [
    path.join("shared-corpus", season),
    path.join("shared-corpus", normalized),
    path.join("shared-corpus", denormalized),
  ];
}

export function enumerateSharedCorpusPackets(season: string): string[] {
  const seasonPath = candidateSeasonPaths(season).find((candidate) => fs.existsSync(candidate));

  if (!seasonPath) {
    throw new Error(`Season corpus not found for: ${season}`);
  }

  const entries = fs.readdirSync(seasonPath);

  return entries
    .map((entry) => path.join(seasonPath, entry))
    .filter((entryPath) => fs.lstatSync(entryPath).isDirectory());
}
