import { intakeValidatedPackets } from "./runPacketIntake";

const sharedCorpusRoot = "shared-corpus";
const seasonWindow = "2000-2001";

const result = intakeValidatedPackets(sharedCorpusRoot, seasonWindow);
console.log("accepted:", result.accepted.length);
console.log("rejected:", result.rejected.length);
