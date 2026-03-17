import fs from "fs";
import path from "path";

export function enumerateSharedCorpusPackets(season: string): string[] {
  const seasonPath = path.join("shared-corpus", season);

  if (!fs.existsSync(seasonPath)) {
    throw new Error(`Season corpus not found: ${seasonPath}`);
  }

  const entries = fs.readdirSync(seasonPath);

  return entries
    .map((e) => path.join(seasonPath, e))
    .filter((p) => fs.lstatSync(p).isDirectory());
}