# Setup Guide

## Which environment should I choose?
For reusable files and native agent/skill discovery, choose Claude Code. Claude web Projects are easier for instruction/knowledge uploads but are not the same as repository-local executable subagents.

## Setup
1. Install Claude Code by following the current official Anthropic documentation for your operating system.
2. Extract this package.
3. Open a terminal in the extracted `ai-software-team` directory.
4. Run `python scripts/validate_team.py`.
5. Start the team with `claude --agent agile-orchestrator` from this directory, and first ask it to inspect configuration only.
6. Review its observed agent/skill discovery and correct any version-specific issues.

## Do not assume
- Do not assume Claude Pro includes API billing/credits. Claude Code availability and usage limits are subject to the current plan terms.
- Do not assume GitHub is required. Local files and Git are enough to start; remote hosting is optional.
- Do not install MCP servers or grant broad permissions unless a concrete need is established.
- Do not paste secrets into prompts, files, or logs.

## Official docs
- Claude Code overview: https://docs.anthropic.com/en/docs/claude-code/overview
- Subagents: https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Agent Skills: https://docs.anthropic.com/en/docs/claude-code/skills
- Plans and usage: https://support.anthropic.com/
