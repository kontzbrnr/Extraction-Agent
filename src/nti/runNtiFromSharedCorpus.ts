import { enumerateSharedCorpusPackets } from "./enumerateSharedCorpusPackets";
import { loadSharedCorpusPacket } from "./loadSharedCorpusPacket";
import { adaptSharedCorpusPacketToNti } from "./adaptSharedCorpusPacketToNti";

// Replace this import with your actual extraction entrypoint
import { runExtraction } from "../extraction/runExtraction";

export async function runNtiFromSharedCorpus(season: string) {
  console.log(`NTI run starting for season: ${season}`);

  const packetDirs = enumerateSharedCorpusPackets(season);

  console.log(`Found ${packetDirs.length} packets`);

  for (const dir of packetDirs) {
    const packet = loadSharedCorpusPacket(dir);

    if (!packet) {
      console.log("Skipping invalid packet:", dir);
      continue;
    }

    const ntiDoc = adaptSharedCorpusPacketToNti(packet);

    console.log("Running extraction for:", ntiDoc.sourceId);

    await runExtraction(ntiDoc);
  }

  console.log("NTI run complete");
}