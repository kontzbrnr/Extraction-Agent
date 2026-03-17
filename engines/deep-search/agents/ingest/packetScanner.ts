import { existsSync, readdirSync, statSync } from "fs";
import * as path from "path";

function seasonDirName(seasonWindow: string): string {
  return seasonWindow
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "") || "unknown_season";
}

function listChildDirectories(parentDir: string): string[] {
  if (!existsSync(parentDir)) {
    return [];
  }

  return readdirSync(parentDir)
    .map((entry) => path.join(parentDir, entry))
    .filter((candidate) => {
      try {
        return statSync(candidate).isDirectory();
      } catch {
        return false;
      }
    })
    .sort((a, b) => a.localeCompare(b));
}

export function scanSeasonPackets(
  sharedCorpusRoot: string,
  seasonWindow: string
): string[] {
  const seasonFolder = seasonDirName(seasonWindow);
  const seasonPath = path.join(sharedCorpusRoot, seasonFolder);
  return listChildDirectories(seasonPath);
}

export function scanAllPackets(sharedCorpusRoot: string): string[] {
  const seasonDirs = listChildDirectories(sharedCorpusRoot);
  const packetDirs = seasonDirs.flatMap((seasonDir) => listChildDirectories(seasonDir));
  return packetDirs;
}
