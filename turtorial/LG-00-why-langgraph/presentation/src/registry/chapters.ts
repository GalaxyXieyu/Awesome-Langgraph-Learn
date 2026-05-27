import type { ChapterDef } from "./types";
import ColdopenChapter from "../chapters/01-coldopen/Coldopen";
import { narrations as coldopenNarrations } from "../chapters/01-coldopen/narrations";
import CompareChapter from "../chapters/02-compare/Compare";
import { narrations as compareNarrations } from "../chapters/02-compare/narrations";
import PainpointsChapter from "../chapters/03-painpoints/Painpoints";
import { narrations as painpointsNarrations } from "../chapters/03-painpoints/narrations";
import BoundaryChapter from "../chapters/04-boundary/Boundary";
import { narrations as boundaryNarrations } from "../chapters/04-boundary/narrations";
import ClosingChapter from "../chapters/05-closing/Closing";
import { narrations as closingNarrations } from "../chapters/05-closing/narrations";

export const CHAPTERS: ChapterDef[] = [
  {
    id: "coldopen",
    title: "开场钩子",
    narrations: coldopenNarrations,
    Component: ColdopenChapter,
  },
  {
    id: "compare",
    title: "框架全景对比",
    narrations: compareNarrations,
    Component: CompareChapter,
  },
  {
    id: "painpoints",
    title: "三大痛点解析",
    narrations: painpointsNarrations,
    Component: PainpointsChapter,
  },
  {
    id: "boundary",
    title: "诚实边界",
    narrations: boundaryNarrations,
    Component: BoundaryChapter,
  },
  {
    id: "closing",
    title: "收尾",
    narrations: closingNarrations,
    Component: ClosingChapter,
  },
];
