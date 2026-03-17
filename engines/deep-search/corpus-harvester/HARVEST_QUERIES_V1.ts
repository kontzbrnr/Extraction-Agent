import { HarvestPassName, HarvestQuerySet } from "./types";

export const HARVEST_QUERIES_V1: HarvestQuerySet[] = [
  {
    passName: "narrative_texture",
    queries: [
      "NFL {seasonWindow} locker room tension local beat report",
      "NFL {seasonWindow} rumor mill team chemistry concern",
      "NFL {seasonWindow} fan sentiment tone shift column",
      "NFL {seasonWindow} media framing quarterback narrative",
      "NFL {seasonWindow} coaching pressure speculative coverage",
      "NFL {seasonWindow} insider notes morale narrative",
      "NFL {seasonWindow} local radio narrative momentum",
      "NFL {seasonWindow} beat writer speculation team direction",
      "NFL {seasonWindow} discourse volatility postgame narrative",
      "NFL {seasonWindow} expectation reset narrative coverage",
    ],
  },
  {
    passName: "media_reaction",
    queries: [
      "NFL {seasonWindow} controversial loss media reaction",
      "NFL {seasonWindow} fan backlash column",
      "NFL {seasonWindow} sports radio criticism coach",
      "NFL {seasonWindow} columnist criticism quarterback",
      "NFL {seasonWindow} postgame controversy analysis",
      "NFL {seasonWindow} media backlash coaching decision",
      "NFL {seasonWindow} columnist criticism team performance",
      "NFL {seasonWindow} press conference controversy reaction",
      "NFL {seasonWindow} media questioning team direction",
      "NFL {seasonWindow} journalist criticism front office decision"
    ],
  },
  {
    passName: "conflict_event",
    queries: [
      "NFL {seasonWindow} coach fired conflict report",
      "NFL {seasonWindow} player suspension disciplinary action",
      "NFL {seasonWindow} holdout contract dispute",
      "NFL {seasonWindow} front office public confrontation",
      "NFL {seasonWindow} trade demand locker room conflict",
      "NFL {seasonWindow} grievance filing team dispute",
      "NFL {seasonWindow} owner coach disagreement public",
      "NFL {seasonWindow} benching controversy press conference",
      "NFL {seasonWindow} penalty appeal league dispute",
      "NFL {seasonWindow} contract standoff negotiation breakdown",
    ],
  },
  {
    passName: "structural_context",
    queries: [
      "NFL {seasonWindow} salary cap implications roster planning",
      "NFL {seasonWindow} rule change competition committee impact",
      "NFL {seasonWindow} offensive scheme transition analysis",
      "NFL {seasonWindow} defensive coordinator philosophy change",
      "NFL {seasonWindow} general manager replacement strategy",
      "NFL {seasonWindow} labor context CBA roster decisions",
      "NFL {seasonWindow} draft capital restructuring front office",
      "NFL {seasonWindow} organizational restructure football operations",
      "NFL {seasonWindow} analytics adoption team process",
      "NFL {seasonWindow} injury policy procedural change",
    ],
  },
  {
    passName: "anomaly",
    queries: [
      "NFL {seasonWindow} scandal investigation unusual incident",
      "NFL {seasonWindow} referee controversy disputed ruling",
      "NFL {seasonWindow} ownership dispute legal conflict",
      "NFL {seasonWindow} unexpected coaching decision backlash",
      "NFL {seasonWindow} league intervention disciplinary anomaly",
      "NFL {seasonWindow} emergency roster decision controversy",
      "NFL {seasonWindow} public apology organizational crisis",
      "NFL {seasonWindow} compliance breach team response",
      "NFL {seasonWindow} unprecedented game management controversy",
      "NFL {seasonWindow} governance controversy league statement",
    ],
  },
  {
    passName: "general_discovery",
    queries: [
      "NFL {seasonWindow} season overview underreported teams",
      "NFL {seasonWindow} alternate outlet team narrative",
      "NFL {seasonWindow} regional publication franchise storyline",
      "NFL {seasonWindow} independent media team development",
      "NFL {seasonWindow} broad sweep team dynamics",
      "NFL {seasonWindow} overlooked roster storyline",
      "NFL {seasonWindow} underrepresented market coverage",
      "NFL {seasonWindow} longform narrative feature team",
      "NFL {seasonWindow} season context by division outlets",
      "NFL {seasonWindow} emerging narrative local publications",
    ],
  },
];

export function buildQueriesForSeason(seasonWindow: string): HarvestQuerySet[] {
  return HARVEST_QUERIES_V1.map((querySet) => ({
    passName: querySet.passName,
    queries: querySet.queries.map((query) =>
      query.split("{seasonWindow}").join(seasonWindow)
    ),
  }));
}

export function flattenQueriesForSeason(
  seasonWindow: string
): { passName: HarvestPassName; query: string }[] {
  const built = buildQueriesForSeason(seasonWindow);
  return built.flatMap((querySet) =>
    querySet.queries.map((query) => ({
      passName: querySet.passName,
      query,
    }))
  );
}
