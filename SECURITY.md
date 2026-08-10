# Security policy

## Reporting a vulnerability

Please use GitHub's **Security** tab and the repository's private vulnerability
reporting form. Do not open a public issue for an unpatched vulnerability, and
do not include real credentials, private prompts, or production data.

Include the affected revision, operating system, endpoint shape, a minimal
reproduction, and the observed result. Synthetic payloads are preferred.

## Supported version

Security fixes target the latest revision on `main`. This research utility does
not maintain parallel supported release branches.

## Security boundary

The tool sends prompts to the operator-selected OpenAI-compatible endpoint and
parses its responses. It does not authenticate that endpoint, sandbox the model
server, establish answer truth, or make third-party services private. Treat
remote endpoints and their data practices as separate trust decisions.
