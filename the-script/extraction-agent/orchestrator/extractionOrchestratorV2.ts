import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

export type NtiSourceDocument = {
  sourceId: string;
  sourceType?: "harvest_packet" | string;
  seasonWindow?: string;
  title?: string;
  publication?: string;
  author?: string;
  url?: string;
  rawText: string;
  teamContext?: string[];
  narrativeTags?: string[];
};

export type ExtractionOrchestratorResult = {
  sourceId: string;
  sourceReference: string;
  rec: Record<string, unknown> | null;
  atomicUnits: Array<Record<string, unknown>>;
  pcrs: Array<Record<string, unknown>>;
  splitRejections: Array<Record<string, unknown>>;
  pressureLane: {
    ploRecords: Array<Record<string, unknown>>;
    cpsObjects: Array<Record<string, unknown>>;
    cpsRejections: Array<Record<string, unknown>>;
    cpsAudit: Array<Record<string, unknown>>;
  };
  narrativeLane: {
    ncaInputs: Array<Record<string, unknown>>;
    ncaAccepted: Array<Record<string, unknown>>;
    ncaRejected: Array<Record<string, unknown>>;
    santaInputs: Array<Record<string, unknown>>;
    csnObjects: Array<Record<string, unknown>>;
    csnRejections: Array<Record<string, unknown>>;
  };
  stageStatus: {
    recProduced: boolean;
    splitExecuted: boolean;
    pressureLaneExecuted: boolean;
    narrativeLaneExecuted: boolean;
  };
};

const PROJECT_ROOT = path.resolve(__dirname, "../../..");
const PYTHON_BRIDGE = String.raw`
import asyncio
import importlib
import inspect
import json
import os
import sys

project_root = sys.argv[1]
module_name = sys.argv[2]
function_name = sys.argv[3]
raw_args = sys.stdin.read() or "[]"

sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "engines", "research-agent", "agents"))

module = importlib.import_module(module_name)
func = getattr(module, function_name)
args = json.loads(raw_args)

try:
    result = func(*args)
    if inspect.isawaitable(result):
        result = asyncio.run(result)
    print(json.dumps({"ok": True, "result": result}, ensure_ascii=False))
except Exception as exc:
    print(json.dumps({
        "ok": False,
        "error": {
            "type": type(exc).__name__,
            "message": str(exc),
        },
    }, ensure_ascii=False))
`;

function resolvePythonExecutable(): string {
  const workspacePython = path.join(PROJECT_ROOT, ".venv", "bin", "python");
  if (existsSync(workspacePython)) {
    return workspacePython;
  }
  return "python3";
}

async function callPythonFunction<T>(
  moduleName: string,
  functionName: string,
  args: unknown[]
): Promise<T> {
  const stdout = execFileSync(
    resolvePythonExecutable(),
    ["-c", PYTHON_BRIDGE, PROJECT_ROOT, moduleName, functionName],
    {
      cwd: PROJECT_ROOT,
      encoding: "utf8",
      input: JSON.stringify(args),
      maxBuffer: 10 * 1024 * 1024,
    }
  );

  const parsed = JSON.parse(stdout) as
    | { ok: true; result: T }
    | { ok: false; error: { type: string; message: string } };

  if (!parsed.ok) {
    throw new Error(`${parsed.error.type}: ${parsed.error.message}`);
  }

  return parsed.result;
}

