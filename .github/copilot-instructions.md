# AgentOps Repository Instructions

## Project

AgentOps is a small service desk agent application.

## Architecture

Keep these responsibilities separate:

- analysis
- planning
- review
- execution
- state
- evaluation

Never bypass human approval for consequential actions.

## Python

Use:

- Python 3.11+
- type hints
- unittest
- small functions

Avoid unnecessary dependencies.

## Safety

Never:

- expose credentials
- bypass approval
- execute an unapproved action
- invent missing information

## Git

Before changing code:

1. Understand the requirement.
2. Inspect existing implementation.
3. Make the smallest safe change.
4. Add tests.
5. Run tests.
6. Report failures honestly.