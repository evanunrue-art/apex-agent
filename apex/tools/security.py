import os
from pathlib import Path

def resolve_and_verify_workspace_path(requested_path: str, workspace: Path) -> Path:
    """Resolves requested_path and verifies it is inside workspace boundary.
    Rejects absolute paths outside workspace, .. traversals, and symlink escapes.
    """
    workspace_resolved = workspace.resolve()
    target_path = Path(requested_path)
    
    if target_path.is_absolute():
        resolved_target = target_path.resolve()
    else:
        resolved_target = (workspace / target_path).resolve()
        
    try:
        resolved_target.relative_to(workspace_resolved)
    except ValueError:
        raise PermissionError(f"Access denied: Requested path '{requested_path}' resolves outside workspace root '{workspace_resolved}'.")
        
    return resolved_target
