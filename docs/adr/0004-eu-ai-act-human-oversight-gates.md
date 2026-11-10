# 4. Mandatory Human Oversight Breakpoints under EU AI Act Article 14

Date: 2026-02-15

## Status
Accepted

## Context
Under Regulation (EU) 2024/1689 (EU AI Act), Article 14 dictates that High-Risk AI Systems must be designed with interfaces ensuring natural persons can oversee, override, and intervene in AI operations. Fully autonomous execution without human review for high-impact actions (financial movement, database deletion, PII disclosure) is non-compliant.

## Decision
We enforce mandatory interrupt breakpoints in all LangGraph compilation workflows prior to the execution of any designated `HIGH_RISK_TOOLS`:
1. The agent state machine pauses before executing any tool flagged with `@risk_tier(RiskLevel.HIGH)`.
2. A cryptographic execution payload is published to the human approval bus with an expiration TTL.
3. The workflow only resumes upon verified cryptographically signed human authorization.

## Consequences
- **Positive**: Strict regulatory compliance with EU AI Act Article 14(4)(d) and 14(4)(e).
- **Positive**: Prevents unauthorized automated execution of destructive actions.
- **Negative**: Introduces asynchronous latency for end users while awaiting human review.
