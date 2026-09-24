# AgentOps Architecture

## Goal

Analyze service desk requests and recommend safe next steps.

## Input

Natural-language service request.

## Output

- category
- priority
- plan
- review decision
- action status

## Agent boundary

The agent can analyze and recommend.

The agent cannot independently perform high-impact actions.

## High-impact examples

- changing access
- changing billing information
- executing incident remediation

## Human boundary

High-impact actions require approval.

## Success criteria

1. Correctly classify requests.
2. Produce structured plans.
3. Identify risky actions.
4. Preserve state.
5. Record actions.
6. Pass automated tests.