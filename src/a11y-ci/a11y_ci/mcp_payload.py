"""
MCP payload generation for accessibility evidence.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import uuid
from typing import Any, Dict, List, Optional

from . import __version__
from .gate import GateResult
from .help import get_help
from .scorecard import Scorecard, compute_fingerprint, finding_id


def sha256_file(path: str) -> str | None:
    """Compute SHA256 hash of a file, returning None if not found."""
    try:
        with open(path, "rb") as f:
            digest = hashlib.sha256()
            while chunk := f.read(8192):
                digest.update(chunk)
            return digest.hexdigest()
    except (FileNotFoundError, PermissionError):
        return None


def build_mcp_payload(
    result: GateResult,
    scorecard: Scorecard,
    fail_on: str,
    artifacts: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Build the structured MCP evidence payload."""
    
    # 1. Environment metadata
    env_repo = os.environ.get("GITHUB_REPOSITORY")
    env_sha = os.environ.get("GITHUB_SHA")
    env_workflow = os.environ.get("GITHUB_WORKFLOW")
    env_run_id = os.environ.get("GITHUB_RUN_ID")

    # 2. Gate details
    gate_info = {
        "decision": "pass" if result.ok else "fail",
        "exit_code": 0 if result.ok else 3,
        "fail_on": fail_on,
        "counts": result.current_counts,
        "deltas": {},  # Could populate if baseline comparison logic exposed logic for deltas
    }
    
    # Calculate deltas if baseline exists
    if result.baseline_counts:
        deltas = {}
        for severity, count in result.current_counts.items():
            base_count = result.baseline_counts.get(severity, 0)
            diff = count - base_count
            if diff != 0:
                deltas[severity] = diff
        gate_info["deltas"] = deltas

    # 3. Blocking findings details
    blocking_details = []
    
    # Create a lookup for blocking status to include help details
    # We only want to detail findings that are actually blocking, 
    # but the GateResult only gives us IDs. 
    # We need to find the full finding objects in the scorecard matching those IDs.
    
    blocking_ids_set = set(result.current_blocking_ids)
    
    # Optimization: Map IDs to help info once
    help_map = {}
    for fid in blocking_ids_set:
        help_map[fid] = get_help(fid)

    for f in scorecard.findings:
        fid = finding_id(f)
        if fid in blocking_ids_set:
            # Reconstruct details
            item = {
                "id": fid,
                "fingerprint": compute_fingerprint(f),
                "severity": f.get("severity"),
                "message": f.get("message"),
                "location": f.get("location"),
            }
            
            help_data = help_map.get(fid)
            if help_data:
                item["help_url"] = help_data.url
                item["help_hint"] = help_data.hint
                
            blocking_details.append(item)

    # 4. Artifacts
    artifact_list = []
    for art in artifacts:
        path = art.get("path")
        if path:
            h = sha256_file(path)
            if h:
                artifact_list.append({
                    "kind": art.get("kind"),
                    "path": path,
                    "sha256": h
                })

    # Assemble final payload
    return {
        "tool": "a11y-ci",
        "tool_version": __version__,
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo": env_repo,
        "commit_sha": env_sha,
        "workflow": env_workflow,
        "gate": gate_info,
        "blocking": blocking_details,
        "artifacts": artifact_list,
    }
