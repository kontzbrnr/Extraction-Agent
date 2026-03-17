import * as path from "path";
import { scanSeasonPackets } from "./packetScanner";
import { moveRejectedPacket, validatePacket } from "./packetValidationGate";

// Packets must validate before NTI ingestion. NTI may only process validated packets.

export function intakeValidatedPackets(
  sharedCorpusRoot: string,
  seasonWindow: string
): {
  accepted: string[];
  rejected: string[];
} {
  const packetDirs = scanSeasonPackets(sharedCorpusRoot, seasonWindow);
  const accepted: string[] = [];
  const rejected: string[] = [];

  const rejectedRoot = path.join(sharedCorpusRoot, "rejected");

  for (const packetDir of packetDirs) {
    const validation = validatePacket(packetDir);
    if (validation.isValid) {
      accepted.push(packetDir);
      continue;
    }

    const movedPath = moveRejectedPacket(packetDir, rejectedRoot, validation.reasons);
    rejected.push(movedPath);
  }

  return {
    accepted,
    rejected,
  };
}
