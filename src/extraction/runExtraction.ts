import {
  NtiSourceDocument,
  runExtractionPipeline,
} from "../../the-script/extraction-agent/orchestrator/extractionOrchestratorV2";

export async function runExtraction(doc: NtiSourceDocument) {
  return runExtractionPipeline(doc);
}
