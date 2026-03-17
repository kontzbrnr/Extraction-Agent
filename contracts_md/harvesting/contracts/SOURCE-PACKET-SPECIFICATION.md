SOURCE-PACKET-SPECIFICATION.md
Purpose
The Source Packet defines the canonical container used to transfer harvested narrative material from the Corpus Harvester system to the NTI Extraction Engine.
It functions as the interface contract between the Research Machine and the Extraction Machine.
The packet preserves:
* source traceability
* narrative texture
* metadata context
* raw textual material
The Source Packet is not responsible for analysis, interpretation, or summarization.
It exists solely to transport source material into the extraction pipeline in a consistent structure.

Packet Structure
Each harvested source is stored as a single packet directory.
source_packet/
    packet.json
    raw.txt
Optional future extensions may include additional files, but V1 requires only the above two.

packet.json
The packet.json file contains metadata describing the source.
Required fields:
{
  "packet_id": "",
  "source_title": "",
  "publication": "",
  "author": "",
  "date_published": "",
  "url": "",
  "season_window": "",
  "team_context": [],
  "narrative_tags": [],
  "harvest_timestamp": "",
  "harvester_version": ""
}

Field Definitions
packet_id
Unique identifier assigned at harvest time.
Must be deterministic within the corpus.
Example:
2001_MIN_beatt_article_014

source_title
Title of the article or source material.

publication
Name of the outlet or publication.
Examples:
ESPN
Star Tribune
New York Times
Sports Illustrated

author
Author of the article when available.

date_published
Original publication date of the material.
Format:
YYYY-MM-DD

url
Source location if the material was harvested from the web.
If the material was local or archived, this field may contain:
archive_reference

season_window
The season context used for the harvest directive.
Example:
2000–2001

team_context
List of teams referenced within the article if identifiable.
Example:
["Minnesota Vikings"]
Multiple teams are allowed.

narrative_tags
Optional rough classification tags applied during harvest.
Examples:
injury
contract
coaching
locker_room
scheme_change
transaction
These tags are non-binding hints only and must not influence extraction logic.
NTI performs independent narrative analysis.

harvest_timestamp
Timestamp when the packet was generated.
Example:
2026-03-11T14:23:11Z

harvester_version
Version identifier of the harvesting system.
Example:
DeepSearcher-V1

raw.txt
This file contains the full textual content of the source.
Rules:
• Preserve original language and tone• Preserve quotes and narrative phrasing• Avoid summarization or rewriting• Remove only obvious non-content artifacts (navigation, ads)
The goal is to retain maximum narrative texture.

Packet Directory Example
source_packet/
    packet.json
    raw.txt
Example directory name:
2001_MIN_coaching_instability_003/

Corpus Organization
Packets are stored inside a corpus directory.
Example:
corpus/

    2000_2001/

        packet_001/
        packet_002/
        packet_003/
Each packet is fully self-contained.
NTI may process packets in any order.

Determinism Requirements
The packet format must remain stable.
Future system changes must not alter:
* packet field names
* required file structure
* raw text preservation rules
Version upgrades must be introduced via new packet versions rather than modification of V1.

Non-Responsibilities of the Packet
The packet must not:
• summarize the article• infer narrative meaning• cluster articles• deduplicate narrative arcs• perform extraction logic
These responsibilities belong exclusively to NTI and downstream agents.

Handoff Boundary
Source Packets represent the handoff boundary between the research machine and the extraction engine.
Once packets are generated, they are placed in the shared corpus directory where NTI can begin processing.

V1 Design Philosophy
The packet intentionally prioritizes:
traceability
simplicity
raw narrative preservation
deterministic structure
It is designed to support future system upgrades without requiring changes to the extraction pipeline.

Status
LOCKED — SOURCE_PACKET_V1
