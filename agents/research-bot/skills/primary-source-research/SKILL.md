---
name: primary-source-research
description: Research a question from primary docs first — Context7, official llms.txt, then papers. Use when the user asks what a system actually does, which knobs exist, or whether a claim is documented.
version: 1.0.0
metadata:
  hermes:
    tags: [research, docs, context7]
    category: research
    requires_toolsets: [web]
---

# Primary-source research

## When to Use

The user wants a documented answer: configuration keys, CLI behavior, API contracts, paper claims, or "does this exist?"

## Procedure

1. Name the library or product. If it is Hermes or Honcho, query Context7 first:
   - `/nousresearch/hermes-agent`
   - `/plastic-labs/honcho`
   - Also useful: `/llmstxt/hermes-agent_nousresearch_llms_txt`, `/websites/honcho_dev_v3`
2. Then open official LLM entry points when they exist (Hermes: `https://hermes-agent.nousresearch.com/llms.txt` and the pages it indexes).
3. Prefer first-party pages, specs, and papers over blogs and secondary summaries.
4. Record every source you actually retrieved: title, URL, and the sentence that supports the claim.
5. If Context7 and the official page disagree, cite both and treat the official page as primary.

## Pitfalls

- Do not invent knobs, flags, or endpoints from training data.
- A 404 or empty Context7 hit is a finding. Say so. Do not fill the gap from memory.
- Do not clone third-party repos to "explore" unless the user explicitly asked for a local checkout.

## Verification

Every factual sentence in the answer maps to a retrieved source, or is labeled inference.
