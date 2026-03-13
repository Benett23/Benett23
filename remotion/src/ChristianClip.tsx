import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ClipProps {
  verse: string;
  reference: string;
  theme: string;
  prayerTitle?: string;
  prayer?: string;
  includePrayer?: boolean;
  musicFile?: string; // chemin relatif dans public/music/
  bgImage?: string;   // chemin relatif dans public/images/
}

// ---------------------------------------------------------------------------
// Palettes de couleurs par thème
// ---------------------------------------------------------------------------

const THEME_COLORS: Record<string, { top: string; bottom: string; accent: string }> = {
  foi:      { top: "#1e3c72", bottom: "#2a5298", accent: "#ffd700" },
  espoir:   { top: "#134e5e", bottom: "#71b280", accent: "#90ee90" },
  amour:    { top: "#b21f1f", bottom: "#fdbb2d", accent: "#ff8c69" },
  paix:     { top: "#1c6fa4", bottom: "#4bb5e0", accent: "#e0f4ff" },
  force:    { top: "#4e342e", bottom: "#a1887f", accent: "#ffd700" },
  "grâce":  { top: "#6a0572", bottom: "#ab47bc", accent: "#e040fb" },
  louange:  { top: "#7b3f00", bottom: "#e6a817", accent: "#fff176" },
  guérison: { top: "#004d40", bottom: "#26a69a", accent: "#b2dfdb" },
};

const DEFAULT_COLORS = THEME_COLORS.foi;

// ---------------------------------------------------------------------------
// Helpers d'animation
// ---------------------------------------------------------------------------

function useFadeIn(startFrame: number, endFrame: number): number {
  const frame = useCurrentFrame();
  return interpolate(frame, [startFrame, endFrame], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.ease),
  });
}

function useSlideUp(startFrame: number, endFrame: number, distance = 40): number {
  const frame = useCurrentFrame();
  return interpolate(frame, [startFrame, endFrame], [distance, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.back(1.2)),
  });
}

// ---------------------------------------------------------------------------
// Sous-composants
// ---------------------------------------------------------------------------

const Cross: React.FC<{ opacity: number; accent: string }> = ({ opacity, accent }) => (
  <div
    style={{
      position: "absolute",
      top: 80,
      left: "50%",
      transform: "translateX(-50%)",
      opacity,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    }}
  >
    {/* Barre verticale */}
    <div
      style={{
        width: 12,
        height: 90,
        background: `linear-gradient(to bottom, transparent, ${accent}55, transparent)`,
        borderRadius: 6,
      }}
    />
    {/* Barre horizontale */}
    <div
      style={{
        width: 60,
        height: 10,
        marginTop: -56,
        background: `linear-gradient(to right, transparent, ${accent}55, transparent)`,
        borderRadius: 5,
      }}
    />
  </div>
);

const ThemeLabel: React.FC<{ theme: string; opacity: number; accent: string }> = ({
  theme,
  opacity,
  accent,
}) => (
  <div
    style={{
      position: "absolute",
      top: 220,
      width: "100%",
      textAlign: "center",
      opacity,
      fontFamily: "Georgia, serif",
      fontSize: 36,
      letterSpacing: 8,
      color: accent,
      textTransform: "uppercase",
      textShadow: `0 0 20px ${accent}88`,
    }}
  >
    {theme}
  </div>
);

const Divider: React.FC<{ opacity: number; accent: string }> = ({ opacity, accent }) => (
  <div
    style={{
      position: "absolute",
      top: 290,
      left: "10%",
      right: "10%",
      height: 1,
      opacity,
      background: `linear-gradient(to right, transparent, ${accent}66, transparent)`,
    }}
  />
);

const VerseBlock: React.FC<{
  verse: string;
  reference: string;
  opacity: number;
  translateY: number;
  accent: string;
}> = ({ verse, reference, opacity, translateY, accent }) => (
  <div
    style={{
      position: "absolute",
      top: 340,
      left: "8%",
      right: "8%",
      opacity,
      transform: `translateY(${translateY}px)`,
      textAlign: "center",
    }}
  >
    <p
      style={{
        fontFamily: "Georgia, serif",
        fontSize: 38,
        lineHeight: 1.6,
        color: "rgba(255,255,255,0.92)",
        fontStyle: "italic",
        margin: 0,
        textShadow: "0 2px 8px rgba(0,0,0,0.5)",
      }}
    >
      « {verse} »
    </p>
    <p
      style={{
        marginTop: 24,
        fontFamily: "Georgia, serif",
        fontSize: 30,
        color: accent,
        fontWeight: "bold",
        textShadow: `0 0 12px ${accent}66`,
      }}
    >
      — {reference}
    </p>
  </div>
);

