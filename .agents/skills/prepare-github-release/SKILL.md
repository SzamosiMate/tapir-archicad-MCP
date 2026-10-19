---
name: prepare-github-release
description: Prepare a version bump, descriptive release notes and a reviewed GitHub draft using this repository's release helper.
---

# Prepare a GitHub release

Read [the release procedure](references/releasing.md) and
[the release-note style](references/release-notes.md). Run commands from the
repository root; `scripts/release.py` handles deterministic preparation.

- Determine the target version and previous release tag from the request or
  session. Ask when the target version is missing; do not choose one implicitly.
  Respect requests limited to notes or local review rather than creating a draft.
- Finish any requested generation and source reviews before release preparation,
  following the repository's existing workflows. Do not invoke an explicit-only
  generation skill unless it was requested.
- Run `python scripts/release.py bump VERSION` and inspect the version/lock diff.
  Include it in the reviewed source changes. Preserve unrelated work and follow
  the session's commit/push authorization. A draft requires committed, pushed HEAD.
  If a branch is needed, use `release/VERSION`.
- Inspect the actual previous-tag-to-release-commit diff, PRs and relevant reports;
  fetch origin's tags when needed. Write the descriptive notes to an OS temporary
  Markdown file. Omit attribution from this helper input: the helper appends
  GitHub's exact generated PR list, authors and contributor credits.
- Run `python scripts/release.py check`, then
  `python scripts/release.py draft --previous vPREVIOUS --notes-file TEMP_FILE`.
  Revise an existing draft in its editor rather than automatically recreating it.
  Do not move a conflicting existing tag.
- Return the draft link. The user edits, discards, or clicks **Publish release**;
  that click starts the publishing workflow. Do not publish the draft or upload
  to PyPI as part of preparing it.
- Report publishing failures against the same tag. Do not delete PyPI files or
  silently choose a different version.

Use the draft as the durable review surface. Do not create a release-state cache
or extra per-step reports; retain existing generation reports when applicable.
