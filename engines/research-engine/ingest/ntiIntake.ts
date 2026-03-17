import {
  appendFileSync,
  copyFileSync,
  cpSync,
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  renameSync,
  rmSync,
  statSync,
} from "fs";
import * as path from "path";
import { validatePacketDetailed } from "./packetValidationGate";

const SHARED_CORPUS_REJECTED_DIR = "/contentlib-docs/shared-corpus/rejected";
const REJECTION_LOG_FILE = "packet_rejections.jsonl";

function ensureRejectedDirectory(): void {
  mkdirSync(SHARED_CORPUS_REJECTED_DIR, { recursive: true });
}

function scanCorpusDirectory(corpusRoot: string): string[] {
  if (!existsSync(corpusRoot)) {
    return [];
  }

  return readdirSync(corpusRoot)
    .map((entryName) => path.join(corpusRoot, entryName))
    .filter((entryPath) => {
      try {
        return statSync(entryPath).isDirectory();
      } catch {
        return false;
      }
    })
    .sort((left, right) => left.localeCompare(right));
}

function safeReadPacketId(packetPath: string): string {
  const packetJsonPath = path.join(packetPath, "packet.json");
  if (!existsSync(packetJsonPath)) {
    return path.basename(packetPath);
  }

  try {
    const parsed = JSON.parse(readFileSync(packetJsonPath, "utf-8"));
    const packetId = parsed?.packet_id;
    if (typeof packetId === "string" && packetId.trim().length > 0) {
      return packetId;
    }
  } catch {
    return path.basename(packetPath);
  }

  return path.basename(packetPath);
}

function targetRejectedPath(packetPath: string): string {
  const baseName = path.basename(packetPath);
  let candidatePath = path.join(SHARED_CORPUS_REJECTED_DIR, baseName);
  let index = 1;

  while (existsSync(candidatePath)) {
    candidatePath = path.join(SHARED_CORPUS_REJECTED_DIR, `${baseName}_${index}`);
    index += 1;
  }

  return candidatePath;
}

function moveRejectedPacket(packetPath: string): void {
  ensureRejectedDirectory();
  const destinationPath = targetRejectedPath(packetPath);

  try {
    renameSync(packetPath, destinationPath);
    return;
  } catch (error) {
    const code = (error as NodeJS.ErrnoException)?.code;
    if (code !== "EXDEV") {
      throw error;
    }
  }

  cpSync(packetPath, destinationPath, { recursive: true });
  rmSync(packetPath, { recursive: true, force: true });
}

function logRejectedPacket(packetPath: string, rejectionReason: string): void {
  ensureRejectedDirectory();
  const packetId = safeReadPacketId(packetPath);
  const logPath = path.join(SHARED_CORPUS_REJECTED_DIR, REJECTION_LOG_FILE);

  const logEntry = {
    packet_id: packetId,
    rejection_reason: rejectionReason,
    timestamp: new Date().toISOString(),
  };

  appendFileSync(logPath, `${JSON.stringify(logEntry)}\n`, "utf-8");
}

export function processPacket(packetPath: string): void {
  void packetPath;
}

export function ingestPackets(corpusRoot: string): void {
  const packets = scanCorpusDirectory(corpusRoot);

  for (const packetPath of packets) {
    const validation = validatePacketDetailed(packetPath);

    if (validation.isValid) {
      processPacket(packetPath);
      continue;
    }

    logRejectedPacket(packetPath, validation.reason);
    moveRejectedPacket(packetPath);
  }
}
