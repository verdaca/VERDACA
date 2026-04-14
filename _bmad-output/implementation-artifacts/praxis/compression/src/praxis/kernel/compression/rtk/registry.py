"""RTK known command registry — mirrors RTK's internal command registry."""
from __future__ import annotations

# Commands known to RTK (representative sample; full list is in the RTK binary)
KNOWN_COMMANDS: frozenset[str] = frozenset({
    "git", "npm", "cargo", "pytest", "docker", "docker-compose",
    "kubectl", "helm", "terraform", "aws", "gcloud", "az",
    "pip", "pip3", "python", "python3", "node", "yarn", "pnpm",
    "make", "cmake", "gradle", "mvn", "ant", "bazel",
    "ls", "find", "grep", "rg", "fd", "cat", "head", "tail",
    "ps", "top", "htop", "df", "du", "free", "lsof", "netstat",
    "curl", "wget", "http", "httpie",
    "ruff", "mypy", "black", "flake8", "eslint", "tsc",
    "rustc", "go", "java", "javac", "scala", "sbt",
    "gh", "hub", "jira", "linear",
})


def is_known_command(argv: list[str]) -> bool:
    """Return True if the first argument is a command known to RTK."""
    if not argv:
        return False
    return argv[0] in KNOWN_COMMANDS
