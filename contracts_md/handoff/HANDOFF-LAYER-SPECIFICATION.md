HANDOFF LAYER SPECIFICATION — V1
Purpose
The Handoff Layer defines the filesystem boundary between the Corpus Harvester system and the NTI Extraction Engine.
It ensures that harvested Source Packets can be transferred from the Research Machine to the Extraction Machine without altering packet structure or metadata.
The handoff layer does not perform analysis or transformation.Its responsibility is strictly packet delivery.

Architectural Model
The research system and extraction system operate as separate machines.

Research Machine
    ↓
Source Packet Builder
    ↓
Shared Corpus Directory
    ↓
NTI Intake
    ↓
Extraction Pipeline

The Shared Corpus Directory is the handoff boundary.

Shared Corpus Directory
All completed Source Packets are written to:

/contentlib-docs/shared-corpus/

The directory is accessible to both systems.
Example structure:

/contentlib-docs/shared-corpus/

    2000_2001/

        packet_001/
            packet.json
            raw.txt

        packet_002/
            packet.json
            raw.txt

        packet_003/
            packet.json
            raw.txt

Each packet directory must conform to SOURCE_PACKET_V1.

Research Machine Responsibilities
The Corpus Harvester system must:
• generate packets conforming to SOURCE_PACKET_V1• write packets into the shared corpus directory• ensure packet directories are fully written before completion
Packets must never be partially written.
Once written, packets are considered immutable.

NTI Intake Responsibilities
The NTI system must:
• scan the shared corpus directory for new packets• ingest packets conforming to SOURCE_PACKET_V1• process packets independently
NTI must treat packets as read-only inputs.
The NTI system must never modify packet contents.

Packet Completion Rule
A packet is considered valid only when both files exist:

packet.json
raw.txt

NTI should ignore directories that do not contain both files.

Optional Completion Marker (Recommended)
To prevent NTI from ingesting partially written packets, the Research Machine may optionally create a completion marker:

_complete

Example:

packet_001/

    packet.json
    raw.txt
    _complete

NTI should only ingest packets containing the _complete marker.
This ensures packet integrity during ingestion.

Packet Processing Independence
NTI must treat each packet as an independent source.
The system must not assume:
• packet order• narrative relationships between packets• chronological packet sequencing
Narrative structure is discovered during extraction, not during handoff.

Deterministic Boundary
The handoff layer must remain stable.
Future upgrades to the harvester or crawler must not alter:
• packet structure• shared corpus directory structure• NTI ingestion expectations
This preserves long-term pipeline stability.

V1 Design Philosophy
The handoff layer is intentionally minimal.
It exists only to provide:

stable packet transfer
system modularity
deterministic ingestion

The design avoids unnecessary services, APIs, or orchestration layers.
Filesystem boundaries are sufficient for V1.

Status

LOCKED — HANDOFF_LAYER_V1


What You Now Have (Important Milestone)
At this point your entire research ingestion architecture is defined.
You now have:
1. Harvest Directive
Defines how the research agent gathers material
2. Source Packet Specification
Defines how research material is packaged
3. Handoff Layer
Defines how packets move into the extraction engine

Your Full Research → Extraction Pipeline Now Looks Like This

Harvest Directive
        ↓
DeepSearcher Research Agent
        ↓
Corpus Harvest
        ↓
Source Packet Builder
        ↓
Shared Corpus Directory
        ↓
NTI Intake
        ↓
Atomic Observation Extraction
        ↓
Canonical Ledger

This is a clean, modular architecture.
You can now upgrade any component independently.

