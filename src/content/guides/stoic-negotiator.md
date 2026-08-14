# Stoic Negotiator

## Overview

Stoic Negotiator is a principled negotiation-intelligence skill designed for Microsoft Copilot Studio, Microsoft 365 Cowork that helps users prepare, analyze, communicate, and make disciplined decisions across legitimate negotiation and dealing activities.

It combines practical negotiation concepts with Stoic disciplines such as composure, control of the controllable, separation of facts from interpretation, and deliberate decision-making.

> Note: This skill can be powered by the Deep Research capability to surface evidence-backed reasoning, citations, and authoritative sourcing. It is particularly impactful when used by Microsoft 365 Researcher and Analyst agents, which leverage extended research and analysis workflows. The skill is also applicable to other advanced AI platforms such as Anthropic Claude and OpenAI ChatGPT; on those platforms it benefits from their research and citation capabilities. For evidence-backed outputs, enable Deep Research or an equivalent source‑grounding mode when available.

## What it supports

- Salary and compensation
- Job offers
- Procurement and supplier negotiations
- Bids and tenders
- Sales and pricing
- Contracts and renewals
- Partnerships
- Commerce and purchasing
- Licensing and subscriptions
- Scope and services
- Dispute and settlement discussions
- General legitimate negotiations

## Core capabilities

- Negotiation brief
- Best Alternative To a Negotiated Agreement (BATNA) and reservation-point analysis
- Zone of Possible Agreement (ZOPA) hypothesis
- Stakeholder and counterpart analysis
- Issue prioritization
- Offer strategy
- Anchoring and counter-anchoring analysis
- Concession strategy
- Conditional trades
- Package offers
- Objection handling
- Negotiation scripts and messages
- Decision analysis
- Post-negotiation review

## Deep Research and Agent impact

- Deep Research augments the skill with documented evidence, source citations, and cross-document synthesis to support stronger, defensible recommendations.
- Microsoft 365 Researcher and Analyst agents benefit most: they can run extended explorations, validate sources, produce prioritized insights, and flag regulatory or organizational constraints.
- When Deep Research is enabled, the skill can propose data-driven BATNAs, identify precedents, and produce annotated negotiation briefs.

## Design principles

- Composure before reaction
- Preparation before persuasion
- Facts before assumptions
- Interests before positions
- Value creation before value claiming
- Conditional concessions over unilateral concessions
- Ethics over manipulation
- Decision quality over “winning”
- Human approval for consequential commitments

## Sample prompts

#1
```
Job offer — Role: CTO, BlackRock France.
I received an offer (base €420,000, signing bonus €50,000, long-term equity 0.25%, market-competitive benefits).
Produce a negotiation plan: 
    1) identify BATNA and reservation point with brief calculations, 
    2) propose a prioritized counteroffer package (numbers + rationale, include a target ask and fallback range), 
    3) draft a concise opening message.
```

#2
```
Supplier renewal: 
Vendor proposes a 12% price increase. Analyze past terms and KPIs, estimate ZOPA, and recommend three conditional trade packages to limit cost while preserving service. 
Flag risks, approval thresholds, and a short escalation script.
```

#3
```
Partnership brief:
Create a one-page annotated negotiation brief: objectives, likely counterpart interests, top 3 concessions, recommended anchor and opening offer, and a 4-line negotiation script.
If Deep Research is enabled, add source citations and precedents to support recommendations.
```

## Architecture

The skill is designed to separate interaction, negotiation reasoning, grounded organizational knowledge, structured state, external actions, approvals, and evaluation.

For enterprise implementations, deterministic rules should govern thresholds, approvals, escalation, and required disclosures. Organizational policies and contractual information should be grounded in authoritative sources.

## Safety and responsible use

This skill is not a tool for coercion, fraud, bribery, harassment, discrimination, or deceptive conduct. It does not guarantee outcomes and should not replace qualified legal, tax, financial, employment, or other regulated professional advice where such advice is required.
