# Project Collaboration Rules

## Approval Before Implementation and Execution

- Before implementing any change or running any command that changes the project, explain the proposed implementation and execution details to the user.
- The explanation must include the goal, files or components affected, intended technical changes, execution steps, validation plan, and relevant risks or trade-offs.
- Wait for explicit user approval before starting implementation or executing project-changing commands.
- Read-only inspection and analysis may be performed before approval when needed to prepare an accurate proposal.
- After implementation, report what changed, what was executed, and the validation results in sufficient detail.

## Git and GitHub Workflow

- Every completed phase or logical change must be committed and pushed before starting the next phase.
- Use GitHub CLI (`gh`) for every push to GitHub. Do not use `git push`.
- Keep each commit scoped to the phase or logical change being completed.
- Commit messages must follow the Conventional Commits specification, for example: `feat: add match prediction pipeline`, `fix: correct team ranking lookup`, or `docs: add project collaboration rules`.
- Do not include unrelated working-tree changes in a commit or push.
- Explain the planned commit and push, then wait for explicit user approval before performing them.

## Attribution and Project Identity

- Never add Codex, Claude, OpenAI, an AI assistant, a bot, or any assistant identity as a contributor, collaborator, author, co-author, maintainer, or project participant.
- Never add `Co-authored-by` or similar attribution for an AI assistant to commit messages.
- Never add AI attribution to source files, documentation, release notes, pull requests, repository metadata, or contributor lists.
- Use only the user's existing Git and GitHub identity for project operations. Do not alter identity settings unless the user explicitly requests it.

## Communication Style

- Do not use emoji in project communication, documentation, commit messages, or generated project content.
- Keep explanations clear, concrete, and focused on implementation, execution, and verification.
