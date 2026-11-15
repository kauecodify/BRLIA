"""Escopos por jurisdicao e por modo de deploy (OIDC e mTLS)."""

from __future__ import annotations

DEPLOY_MODES = ("sidecar", "daemonset", "standalone", "managed")


def scope_for(jurisdiction: str, deploy_mode: str) -> str:
    if deploy_mode not in DEPLOY_MODES:
        raise ValueError(f"modo de deploy invalido: {deploy_mode}")
    return f"brlia:{jurisdiction}:{deploy_mode}"


def authorize(subject_scopes: list[str], jurisdiction: str, deploy_mode: str) -> bool:
    return scope_for(jurisdiction, deploy_mode) in subject_scopes
