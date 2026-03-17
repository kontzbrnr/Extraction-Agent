import { existsSync, readFileSync } from "fs";
import * as path from "path";

const REQUIRED_FILES = ["packet.json", "raw.txt", "_complete"] as const;

const REQUIRED_PACKET_FIELDS = [
  "packet_id",
  "source_title",
  "publication",
  "date_published",
  "season_window",
  "harvest_timestamp",
  "harvester_version",
] as const;

export const RAW_TEXT_MIN_LENGTH = 500;
export const PACKET_VALIDATION_GATE_CONTRACT_STATUS =
  "LOCKED — PACKET_VALIDATION_GATE_V1";

export interface PacketValidationResult {
  isValid: boolean;
  reason: string;
  packetId: string;
}

function safePacketId(packetPath: string, parsedPacketJson?: Record<string, unknown>): string {
  const packetId = parsedPacketJson?.packet_id;
  if (typeof packetId === "string" && packetId.trim().length > 0) {
    return packetId;
  }
  return path.basename(packetPath);
}

function readPacketJson(packetJsonPath: string): Record<string, unknown> | null {
  try {
    const raw = readFileSync(packetJsonPath, "utf-8");
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return null;
    }
    return parsed as Record<string, unknown>;
  } catch {
    return null;
  }
}

export function validatePacketDetailed(packetPath: string): PacketValidationResult {
  for (const fileName of REQUIRED_FILES) {
    const requiredFilePath = path.join(packetPath, fileName);
    if (!existsSync(requiredFilePath)) {
      return {
        isValid: false,
        reason: `MISSING_REQUIRED_FILE:${fileName}`,
        packetId: path.basename(packetPath),
      };
    }
  }

  const packetJsonPath = path.join(packetPath, "packet.json");
  const packetJson = readPacketJson(packetJsonPath);
  if (!packetJson) {
    return {
      isValid: false,
      reason: "INVALID_PACKET_JSON",
      packetId: path.basename(packetPath),
    };
  }

  for (const fieldName of REQUIRED_PACKET_FIELDS) {
    const value = packetJson[fieldName];
    if (value === undefined || value === null || (typeof value === "string" && value.trim() === "")) {
      return {
        isValid: false,
        reason: `MISSING_PACKET_JSON_FIELD:${fieldName}`,
        packetId: safePacketId(packetPath, packetJson),
      };
    }
  }

  const rawTextPath = path.join(packetPath, "raw.txt");
  let rawText = "";
  try {
    rawText = readFileSync(rawTextPath, "utf-8");
  } catch {
    return {
      isValid: false,
      reason: "RAW_TEXT_READ_ERROR",
      packetId: safePacketId(packetPath, packetJson),
    };
  }

  if (rawText.trim().length === 0) {
    return {
      isValid: false,
      reason: "RAW_TEXT_EMPTY",
      packetId: safePacketId(packetPath, packetJson),
    };
  }

  if (rawText.length < RAW_TEXT_MIN_LENGTH) {
    return {
      isValid: false,
      reason: `RAW_TEXT_TOO_SHORT:min=${RAW_TEXT_MIN_LENGTH}`,
      packetId: safePacketId(packetPath, packetJson),
    };
  }

  const completionMarkerPath = path.join(packetPath, "_complete");
  if (!existsSync(completionMarkerPath)) {
    return {
      isValid: false,
      reason: "MISSING_COMPLETION_MARKER",
      packetId: safePacketId(packetPath, packetJson),
    };
  }

  return {
    isValid: true,
    reason: "VALID",
    packetId: safePacketId(packetPath, packetJson),
  };
}

export function validatePacket(packetPath: string): boolean {
  return validatePacketDetailed(packetPath).isValid;
}
