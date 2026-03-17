import fs from "fs";
import path from "path";

export type SharedCorpusPacket = {
  packetId: string;
  packetPath: string;
  metadata: any;
  rawText: string;
};

export function loadSharedCorpusPacket(packetDir: string): SharedCorpusPacket | null {
  const packetJsonPath = path.join(packetDir, "packet.json");
  const rawPath = path.join(packetDir, "raw.txt");

  if (!fs.existsSync(packetJsonPath)) return null;
  if (!fs.existsSync(rawPath)) return null;

  const metadata = JSON.parse(fs.readFileSync(packetJsonPath, "utf-8"));
  const rawText = fs.readFileSync(rawPath, "utf-8");

  if (!rawText || rawText.trim().length === 0) return null;

  return {
    packetId: metadata.packet_id,
    packetPath: packetDir,
    metadata,
    rawText,
  };
}