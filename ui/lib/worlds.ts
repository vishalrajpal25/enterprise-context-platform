import type { Industry, World } from "./types";

/**
 * Five worlds, each with its own personas and scenarios. Keep these
 * tight and opinionated — this is the curated tour, not an encyclopedia.
 *
 * Order matters: Metro Capital is the default because the "APAC revenue,
 * finance vs sales" story is the cleanest 15-second aha moment.
 */
export const WORLDS: World[] = [
  {
    id: "metro",
    industry_id: "finance",
    name: "Metro Capital",
    kind: "Sell-side investment bank",
    tagline:
      "Revenue means four different things to four different desks. And they're all correct.",
    personas: [
      {
        id: "priya",
        name: "Priya Raman",
        role: "Finance Analyst",
        department: "finance",
        avatar_initials: "PR",
      },
      {
        id: "marco",
        name: "Marco Silva",
        role: "Sales Analyst",
        department: "sales",
        avatar_initials: "MS",
      },
      {
        id: "dana",
        name: "Dana Okafor",
        role: "Auditor",
        department: "compliance",
        avatar_initials: "DO",
      },
      {
        id: "sam",
        name: "Sam Whitford",
        role: "Executive",
        department: "executive",
        avatar_initials: "SW",
      },
    ],
    scenarios: [
      {
        id: "apac-revenue",
        world_id: "metro",
        title: "APAC revenue last quarter",
        question: "Show me APAC revenue for last quarter",
        watch_for:
          "Switch from Priya (Finance) to Marco (Sales) and watch the answer change — finance includes ANZ, sales excludes it.",
      },
      {
        id: "credit-suisse-exposure",
        world_id: "metro",
        title: "Credit Suisse exposure",
        question: "What was our exposure to Credit Suisse on March 14, 2023?",
        watch_for:
          "CS merged into UBS in June 2023. Your query spans the cutover — ECP warns and asks which view you want.",
      },
      {
        id: "top-clients-aum",
        world_id: "metro",
        title: "Top 10 clients by AUM",
        question: "Who are our top 10 clients by AUM?",
        watch_for:
          "'Client' means three different things (legal entity / billing / coverage) — three different top-10 lists.",
      },
    ],
  },
  {
    id: "pine-ridge",
    industry_id: "finance",
    name: "Pine Ridge Capital",
    kind: "Buy-side equity fund",
    tagline:
      "Five vendors, five definitions of free cash flow, and one PM who has strong opinions.",
    personas: [
      {
        id: "elena",
        name: "Elena Voss",
        role: "Portfolio Manager",
        department: "pm",
        avatar_initials: "EV",
      },
      {
        id: "jin",
        name: "Jin Park",
        role: "Junior Analyst",
        department: "research",
        avatar_initials: "JP",
      },
      {
        id: "rachel",
        name: "Rachel Kim",
        role: "Compliance",
        department: "compliance",
        avatar_initials: "RK",
      },
    ],
    scenarios: [
      {
        id: "fcf-yield",
        world_id: "pine-ridge",
        title: "FCF yield, tech book, 8 quarters",
        question:
          "Show me free cash flow yield for my tech book over the last 8 quarters, peer-adjusted",
        watch_for:
          "Five FCF definitions across FactSet, S&P, GAAP, management-adjusted, and the house model. ECP picks the fund's canonical and flags the rest.",
      },
      {
        id: "tech-book-membership",
        world_id: "pine-ridge",
        title: "What's in 'my tech book'",
        question: "What positions are in my tech book right now?",
        watch_for:
          "GICS reclassified Comms Services out of Tech in 2018. House rule says Amazon counts as tech anyway. Tribal knowledge lives in a spreadsheet.",
      },
    ],
  },
  {
    id: "meridian",
    industry_id: "healthcare",
    name: "Meridian Health",
    kind: "Provider integrated delivery network",
    tagline:
      "Three definitions of readmission, all legally correct, all producing different quality scores.",
    personas: [
      {
        id: "aisha",
        name: "Dr. Aisha Nair",
        role: "Quality Lead",
        department: "quality",
        avatar_initials: "AN",
      },
      {
        id: "tom",
        name: "Tom Byrne",
        role: "Value-Based Contracts",
        department: "finance",
        avatar_initials: "TB",
      },
      {
        id: "lee",
        name: "Lee Park",
        role: "Data Analyst",
        department: "analytics",
        avatar_initials: "LP",
      },
    ],
    scenarios: [
      {
        id: "readmission-rate",
        world_id: "meridian",
        title: "30-day readmission, heart failure",
        question:
          "What's our 30-day readmission rate for heart failure patients?",
        watch_for:
          "CMS says 14.2%, internal says 11.8%, BCBS contract says 9.4%. Same patients, three rulebooks. ECP shows which one you actually need.",
      },
      {
        id: "diabetic-patients",
        world_id: "meridian",
        title: "How many diabetic patients",
        question: "How many diabetic patients do we currently have?",
        watch_for:
          "ICD-9→ICD-10 transition, Epic problem list vs claims disagree by 12%, pre-diabetes counts or not. Tribal landmine.",
      },
    ],
  },
  {
    id: "atlas",
    industry_id: "healthcare",
    name: "Atlas Health Plan",
    kind: "Commercial + Medicare Advantage payer",
    tagline:
      "MLR is a regulatory metric. Also a board metric. Also an actuarial metric. They disagree.",
    personas: [
      {
        id: "ravi",
        name: "Ravi Menon",
        role: "Medical Economics",
        department: "med-econ",
        avatar_initials: "RM",
      },
      {
        id: "nina",
        name: "Nina Orlov",
        role: "Actuary",
        department: "actuarial",
        avatar_initials: "NO",
      },
      {
        id: "carlos",
        name: "Carlos Mendez",
        role: "Compliance Officer",
        department: "compliance",
        avatar_initials: "CM",
      },
    ],
    scenarios: [
      {
        id: "mlr-florida-ma",
        world_id: "atlas",
        title: "MLR, Florida MA, Q1",
        question:
          "What's our medical loss ratio for the Medicare Advantage book in Florida for Q1, ACA-compliant?",
        watch_for:
          "Q1 claims are 73% complete — your MLR will drift up by ~2 points over the next 90 days. Actuaries know this. Dashboards don't.",
      },
    ],
  },
  {
    id: "nimbus",
    industry_id: "technology",
    name: "Nimbus Cloud",
    kind: "SaaS infrastructure",
    tagline: "MRR has six definitions and the board deck uses a seventh.",
    personas: [
      {
        id: "jordan",
        name: "Jordan Liu",
        role: "CFO",
        department: "finance",
        avatar_initials: "JL",
      },
      {
        id: "maya",
        name: "Maya Chen",
        role: "Head of Product",
        department: "product",
        avatar_initials: "MC",
      },
      {
        id: "ben",
        name: "Ben Fischer",
        role: "RevOps",
        department: "revops",
        avatar_initials: "BF",
      },
    ],
    scenarios: [
      {
        id: "mrr",
        world_id: "nimbus",
        title: "What's our MRR?",
        question: "What's our MRR this month?",
        watch_for:
          "Six legitimate answers: contracted, billed, collected, GAAP÷12, ARR÷12, committed. Finance uses one, the board sees another. A $400K annual prepay hits all six differently.",
      },
      {
        id: "dau",
        world_id: "nimbus",
        title: "Active users last week",
        question: "How many active users did we have last week?",
        watch_for:
          "Product says DAU is authenticated session, Growth says it's a qualifying event in Amplitude, Finance says it's paid seats. Plus: iOS 17 dropped reported sessions ~8% in Sept 2023.",
      },
    ],
  },
];

export const DEFAULT_WORLD_ID = "metro";
export const DEFAULT_SCENARIO_ID = "apac-revenue";
export const DEFAULT_INDUSTRY_ID = "finance";

/**
 * Top-level grouping. Users pick an industry first, then a specific
 * company inside it. Order matters: Finance first because that's where
 * the cleanest aha moment lives.
 */
export const INDUSTRIES: Industry[] = [
  {
    id: "finance",
    name: "Finance",
    tagline: "Where the same number means five different things.",
    worlds: WORLDS.filter((w) => w.industry_id === "finance"),
  },
  {
    id: "healthcare",
    name: "Healthcare",
    tagline: "Where regulatory, clinical, and contractual truth disagree.",
    worlds: WORLDS.filter((w) => w.industry_id === "healthcare"),
  },
  {
    id: "technology",
    name: "Technology",
    tagline: "Where product, finance, and growth measure different worlds.",
    worlds: WORLDS.filter((w) => w.industry_id === "technology"),
  },
];

export function findIndustryForWorld(worldId: string): Industry {
  const world = WORLDS.find((w) => w.id === worldId);
  const industry = INDUSTRIES.find((i) => i.id === world?.industry_id);
  return industry ?? INDUSTRIES[0];
}
