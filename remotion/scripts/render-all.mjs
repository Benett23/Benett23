/**
 * Script de rendu batch pour les clips chrétiens.
 * Lit un fichier JSON de paramètres et rend chaque clip via Remotion.
 *
 * Usage :
 *   node scripts/render-all.mjs [params.json]
 *
 * Format de params.json :
 * [
 *   {
 *     "verse": "...",
 *     "reference": "Jean 3:16",
 *     "theme": "amour",
 *     "prayerTitle": "Prière d'amour",
 *     "prayer": "...",
 *     "includePrayer": true,
 *     "musicFile": "worship.mp3",
 *     "bgImage": "nature.jpg",
 *     "outputFile": "out/clip_amour.mp4",
 *     "compositionId": "ChristianClip"
 *   }
 * ]
 */

import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

async function renderClip(params, bundleLocation) {
  const {
    verse,
    reference,
    theme = "foi",
    prayerTitle = "Prière",
    prayer = "",
    includePrayer = true,
    musicFile,
    bgImage,
    outputFile = `out/clip_${theme}_${Date.now()}.mp4`,
    compositionId = "ChristianClip",
  } = params;

  const inputProps = { verse, reference, theme, prayerTitle, prayer, includePrayer, musicFile, bgImage };

  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: compositionId,
    inputProps,
  });

  console.log(`[RENDER] ${compositionId} → ${outputFile}`);
  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation: resolve(ROOT, outputFile),
    inputProps,
  });
  console.log(`[OK]     ${outputFile}`);
}

async function main() {
  const paramsFile = process.argv[2] || resolve(ROOT, "render-params.json");

  let clips = [];
  if (existsSync(paramsFile)) {
    clips = JSON.parse(readFileSync(paramsFile, "utf8"));
  } else {
    // Exemple par défaut
    clips = [
      {
        verse: "Car Dieu a tant aimé le monde…",
        reference: "Jean 3:16",
        theme: "amour",
        prayerTitle: "Prière d'amour",
        prayer: "Père, tu es amour…",
        includePrayer: true,
        outputFile: "out/clip_amour.mp4",
      },
    ];
  }

  console.log(`[INFO] Bundling Remotion entry point...`);
  const bundleLocation = await bundle({
    entryPoint: resolve(ROOT, "src/index.tsx"),
    webpackOverride: (config) => config,
  });

  for (const clip of clips) {
    await renderClip(clip, bundleLocation);
  }

  console.log("[DONE] Tous les clips ont été rendus.");
}

main().catch((err) => {
  console.error("[ERROR]", err);
  process.exit(1);
});