const PrayerBlock: React.FC<{
  title: string;
  text: string;
  opacity: number;
  translateY: number;
  accent: string;
}> = ({ title, text, opacity, translateY, accent }) => (
  <div
    style={{
      position: "absolute",
      bottom: 140,
      left: "8%",
      right: "8%",
      opacity,
      transform: `translateY(${translateY}px)`,
      textAlign: "center",
      borderTop: `1px solid ${accent}33`,
      paddingTop: 28,
    }}
  >
    <p
      style={{
        fontFamily: "Arial, sans-serif",
        fontSize: 26,
        color: accent,
        fontWeight: "bold",
        marginBottom: 14,
        letterSpacing: 2,
        textTransform: "uppercase",
      }}
    >
      {title}
    </p>
    <p
      style={{
        fontFamily: "Georgia, serif",
        fontSize: 30,
        lineHeight: 1.65,
        color: "rgba(220,220,255,0.88)",
        margin: 0,
        fontStyle: "italic",
      }}
    >
      {text}
    </p>
  </div>
);

const Watermark: React.FC<{ opacity: number }> = ({ opacity }) => (
  <div
    style={{
      position: "absolute",
      bottom: 48,
      width: "100%",
      textAlign: "center",
      opacity,
      fontFamily: "Arial, sans-serif",
      fontSize: 22,
      color: "rgba(255,255,255,0.4)",
      letterSpacing: 3,
    }}
  >
    ✝  Parole de Vie
  </div>
);

// ---------------------------------------------------------------------------
// Composant principal
// ---------------------------------------------------------------------------

export const ChristianClip: React.FC<ClipProps> = ({
  verse,
  reference,
  theme,
  prayerTitle = "Prière",
  prayer = "",
  includePrayer = true,
  musicFile,
  bgImage,
}) => {
  const { fps, durationInFrames } = useVideoConfig();

  const colors = THEME_COLORS[theme] ?? DEFAULT_COLORS;

  // Timings (en frames)
  const crossFade   = useFadeIn(0, fps * 0.8);
  const themeFade   = useFadeIn(fps * 0.5, fps * 1.2);
  const divFade     = useFadeIn(fps * 0.8, fps * 1.4);
  const verseOpacity = useFadeIn(fps * 1.2, fps * 2.2);
  const verseSlide  = useSlideUp(fps * 1.2, fps * 2.2);
  const prayerOpacity = useFadeIn(fps * 2.5, fps * 3.5);
  const prayerSlide = useSlideUp(fps * 2.5, fps * 3.5);
  const wmFade      = useFadeIn(fps * 3, fps * 4);

  // Fondu sortant (dernière seconde)
  const frame = useCurrentFrame();
  const fadeOutOpacity = interpolate(
    frame,
    [durationInFrames - fps, durationInFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(to bottom, ${colors.top}, ${colors.bottom})`,
        overflow: "hidden",
        opacity: fadeOutOpacity,
      }}
    >
      {/* Image de fond optionnelle */}
      {bgImage && (
        <AbsoluteFill
          style={{
            backgroundImage: `url(${staticFile(`images/${bgImage}`)})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
            opacity: 0.25,
          }}
        />
      )}

      {/* Overlay sombre pour lisibilité */}
      <AbsoluteFill style={{ background: "rgba(0,0,0,0.38)" }} />

      {/* Musique */}
      {musicFile && (
        <Audio
          src={staticFile(`music/${musicFile}`)}
          volume={(f) =>
            interpolate(
              f,
              [0, fps, durationInFrames - fps * 2, durationInFrames],
              [0, 0.6, 0.6, 0],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
            )
          }
        />
      )}

      {/* Éléments visuels */}
      <Cross opacity={crossFade} accent={colors.accent} />
      <ThemeLabel theme={theme} opacity={themeFade} accent={colors.accent} />
      <Divider opacity={divFade} accent={colors.accent} />

      <VerseBlock
        verse={verse}
        reference={reference}
        opacity={verseOpacity}
        translateY={verseSlide}
        accent={colors.accent}
      />

      {includePrayer && prayer && (
        <PrayerBlock
          title={prayerTitle}
          text={prayer}
          opacity={prayerOpacity}
          translateY={prayerSlide}
          accent={colors.accent}
        />
      )}

      <Watermark opacity={wmFade} />
    </AbsoluteFill>
  );
};