export async function runExtractionOrchestratorV2(
  input: NtiSourceDocument
): Promise<ExtractionOrchestratorResult> {
  const sourceReference = input.sourceId;

  console.log(`Extraction orchestrator start: ${input.sourceId}`);

  let rec: Record<string, unknown> | null = null;

  try {
    rec = await callPythonFunction<Record<string, unknown>>(
      "engines.research_agent.agents.extraction.rec_producer",
      "produce_rec",
      [input.rawText, false]
    );
    console.log("REC success");
  } catch {
    console.log("REC fail");
    return {
      sourceId: input.sourceId,
      sourceReference,
      rec: null,
      atomicUnits: [],
      pcrs: [],
      splitRejections: [],
      pressureLane: {
        ploRecords: [],
        cpsObjects: [],
        cpsRejections: [],
        cpsAudit: [],
      },
      narrativeLane: {
        ncaInputs: [],
        ncaAccepted: [],
        ncaRejected: [],
        santaInputs: [],
        csnObjects: [],
        csnRejections: [],
      },
      stageStatus: {
        recProduced: false,
        splitExecuted: false,
        pressureLaneExecuted: false,
        narrativeLaneExecuted: false,
      },
    };
  }

  let atomicUnits: Array<Record<string, unknown>> = [];
  let pcrs: Array<Record<string, unknown>> = [];
  let splitRejections: Array<Record<string, unknown>> = [];

  try {
    const splitResult = await callPythonFunction<[
      Array<Record<string, unknown>>,
      Array<Record<string, unknown>>,
      Array<Record<string, unknown>>
    ]>(
      "engines.research_agent.agents.gsd.split_mechanics",
      "split_rec",
      [rec, sourceReference]
    );
    atomicUnits = Array.isArray(splitResult[0]) ? splitResult[0] : [];
    pcrs = Array.isArray(splitResult[1]) ? splitResult[1] : [];
    splitRejections = Array.isArray(splitResult[2]) ? splitResult[2] : [];
  } catch {
    atomicUnits = [];
    pcrs = [];
    splitRejections = [];
  }

  console.log(
    `Split counts: aus=${atomicUnits.length} pcrs=${pcrs.length} rejections=${splitRejections.length}`
  );

  const ploRecords: Array<Record<string, unknown>> = [];
  const cpsObjects: Array<Record<string, unknown>> = [];
  const cpsRejections: Array<Record<string, unknown>> = [];
  const cpsAudit: Array<Record<string, unknown>> = [];

  for (const atomicUnit of atomicUnits) {
    try {
      const ploResult = await callPythonFunction<[
        boolean,
        Record<string, unknown> | null,
        Record<string, unknown> | null,
        Record<string, unknown>
      ]>(
        "engines.research_agent.agents.pressure.plo_e",
        "enforce_plo_e",
        [atomicUnit, null, sourceReference]
      );

      const ploRecord = ploResult[1];
      if (ploRecord) {
        ploRecords.push(ploRecord);

        try {
          const pstaResult = await callPythonFunction<[
            Array<Record<string, unknown>>,
            Array<Record<string, unknown>>,
            Record<string, unknown>
          ]>(
            "engines.research_agent.agents.pressure.psta",
            "enforce_psta",
            [ploRecord]
          );

          const pstaObjects = Array.isArray(pstaResult[0]) ? pstaResult[0] : [];
          const pstaRejections = Array.isArray(pstaResult[1]) ? pstaResult[1] : [];
          const pstaAudit = pstaResult[2];

          for (const object of pstaObjects) {
            cpsObjects.push(object);
          }

          for (const rejection of pstaRejections) {
            cpsRejections.push(rejection);
          }

          if (pstaAudit && typeof pstaAudit === "object") {
            cpsAudit.push(pstaAudit);
          }
        } catch (pstaError) {
          cpsRejections.push({
            error: pstaError instanceof Error ? pstaError.message : String(pstaError),
          });
        }
      }
    } catch {
      continue;
    }
  }

  const ncaInputs: Array<Record<string, unknown>> = [];
  const ncaAccepted: Array<Record<string, unknown>> = [];
  const ncaRejected: Array<Record<string, unknown>> = [];
  const santaInputs: Array<Record<string, unknown>> = [];
  const csnObjects: Array<Record<string, unknown>> = [];
  const csnRejections: Array<Record<string, unknown>> = [];

  for (const atomicUnit of atomicUnits) {
    const eventCandidate: Record<string, unknown> = {
      eventDescription: atomicUnit.text ?? "",
      sourceReference,
      timestampContext: "unknown",
      actorRole: null,
      action: null,
      objectRole: null,
      contextRole: null,
    };

    ncaInputs.push(eventCandidate);

    try {
      const ncaResult = await callPythonFunction<[
        boolean,
        Record<string, unknown> | null,
        Record<string, unknown> | null
      ]>(
        "engines.research_agent.agents.nca.nca_agent",
        "enforce_nca",
        [eventCandidate]
      );

      const ncaPassed = Boolean(ncaResult[0]);
      const ncaRejection = ncaResult[1];
      const ncaAcceptedResult = ncaResult[2];

      if (!ncaPassed) {
        ncaRejected.push(
          ncaRejection && typeof ncaRejection === "object"
            ? ncaRejection
            : { rejection: ncaRejection ?? null }
        );
        continue;
      }

      if (ncaAcceptedResult && typeof ncaAcceptedResult === "object") {
        ncaAccepted.push(ncaAcceptedResult);
      }

      if (
        ncaAcceptedResult &&
        typeof ncaAcceptedResult === "object" &&
        ncaAcceptedResult.classification === "CSN"
      ) {
        const santaInput: Record<string, unknown> = {
          ...eventCandidate,
          classification: "CSN",
          standaloneSubclass: ncaAcceptedResult.standaloneSubclass,
        };

        santaInputs.push(santaInput);

        try {
          const santaResult = await callPythonFunction<[
            boolean,
            Record<string, unknown> | null,
            Record<string, unknown> | null
          ]>(
            "engines.research_agent.agents.santa.santa_agent",
            "enforce_santa",
            [santaInput]
          );

          const santaPassed = Boolean(santaResult[0]);
          const santaRejection = santaResult[1];
          const santaAcceptedResult = santaResult[2];

          if (santaPassed && santaAcceptedResult && typeof santaAcceptedResult === "object") {
            const canonicalObject = santaAcceptedResult.canonicalObject;
            if (canonicalObject && typeof canonicalObject === "object") {
              csnObjects.push(canonicalObject as Record<string, unknown>);
            }
          } else if (santaRejection && typeof santaRejection === "object") {
            csnRejections.push(santaRejection);
          } else {
            csnRejections.push({ rejection: santaRejection ?? null });
          }
        } catch (santaError) {
          csnRejections.push({
            error: santaError instanceof Error ? santaError.message : String(santaError),
          });
        }
      }
    } catch (ncaError) {
      ncaRejected.push({
        error: ncaError instanceof Error ? ncaError.message : String(ncaError),
      });
    }
  }

  console.log(`CPS count: ${cpsObjects.length}`);
  console.log(`CSN count: ${csnObjects.length}`);

  return {
    sourceId: input.sourceId,
    sourceReference,
    rec,
    atomicUnits,
    pcrs,
    splitRejections,
    pressureLane: {
      ploRecords,
      cpsObjects,
      cpsRejections,
      cpsAudit,
    },
    narrativeLane: {
      ncaInputs,
      ncaAccepted,
      ncaRejected,
      santaInputs,
      csnObjects,
      csnRejections,
    },
    stageStatus: {
      recProduced: !!rec,
      splitExecuted: true,
      pressureLaneExecuted: true,
      narrativeLaneExecuted: true,
    },
  };
}


export async function runExtractionPipeline(
  input: NtiSourceDocument
): Promise<ExtractionOrchestratorResult> {
  return runExtractionOrchestratorV2(input);
}
