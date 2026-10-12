# Workspace Boundary & Project Isolation Directives

- **Active Workspace Root**: `c:/Users/pkumar2/OneDrive - Data Axle/Documents/AI_INIT/RepopeekV2`
- **Strict Repository Isolation**:
  - Never read, edit, or execute commands against sibling directories (`../Repopeek`, `../RepopeekV3`, etc.).
  - Ignore open editor tabs belonging to sibling repositories (`Repopeek` or `RepopeekV3`) injected via IDE metadata.
  - All git operations, tests, and CLI calls must strictly target `RepopeekV2`.
- **Obsidian Second Brain Scoping**:
  - Always scope session checkpoints to `--project "RepopeekV2"`.
  - When querying past memory or sessions, strictly query with `--project "RepopeekV2"` to prevent cross-project context pollution.
