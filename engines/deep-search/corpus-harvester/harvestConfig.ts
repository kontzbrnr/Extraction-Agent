import { readFileSync } from "fs";
import path from "path";
import { HarvestDirective } from "./types";

export interface HarvestRuntimeConfig {
  directive: HarvestDirective;
  querySetReference: "HARVEST_QUERIES_V1";
  braveApiKeyEnvVar: string;
  rateLimits: {
    braveRequestsPerMinute: number;
    articleFetchMaxConcurrent: number;
    articleFetchPerDomainCooldownMs: number;
  };
}

const DEFAULT_CONFIG_PATH = "engines/deep-search/corpus-harvester/harvest.config.json";

export function loadHarvestRuntimeConfig(configPathArg?: string): HarvestRuntimeConfig {
  const configPath = configPathArg || process.env.HARVEST_CONFIG_PATH || DEFAULT_CONFIG_PATH;
  const resolvedPath = path.isAbsolute(configPath)
    ? configPath
    : path.join(process.cwd(), configPath);

  const raw = readFileSync(resolvedPath, "utf-8");
  const parsed = JSON.parse(raw) as Partial<HarvestRuntimeConfig["directive"]> & {
    querySetReference?: string;
    braveApiKeyEnvVar?: string;
    rateLimits?: Partial<HarvestRuntimeConfig["rateLimits"]>;
  };

  const directive: HarvestDirective = {
    seasonWindow: String(parsed.seasonWindow ?? "2000-2001"),
    targetMinSources: Number(parsed.targetMinSources ?? 30),
    targetMaxSources: Number(parsed.targetMaxSources ?? 40),
    outputRoot: String(parsed.outputRoot ?? "shared-corpus"),
    harvesterVersion: String(parsed.harvesterVersion ?? "DeepSearcher-V1"),
  };

  if (parsed.querySetReference && parsed.querySetReference !== "HARVEST_QUERIES_V1") {
    throw new Error(
      `Unsupported querySetReference: ${parsed.querySetReference}. Supported: HARVEST_QUERIES_V1`
    );
  }

  const braveApiKeyEnvVar = String(parsed.braveApiKeyEnvVar ?? "BRAVE_API_KEY").trim() || "BRAVE_API_KEY";
  const rateLimits = {
    braveRequestsPerMinute: Math.max(1, Number(parsed.rateLimits?.braveRequestsPerMinute ?? 20)),
    articleFetchMaxConcurrent: Math.max(1, Number(parsed.rateLimits?.articleFetchMaxConcurrent ?? 4)),
    articleFetchPerDomainCooldownMs: Math.max(0, Number(parsed.rateLimits?.articleFetchPerDomainCooldownMs ?? 1000)),
  };

  process.env.BRAVE_API_KEY_ENV_VAR = braveApiKeyEnvVar;

  return {
    directive,
    querySetReference: "HARVEST_QUERIES_V1",
    braveApiKeyEnvVar,
    rateLimits,
  };
}
