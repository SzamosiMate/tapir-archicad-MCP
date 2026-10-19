"""Prepare a reviewed draft; publishing is handled by GitHub Actions."""

import argparse
import json
import re
import shutil
import subprocess
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args, capture=False):
    result = subprocess.run(
        [shutil.which(args[0]) or args[0], *map(str, args[1:])],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        capture_output=capture,
    )
    return result.stdout.strip() if capture else None


def project():
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]


def check(tag=None):
    version = project()["version"]
    if tag and tag != f"v{version}":
        raise ValueError(f"Tag {tag} does not match package version v{version}.")
    manifest = ROOT / "manifest.json"
    if manifest.exists() and json.loads(manifest.read_text(encoding="utf-8"))["version"] != version:
        raise ValueError("Python package and MCPB manifest versions differ.")
    run("uv", "lock", "--check")


def bump(version):
    paths = [ROOT / "pyproject.toml", ROOT / "uv.lock"]
    manifest = ROOT / "manifest.json"
    if manifest.exists():
        paths.append(manifest)
    original = {p: p.read_bytes() for p in paths}
    try:
        run("uv", "version", version, "--frozen")
        if manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["version"] = project()["version"]
            manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        run("uv", "lock")
        check()
    except BaseException:
        for path, content in original.items():
            path.write_bytes(content)
        raise
    print("Review and commit the version files with the release changes before drafting.")


def draft(previous, notes_file):
    if run("git", "status", "--porcelain", "--untracked-files=no", capture=True):
        raise ValueError("Commit or stash tracked changes before creating the draft.")
    check()
    summary = Path(notes_file).read_text(encoding="utf-8").strip()
    if not summary or re.search(
        r"^## (What's Changed|New Contributors)|^\*\*Full Changelog\*\*:", summary, re.MULTILINE
    ):
        raise ValueError("Supply descriptive notes only; the helper appends GitHub's generated credits.")
    repo = project()["urls"]["Homepage"].removeprefix("https://github.com/").rstrip("/")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise ValueError("project.urls.Homepage must identify the GitHub repository.")
    tag = f"v{project()['version']}"
    commit = run("git", "rev-parse", "HEAD", capture=True)
    run("git", "merge-base", "--is-ancestor", previous, commit)
    remote = run("gh", "api", f"repos/{repo}/commits/{commit}", "--jq", ".sha", capture=True)
    if remote != commit:
        raise ValueError("Push the reviewed release commit before drafting.")
    refs = json.loads(run("gh", "api", f"repos/{repo}/git/matching-refs/tags/{tag}", capture=True))
    if any(ref["ref"] == f"refs/tags/{tag}" for ref in refs):
        tagged = run("gh", "api", f"repos/{repo}/commits/{tag}", "--jq", ".sha", capture=True)
        if tagged != commit:
            raise ValueError("The existing release tag points to a different commit; it will not be moved.")
    run(
        "gh",
        "release",
        "create",
        tag,
        "--repo",
        repo,
        "--target",
        commit,
        "--draft",
        "--title",
        f"{tag} Release",
        "--notes-file",
        Path(notes_file).resolve(),
        "--generate-notes",
        "--notes-start-tag",
        previous,
    )
    print("Review, edit or discard the draft in GitHub. Publish release starts the publishing workflow.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    bump_parser = commands.add_parser("bump", help="Bump package/MCPB versions and refresh the lock")
    bump_parser.add_argument("version")
    check_parser = commands.add_parser("check", help="Check versions and lock freshness")
    check_parser.add_argument("--tag")
    draft_parser = commands.add_parser("draft", help="Create a draft with generated PR/author credits")
    draft_parser.add_argument("--previous", required=True)
    draft_parser.add_argument("--notes-file", required=True, help="Descriptive Markdown without the generated footer")
    args = parser.parse_args()
    try:
        if args.command == "bump":
            bump(args.version)
        elif args.command == "check":
            check(args.tag)
        else:
            draft(args.previous, args.notes_file)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Release preparation stopped: {getattr(error, 'stderr', None) or error}\n")


if __name__ == "__main__":
    main()
