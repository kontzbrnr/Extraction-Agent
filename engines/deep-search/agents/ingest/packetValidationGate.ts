import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "fs";
import * as path from "path";
import { ValidationResult } from "../agents/corpus-harvester/types";

const REQUIRED_FILES = ["packet.json", "raw.txt", "_complete"] as const;

const REQUIRED_METADATA_FIELDS = [
  "packet_id",
  "source_title",
  "publication",
  "date_published",
  "url",
  "season_window",
  "harvest_timestamp",
  "harvester_version",
] as const;

export function validatePacket(packetDir: string): ValidationResult {
  const reasons: string[] = [];

  for (const fileName of REQUIRED_FILES) {
    const filePath = path.join(packetDir, fileName);
    if (!existsSync(filePath)) {
      reasons.push(`missing_required_file:${fileName}`);
    }
  }

  let parsedPacketJson: Record<string, unknown> | null = null;
  const packetJsonPath = path.join(packetDir, "packet.json");

  if (existsSync(packetJsonPath)) {
    try {
      const raw = readFileSync(packetJsonPath, "utf-8");
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        reasons.push("packet_json_not_object");
      } else {
        parsedPacketJson = parsed as Record<string, unknown>;
      }
    } catch {
      reasons.push("packet_json_parse_error");
    }
  }

  if (parsedPacketJson) {
    for (const fieldName of REQUIRED_METADATA_FIELDS) {
      const value = parsedPacketJson[fieldName];
      if (value === undefined || value === null || String(value).trim().length === 0) {
        reasons.push(`missing_packet_field:${fieldName}`);
      }
    }
  }

  const rawTextPath = path.join(packetDir, "raw.txt");
  if (existsSync(rawTextPath)) {
    try {
      const rawText = readFileSync(rawTextPath, "utf-8");
      const trimmed = rawText.trim();
      if (trimmed.length === 0) {
        reasons.push("raw_txt_empty");
      }
      if (trimmed.length < 500) {
        reasons.push("raw_txt_below_min_length_500");
      }
    } catch {
      reasons.push("raw_txt_read_error");
    }
  }

  return {
    isValid: reasons.length === 0,
    reasons,
  };
}

export function moveRejectedPacket(
  packetDir: string,
  rejectedRoot: string,
  reasons: string[]
): string {
  mkdirSync(rejectedRoot, { recursive: true });

  const packetDirName = path.basename(packetDir);
  const destinationDir = path.join(rejectedRoot, packetDirName);

  renameSync(packetDir, destinationDir);

  const rejectionLog = {
    packetDirName,
    reasons,
    rejectedAt: new Date().toISOString(),
  };

  const rejectionLogPath = path.join(destinationDir, "rejection_log.json");
  writeFileSync(rejectionLogPath, `${JSON.stringify(rejectionLog, null, 2)}\n`, "utf-8");

  return destinationDir;
}
