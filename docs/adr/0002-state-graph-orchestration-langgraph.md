# 2. Adopt LangGraph for Stateful Cyclic Agent Orchestration

Date: 2026-01-20

## Status
Accepted

## Context
Standard linear DAG orchestrators and basic LLM chaining frameworks (e.g., standard LangChain Chains or vanilla ReAct loops) do not support durable cyclic graphs, persistence, state mutation, or explicit interrupt breakpoints required for complex multi-agent systems and regulatory compliance.

## Decision
We adopt **LangGraph** as our primary orchestration framework. LangGraph models agent workflows as stateful cyclic graphs with built-in checkpointing, time-travel debugging, and first-class interrupt semantics.

## Consequences
- **Positive**: Native support for cyclic reasoning loops (e.g. Plan -> Execute -> Critique -> Replan).
- **Positive**: Checkpointing enables state persistence across server restarts and human-in-the-loop pauses.
- **Positive**: Conforms directly to EU AI Act Article 14 requirement for operational breakpoints and state rollback.
- **Negative**: Requires engineers to adopt a graph-oriented mental model and explicit schema typing (`TypedDict`).
