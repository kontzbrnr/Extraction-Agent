import { promises as fs } from "fs";
import * as path from "path";
import { BuiltSourcePacket } from "./types";

export function seasonDirName(seasonWindow: string): string {
  return seasonWindow
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "") || "unknown_season";
}

export async function writePacket(
  packet: BuiltSourcePacket,
  seasonWindow: string,
  outputRoot: string
): Promise<string> {
  const seasonFolder = seasonDirName(seasonWindow);
  const packetDir = path.join(outputRoot, seasonFolder, packet.packetDirName);

  await fs.mkdir(packetDir, { recursive: true });

  const packetJsonPath = path.join(packetDir, "packet.json");
  const rawTextPath = path.join(packetDir, "raw.txt");
  const completeMarkerPath = path.join(packetDir, "_complete");

  await fs.writeFile(packetJsonPath, `${JSON.stringify(packet.metadata, null, 2)}\n`, "utf-8");
  await fs.writeFile(rawTextPath, packet.rawText, "utf-8");
  await fs.writeFile(completeMarkerPath, "complete\n", "utf-8");

  return packetDir;
}
