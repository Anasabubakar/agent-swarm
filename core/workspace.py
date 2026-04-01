#!/usr/bin/env python3
"""
Agent Swarm — Workspace Manager
Creates isolated project workspaces for each goal.
The agent-swarm folder stays untouched.

Each goal gets its own directory:
  projects/
  ├── todo-app-20260401_143022/
  │   ├── src/
  │   ├── tests/
  │   ├── package.json
  │   └── .swarm-meta.json  ← swarm metadata (agents used, status, etc.)
  ├── landing-page-20260401_150000/
  │   └── ...
  └── ...
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

SWARM_ROOT = Path(__file__).parent.parent
PROJECTS_DIR = SWARM_ROOT / "projects"


class Workspace:
    """
    An isolated workspace for a single goal/project.
    All agent work happens here — never in the agent-swarm folder.
    """
    
    def __init__(self, goal: str, base_dir: Optional[str] = None):
        self.goal = goal
        self.created_at = datetime.now()
        self.timestamp = self.created_at.strftime("%Y%m%d_%H%M%S")
        
        # Create project directory name from goal
        slug = goal.lower()
        for char in [" ", "/", "\\", ":", "*", "?", "\"", "<", ">", "|", "."]:
            slug = slug.replace(char, "-")
        slug = slug[:30].strip("-")
        # Remove multiple dashes
        while "--" in slug:
            slug = slug.replace("--", "-")
        
        self.name = f"{slug}-{self.timestamp}"
        
        # Create in current directory (or specified base)
        if base_dir and base_dir != ".":
            self.path = Path(base_dir) / self.name
        else:
            self.path = Path.cwd() / self.name
        
        self.meta_file = self.path / ".swarm-meta.json"
        self.agents_run = []
    
    def create(self) -> Path:
        """Create the workspace directory structure"""
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Write metadata
        self._save_meta()
        
        print(f"📁 Workspace created: {self.path}")
        return self.path
    
    def register_agent(self, agent_name: str, engine: str, status: str):
        """Register an agent that ran in this workspace"""
        self.agents_run.append({
            "agent": agent_name,
            "engine": engine,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        })
        self._save_meta()
    
    def get_path(self) -> Path:
        """Get the workspace path"""
        return self.path
    
    def get_meta(self) -> dict:
        """Get workspace metadata"""
        if self.meta_file.exists():
            return json.loads(self.meta_file.read_text())
        return {}
    
    def _save_meta(self):
        """Save workspace metadata"""
        meta = {
            "goal": self.goal,
            "created_at": self.created_at.isoformat(),
            "workspace": str(self.path),
            "agents_run": self.agents_run,
            "status": "active",
        }
        self.meta_file.write_text(json.dumps(meta, indent=2))
    
    def complete(self, status: str = "completed"):
        """Mark workspace as complete"""
        meta = self.get_meta()
        meta["status"] = status
        meta["completed_at"] = datetime.now().isoformat()
        self.meta_file.write_text(json.dumps(meta, indent=2))
    
    def list_files(self) -> list:
        """List all files in the workspace (excluding .swarm-meta)"""
        files = []
        for f in self.path.rglob("*"):
            if f.is_file() and f.name != ".swarm-meta.json":
                files.append(str(f.relative_to(self.path)))
        return sorted(files)


class WorkspaceManager:
    """Manages all workspaces"""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir) if base_dir else PROJECTS_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def create_workspace(self, goal: str) -> Workspace:
        """Create a new isolated workspace for a goal"""
        workspace = Workspace(goal, str(self.base_dir))
        workspace.create()
        return workspace
    
    def list_workspaces(self) -> list:
        """List all workspaces"""
        workspaces = []
        for d in sorted(self.base_dir.iterdir()):
            if d.is_dir() and (d / ".swarm-meta.json").exists():
                meta = json.loads((d / ".swarm-meta.json").read_text())
                meta["path"] = str(d)
                workspaces.append(meta)
        return workspaces
    
    def get_workspace(self, name: str) -> Optional[Workspace]:
        """Get a workspace by name"""
        path = self.base_dir / name
        if path.exists() and (path / ".swarm-meta.json").exists():
            meta = json.loads((path / ".swarm-meta.json").read_text())
            ws = Workspace(meta["goal"], str(self.base_dir))
            ws.path = path
            ws.name = name
            return ws
        return None
