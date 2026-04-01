"""VCS platform integrations for specsmith."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specsmith.vcs.base import VCSPlatform

PLATFORM_REGISTRY: dict[str, type[VCSPlatform]] = {}


def _load_platforms() -> None:
    """Populate the platform registry."""
    from specsmith.vcs.bitbucket import BitbucketPlatform
    from specsmith.vcs.github import GitHubPlatform
    from specsmith.vcs.gitlab import GitLabPlatform

    for cls in (GitHubPlatform, GitLabPlatform, BitbucketPlatform):
        PLATFORM_REGISTRY[cls().name] = cls


def get_platform(name: str) -> VCSPlatform:
    """Get a platform instance by name."""
    if not PLATFORM_REGISTRY:
        _load_platforms()
    cls = PLATFORM_REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(PLATFORM_REGISTRY.keys()))
        msg = f"Unknown VCS platform '{name}'. Available: {available}"
        raise ValueError(msg)
    return cls()


def list_platforms() -> list[str]:
    """List available platform names."""
    if not PLATFORM_REGISTRY:
        _load_platforms()
    return sorted(PLATFORM_REGISTRY.keys())
