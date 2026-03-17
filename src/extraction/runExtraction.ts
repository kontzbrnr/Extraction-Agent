import { runExtractionOrchestratorV2 } from "the-script/extraction-agent/orchestrator/extractionOrchestratorV2";

export async function runExtraction(doc: any) {
  const result = await runExtractionOrchestratorV2(doc);

  console.log("[Extraction Result]", {
    sourceId: result.sourceId,
    stageStatus: result.stageStatus,
    pressureLaneCount: result.pressureLane?.cpsObjects?.length || 0,
    narrativeLaneCount: result.narrativeLane?.csnObjects?.length || 0,
  });

  return result;
}