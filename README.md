# ForgeOps

ForgeOps is a local-first, open-source DevOps automation CLI tool built in Python. It helps developers initialize projects, lint Dockerfiles, scan for secrets in environment files, and generate basic CI workflows—all without relying on external APIs or network connections.

## Installation

1. Ensure you have Python 3.10+ installed.
2. Clone or download the repository.
3. Install dependencies: `pip install -e .`

## Usage

- Initialize a new project: `forgeops init <project_name>`
- Lint a Dockerfile: `forgeops lint`
- Scan for secrets in .env files: `forgeops scan`
- Generate a GitHub Actions CI workflow: `forgeops generate-ci`

All commands operate locally and do not require internet access.

## Why This Matters for Open Source

ForgeOps empowers open-source developers by providing essential DevOps tools that work offline, ensuring privacy, security, and accessibility. It promotes self-reliance in development workflows, reducing dependencies on cloud services and fostering a more decentralized approach to software automation.
