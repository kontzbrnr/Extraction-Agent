import { runNtiFromSharedCorpus } from "./runNtiFromSharedCorpus";

const season = process.argv[2];

if (!season) {
  console.error("Usage: npm run nti <season>");
  process.exit(1);
}

runNtiFromSharedCorpus(season);