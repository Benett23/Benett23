import React from "react";
import { Composition } from "remotion";
import { ChristianClip, ClipProps } from "./ChristianClip";

// Valeurs par défaut pour le studio Remotion
const defaultProps: ClipProps = {
  verse:
    "Car Dieu a tant aimé le monde qu'il a donné son Fils unique, " +
    "afin que quiconque croit en lui ne périsse point, " +
    "mais qu'il ait la vie éternelle.",
  reference: "Jean 3:16",
  theme: "amour",
  prayerTitle: "Prière d'amour",
  prayer:
    "Père, tu es amour. Remplis mon cœur de ton amour afin que je puisse " +
    "aimer mon prochain comme tu m'as aimé. " +
    "Que ta charité soit parfaite en moi. Amen.",
  includePrayer: true,
  musicFile: undefined,
  bgImage: undefined,
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* Clip portrait 9:16 — format Reels / TikTok / Shorts */}
      <Composition
        id="ChristianClip"
        component={ChristianClip}
        durationInFrames={30 * 20}   // 20 secondes @ 30fps
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultProps}
      />

      {/* Clip paysage 16:9 — format YouTube */}
      <Composition
        id="ChristianClipWide"
        component={ChristianClip}
        durationInFrames={30 * 20}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={defaultProps}
      />
    </>
  );
};
