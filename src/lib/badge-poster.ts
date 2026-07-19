import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";
import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import type { PosterTile } from "./badges";

const require = createRequire(import.meta.url);

// Brand palette — the same navy / cream / gold the badge medallions are painted in.
const NAVY = "#0d1836";
const NAVY_DEEP = "#080f28";
const CREAM = "#f5efe0";
const CREAM_MUTED = "#c3cbe0";
const GOLD = "#e8b64a";
const HAIRLINE = "rgba(245, 239, 224, 0.14)";
const TILE_BG = "rgba(255, 255, 255, 0.05)";

const WIDTH = 1200;
const HEIGHT = 630;

/** Read one vendored @fontsource `.woff` (satori reads ttf/otf/woff, not woff2). */
function fontFile(pkg: string, file: string): Buffer {
  return readFileSync(require.resolve(`${pkg}/files/${file}`));
}

// Loaded once per build process.
let fontsCache: Parameters<typeof satori>[1]["fonts"] | null = null;
function fonts() {
  if (fontsCache) return fontsCache;
  fontsCache = [
    {
      name: "DM Sans",
      data: fontFile("@fontsource/dm-sans", "dm-sans-latin-400-normal.woff"),
      weight: 400,
      style: "normal",
    },
    {
      name: "DM Sans",
      data: fontFile("@fontsource/dm-sans", "dm-sans-latin-700-normal.woff"),
      weight: 700,
      style: "normal",
    },
    {
      name: "JetBrains Mono",
      data: fontFile(
        "@fontsource/jetbrains-mono",
        "jetbrains-mono-latin-500-normal.woff",
      ),
      weight: 500,
      style: "normal",
    },
  ];
  return fontsCache;
}

const badgeCache = new Map<string, string>();
/** Inline a badge medallion PNG as a data URI (satori can't fetch by URL at build). */
function badgeDataUri(image: string): string {
  const cached = badgeCache.get(image);
  if (cached) return cached;
  const buf = readFileSync(join(process.cwd(), "public", "badges", `${image}.png`));
  const uri = `data:image/png;base64,${buf.toString("base64")}`;
  badgeCache.set(image, uri);
  return uri;
}

export interface PosterInput {
  login: string;
  title: string;
  image: string;
  caption: string;
  tiles: PosterTile[];
  siteLabel: string;
}

// Minimal satori element helper (avoids JSX in a .ts lib).
type El = {
  type: string;
  props: { style: Record<string, unknown>; children?: unknown };
};
const box = (style: Record<string, unknown>, children?: unknown): El => ({
  type: "div",
  props: { style: { display: "flex", ...style }, children },
});
const text = (style: Record<string, unknown>, value: string): El => ({
  type: "div",
  props: { style, children: value },
});

function posterElement(input: PosterInput): El {
  const tiles = input.tiles.map((t) =>
    box(
      {
        flexDirection: "column",
        gap: 4,
        padding: "16px 22px",
        background: TILE_BG,
        border: `1px solid ${HAIRLINE}`,
        borderRadius: 16,
      },
      [
        text(
          { fontSize: 40, fontWeight: 700, color: CREAM, lineHeight: 1 },
          t.num,
        ),
        text(
          {
            fontFamily: "JetBrains Mono",
            fontSize: 17,
            fontWeight: 500,
            letterSpacing: 1,
            textTransform: "uppercase",
            color: CREAM_MUTED,
          },
          t.label,
        ),
      ],
    ),
  );

  return box(
    {
      width: WIDTH,
      height: HEIGHT,
      flexDirection: "column",
      position: "relative",
      background: NAVY,
      fontFamily: "DM Sans",
    },
    [
      // Ambient glow behind the medallion.
      box({
        position: "absolute",
        top: -160,
        left: -120,
        width: 620,
        height: 620,
        borderRadius: 620,
        backgroundImage: `radial-gradient(circle, rgba(232,182,74,0.22), rgba(13,24,54,0))`,
      }),
      // Main content row.
      box(
        {
          flex: 1,
          alignItems: "center",
          gap: 56,
          padding: "64px 72px 40px",
        },
        [
          {
            type: "img",
            props: {
              src: badgeDataUri(input.image),
              width: 360,
              height: 360,
              style: { width: 360, height: 360, objectFit: "contain" },
            },
          } as unknown as El,
          box({ flexDirection: "column", flex: 1 }, [
            text(
              {
                fontFamily: "JetBrains Mono",
                fontSize: 24,
                fontWeight: 500,
                letterSpacing: 3,
                textTransform: "uppercase",
                color: GOLD,
              },
              `Issued to @${input.login}`,
            ),
            text(
              {
                fontSize: 68,
                fontWeight: 700,
                color: CREAM,
                lineHeight: 1.05,
                marginTop: 10,
              },
              input.title,
            ),
            text(
              {
                fontSize: 30,
                fontWeight: 400,
                color: CREAM_MUTED,
                lineHeight: 1.35,
                marginTop: 18,
                maxWidth: 640,
              },
              `\u201C${input.caption}\u201D`,
            ),
            box({ gap: 16, marginTop: 30 }, tiles),
          ]),
        ],
      ),
      // Footer bar: brand wordmark left, gallery URL right.
      box(
        {
          alignItems: "center",
          justifyContent: "space-between",
          padding: "22px 72px",
          borderTop: `1px solid ${HAIRLINE}`,
          background: NAVY_DEEP,
        },
        [
          box({ alignItems: "baseline", gap: 10 }, [
            text(
              { fontSize: 26, fontWeight: 700, color: GOLD, letterSpacing: 1 },
              "CAT",
            ),
            text(
              { fontSize: 26, fontWeight: 700, color: CREAM },
              "Agent Skills",
            ),
          ]),
          text(
            {
              fontFamily: "JetBrains Mono",
              fontSize: 22,
              fontWeight: 500,
              color: CREAM_MUTED,
            },
            input.siteLabel,
          ),
        ],
      ),
    ],
  );
}

/** Render a contributor's badge poster as a 1200×630 PNG buffer (build-time only). */
export async function renderBadgePng(input: PosterInput): Promise<Buffer> {
  const svg = await satori(posterElement(input) as never, {
    width: WIDTH,
    height: HEIGHT,
    fonts: fonts(),
  });
  const png = new Resvg(svg, {
    fitTo: { mode: "width", value: WIDTH },
    font: { loadSystemFonts: false },
  })
    .render()
    .asPng();
  return Buffer.from(png);
}
