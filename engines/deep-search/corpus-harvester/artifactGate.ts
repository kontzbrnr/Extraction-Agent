import * as fs from "fs";
import * as path from "path";
import { createHash } from "crypto";
import { BuiltSourcePacket } from "./types";

export type ArtifactDecision = "accept" | "extend" | "reject";

const REGISTRY_PATH = path.join(process.cwd(), "artifactRegistry.json");

function loadRegistry(): Set<string> {
  if (!fs.existsSync(REGISTRY_PATH)) {
    fs.writeFileSync(REGISTRY_PATH, "[]\n", "utf8");
    return new Set<string>();
  }

  const raw = fs.readFileSync(REGISTRY_PATH, "utf8").trim();
  if (raw.length === 0) {
    return new Set<string>();
  }

  const data: unknown = JSON.parse(raw);
  if (!Array.isArray(data)) {
    return new Set<string>();
  }

  return new Set(data.map((value) => String(value)));
}

function saveRegistry(registry: Set<string>): void {
  fs.writeFileSync(REGISTRY_PATH, `${JSON.stringify([...registry], null, 2)}\n`, "utf8");
}

function fingerprint(text: string): string {
  return createHash("sha256").update(text).digest("hex");
}

export function artifactGate(packet: BuiltSourcePacket): ArtifactDecision {
  console.log(
    "[ArtifactGate] temporarily bypassed:",
    packet.metadata?.url || packet.packetDirName
  );
  return "accept";
}
