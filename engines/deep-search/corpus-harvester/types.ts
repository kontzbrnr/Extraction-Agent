export type HarvestPassName =
  | "narrative_texture"
  | "media_reaction"
  | "conflict_event"
  | "structural_context"
  | "anomaly"
  | "general_discovery";

export interface HarvestQuerySet {
  passName: HarvestPassName;
  queries: string[];
}

export interface HarvestDirective {
  seasonWindow: string;
  targetMinSources: number;
  targetMaxSources: number;
  outputRoot: string;
  harvesterVersion: string;
}

export interface SearchResult {
  title: string;
  publication: string;
  author?: string;
  datePublished?: string;
  url: string;
  rawText: string;
  teamContext?: string[];
  narrativeTags?: string[];
}

export interface SourcePacketMetadata {
  packet_id: string;
  source_title: string;
  publication: string;
  author: string;
  date_published: string;
  url: string;
  season_window: string;
  team_context: string[];
  narrative_tags: string[];
  harvest_timestamp: string;
  harvester_version: string;
}

export interface BuiltSourcePacket {
  packetDirName: string;
  metadata: SourcePacketMetadata;
  rawText: string;
}

export interface ValidationResult {
  isValid: boolean;
  reasons: string[];
}
