# AgentOps Architecture

## Goal

Analyze service desk requests and recommend safe next steps.

## Input

Natural-language service request.

## Output

- category
- priority
- plan
- LLM plan validation
- review decision
- action status

## Agent boundary

The agent can analyze and recommend.

The agent cannot independently perform high-impact actions.

Plans are validated with the OpenAI Responses API using `gpt-6-astra`
before they reach the deterministic reviewer. The LLM can reject a plan,
but it cannot approve or execute an action.

## Configuration

Set `OPENAI_API_KEY` and `OPENAI_MODEL` in the application environment or
the local, git-ignored `.env` file. Do not store a real key in source
control. If validation cannot produce a structured result, request creation
stops instead of bypassing validation.

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
4. Validate plans before review.
5. Preserve state.
6. Record actions.
7. Pass automated tests.