"use client";

/**
 * Global UI state held in React context + useReducer. No Zustand/Redux —
 * the state surface is small enough that context is the right tool.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
} from "react";
import { DEFAULT_SCENARIO_ID, DEFAULT_WORLD_ID, WORLDS } from "./worlds";
import type { Persona, ResolveResponse, Scenario, World } from "./types";
import { resolve as resolveApi } from "./api";

type Status = "idle" | "loading" | "ready" | "error";

type State = {
  world: World;
  persona: Persona;
  scenario: Scenario;
  question: string;
  status: Status;
  error: string | null;
  current: ResolveResponse | null;
  previous: ResolveResponse | null; // for persona-swap comparison
  previousPersonaId: string | null;
};

type Action =
  | { type: "SET_WORLD"; worldId: string }
  | { type: "SET_PERSONA"; personaId: string }
  | { type: "SET_SCENARIO"; scenarioId: string }
  | { type: "SET_QUESTION"; question: string }
  | { type: "RESOLVE_START" }
  | {
      type: "RESOLVE_SUCCESS";
      response: ResolveResponse;
      carryAsPrevious?: boolean;
      previousPersonaId?: string;
    }
  | { type: "RESOLVE_ERROR"; error: string }
  | { type: "CLEAR_COMPARISON" };

function initialState(): State {
  const world =
    WORLDS.find((w) => w.id === DEFAULT_WORLD_ID) ?? WORLDS[0];
  const scenario =
    world.scenarios.find((s) => s.id === DEFAULT_SCENARIO_ID) ??
    world.scenarios[0];
  return {
    world,
    persona: world.personas[0],
    scenario,
    question: scenario.question,
    status: "idle",
    error: null,
    current: null,
    previous: null,
    previousPersonaId: null,
  };
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "SET_WORLD": {
      const world = WORLDS.find((w) => w.id === action.worldId) ?? state.world;
      const scenario = world.scenarios[0];
      return {
        ...state,
        world,
        persona: world.personas[0],
        scenario,
        question: scenario.question,
        current: null,
        previous: null,
        previousPersonaId: null,
        status: "idle",
        error: null,
      };
    }
    case "SET_PERSONA": {
      const persona =
        state.world.personas.find((p) => p.id === action.personaId) ??
        state.persona;
      return { ...state, persona };
    }
    case "SET_SCENARIO": {
      const scenario =
        state.world.scenarios.find((s) => s.id === action.scenarioId) ??
        state.scenario;
      return {
        ...state,
        scenario,
        question: scenario.question,
        current: null,
        previous: null,
        previousPersonaId: null,
        status: "idle",
        error: null,
      };
    }
    case "SET_QUESTION":
      return { ...state, question: action.question };
    case "RESOLVE_START":
      return { ...state, status: "loading", error: null };
    case "RESOLVE_SUCCESS":
      return {
        ...state,
        status: "ready",
        current: action.response,
        previous: action.carryAsPrevious ? state.current : state.previous,
        previousPersonaId: action.carryAsPrevious
          ? action.previousPersonaId ?? state.previousPersonaId
          : state.previousPersonaId,
        error: null,
      };
    case "RESOLVE_ERROR":
      return { ...state, status: "error", error: action.error };
    case "CLEAR_COMPARISON":
      return { ...state, previous: null, previousPersonaId: null };
    default:
      return state;
  }
}

type Ctx = State & {
  setWorld: (id: string) => void;
  setPersona: (id: string) => void;
  setScenario: (id: string) => void;
  setQuestion: (q: string) => void;
  run: (opts?: { carryAsPrevious?: boolean }) => Promise<void>;
  clearComparison: () => void;
};

const StoreContext = createContext<Ctx | null>(null);

export function StoreProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, undefined, initialState);

  const run = useCallback(
    async (opts?: { carryAsPrevious?: boolean }) => {
      dispatch({ type: "RESOLVE_START" });
      try {
        const previousPersonaId = state.persona.id;
        const response = await resolveApi({
          worldId: state.world.id,
          scenarioId: state.scenario.id,
          persona: state.persona,
          question: state.question,
        });
        dispatch({
          type: "RESOLVE_SUCCESS",
          response,
          carryAsPrevious: opts?.carryAsPrevious,
          previousPersonaId,
        });
      } catch (e) {
        dispatch({ type: "RESOLVE_ERROR", error: (e as Error).message });
      }
    },
    [state.world.id, state.scenario.id, state.persona, state.question],
  );

  // Auto-run on first mount so the visitor sees the story immediately.
  useEffect(() => {
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo<Ctx>(
    () => ({
      ...state,
      setWorld: (id) => dispatch({ type: "SET_WORLD", worldId: id }),
      setPersona: (id) => dispatch({ type: "SET_PERSONA", personaId: id }),
      setScenario: (id) => dispatch({ type: "SET_SCENARIO", scenarioId: id }),
      setQuestion: (q) => dispatch({ type: "SET_QUESTION", question: q }),
      run,
      clearComparison: () => dispatch({ type: "CLEAR_COMPARISON" }),
    }),
    [state, run],
  );

  return (
    <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
  );
}

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore must be used within StoreProvider");
  return ctx;
}
