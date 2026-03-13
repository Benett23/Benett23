/**
 * Rendu d'un seul clip via Remotion (appelé par le backend Python).
 *
 * Usage :
 *   node scripts/render-single.mjs '<json_props>' <outputFile> [compositionId]
 *
 * Exemple :
 *   node scripts/render-single.mjs \
 *     '{"verse":"Je puis tout…","reference":"Phil 4:13","theme":"force","includePrayer":false}' \
 *     out/clip_force.mp4 ChristianClip
 */

import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

async function main() {
  const rawProps   = process.argv[2];
  const outputFile = process.argv[3] || "out/clip.mp4";
  const compId     = process.argv[4] || "ChristianClip";

  if (!rawProps) {
    console.error("Usage: node render-single.mjs '<json_props>' <outputFile> [compositionId]");
    process.exit(1);
  }

  const inputProps = JSON.parse(rawProps);

  console.log(`[INFO] Bundling...`);
  const bundleLocation = await bundle({
    entryPoint: resolve(ROOT, "src/index.tsx"),
    webpackOverride: (config) => config,
  });

  const composition = await selectComposition({
    serveUrl: bundleLocation,
    id: compId,
    inputProps,
  });

  const outputLocation = resolve(ROOT, outputFile);
  console.log(`[RENDER] ${compId} → ${outputLocation}`);

  await renderMedia({
    composition,
    serveUrl: bundleLocation,
    codec: "h264",
    outputLocation,
    inputProps,
  });

  console.log(`[OK] ${outputLocation}`);
}

main().catch((err) => {
  console.error("[ERROR]", err);
  process.exit(1);
});
