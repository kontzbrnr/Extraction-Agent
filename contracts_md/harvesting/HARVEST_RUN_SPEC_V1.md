HARVEST_RUN_SPEC_V1
Harvest Execution Contract v1.0

--

Run Objective

Execute a season-level narrative corpus harvest using the
SEASON_CORPUS_HARVEST directive. The run collects narrative-relevant
reporting sources within the defined season window and produces a
validated corpus suitable for Narrative Texture Intake (NTI).

--

Directive Binding

Directive File

contracts_md/harvesting/SEASON_CORPUS_HARVEST_DIRECTIVE_v1.md

The directive governs discovery scope, narrative relevance,
perspective diversity, discourse preservation, and corpus completion.

The run spec does not redefine discovery behavior. It only defines
execution mechanics.

--

Run Inputs

season_window
Defined inside the directive.

target_range
Defined inside the directive.

search_engine
DeepSearch engine instance used for query execution.

output_paths

corpus_output
data/corpus/

run_metadata
data/runs/

source_packets
data/packets/

--

Execution Pipeline

1. Load Harvest Directive

Load the directive specified in Directive Binding.
Parse season window, target range, and discovery guidance.

2. Execute Search Expansion

Generate query sets derived from directive elements,
including narrative discovery targets and reporting environments.

Execute DeepSearch queries within the defined season window.

3. Build Source Packets

For each discovered source, construct a source packet containing:

• title
• publication
• author (if available)
• publication date
• url
• source type (national, beat, column, feature, etc.)
• extracted article content
• preliminary narrative relevance indicators

Source packets represent the raw acquisition layer prior to validation.

4. Run Packet Validation Gate

Evaluate each packet for:

• duplicate article detection
• narrative relevance
• sufficient textual content
• eligibility within the season window

Packets failing validation are discarded.

Accepted packets proceed to corpus construction.

5. Write to Corpus

Validated packets are written to the season corpus.

Corpus artifacts should contain:

• source metadata
• narrative excerpts
• contextual summary
• preserved narrative language

The corpus should reflect the narrative discourse environment
surrounding the season.

6. Trigger NTI Intake

Once corpus completion conditions are met,
trigger Narrative Texture Intake (NTI).

NTI processes corpus artifacts into narrative observation units
for downstream transformation and canonicalization.

--

Stopping Conditions

The run terminates when one of the following occurs:

• the corpus reaches the upper bound of the directive target range
• narrative saturation is detected according to directive criteria

Narrative saturation occurs when continued discovery produces
sources that substantially repeat previously captured narrative
situations without introducing new narrative material.

--

Artifacts Produced

corpus artifacts

data/corpus/{season_id}_corpus.json

source packets

data/packets/{run_id}_packets.json

run metadata

data/runs/{run_id}.json

Run metadata must include:

• run_id
• directive used
• season window
• sources collected
• packets rejected
• termination condition

--

Downstream Trigger

After corpus completion, NTI intake is triggered.

NTI converts corpus material into narrative texture observations
for later transformation and canonicalization layers.

--

End of Run Spec