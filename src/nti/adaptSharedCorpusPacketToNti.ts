import { SharedCorpusPacket } from "./loadSharedCorpusPacket";

export type NtiSourceDocument = {
  sourceId: string;
  sourceType: "harvest_packet";
  seasonWindow: string;
  title: string;
  publication: string;
  author: string;
  url: string;
  rawText: string;
  teamContext: string[];
  narrativeTags: string[];
};

export function adaptSharedCorpusPacketToNti(
  packet: SharedCorpusPacket
): NtiSourceDocument {
  return {
    sourceId: packet.packetId,
    sourceType: "harvest_packet",
    seasonWindow: packet.metadata.season_window || "",
    title: packet.metadata.source_title || "",
    publication: packet.metadata.publication || "",
    author: packet.metadata.author || "",
    url: packet.metadata.url || "",
    rawText: packet.rawText,
    teamContext: packet.metadata.team_context || [],
    narrativeTags: packet.metadata.narrative_tags || [],
  };
}