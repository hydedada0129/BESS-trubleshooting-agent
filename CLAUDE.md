# BESS PCS Troubleshooting Agent

## Project
- Goal: BESS PCS troubleshooting agent, portfolio project. All docs in English.

## Working agreement
- I write agent.py myself. You review it, never write it.
- retrieval.py was written by Claude at my request (D-38); I review and own it.
- You may write boilerplate: ingest, API, Docker, tests, MCP wrapper.
- Before any new module: ask me design questions first, then plan, then code.

## Architecture rules
- LLM access only via the LLMClient interface (llm/base.py); cloud and local models are interchangeable.
- Raw logs never leave the machine; only anonymized summaries go to cloud models.

## Data and confidentiality
- No proprietary manuals, fault code tables, site names, or serial numbers anywhere.

## Dev workflow
- Run pytest before every commit. Commit messages in English.
- Project skills live in .claude/skills/. Skill rules encode my domain judgement; draft with me, don't invent safety or diagnostic rules.
