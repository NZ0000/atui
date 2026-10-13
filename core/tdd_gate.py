"""
TDD Gate and Verification Controller.
Enforces:
1. Test-Driven Development (TDD): Tests must be run and passed before code can be accepted.
2. Syntax and compilation checks before test execution.
3. Post-merge verification gate: If tests pass, commit to git; if fail, rollback via git!
"""

import os
from typing import Dict, Any, Optional, List
import tools
from tools.base import make_result
from core.event_bus import default_bus, EventType

class TddGate:
    def __init__(self, target_dir: str = "tests", repo_root: Optional[str] = None):
        self.target_dir = target_dir
        self.repo_root = repo_root or os.getcwd()

    def run_verification(self, target: Optional[str] = None) -> Dict[str, Any]:
        """Runs syntax check and test runner on target tests."""
        test_target = target or self.target_dir
        default_bus.publish(EventType.TDD_CYCLE, {"phase": "verification_start", "target": test_target})

        result = tools.execute_tool("test_runner", {
            "target": test_target,
            "mode": "all",
            "cwd": self.repo_root
        })

        passed = result.get("success", False) and result.get("data", {}).get("passed", False)
        default_bus.publish(EventType.TDD_CYCLE, {
            "phase": "verification_result",
            "passed": passed,
            "data": result.get("data")
        })

        return {
            "passed": passed,
            "result": result,
            "summary": "All tests and syntax checks passed." if passed else "Verification failed.",
            "error_details": result.get("error") or result.get("data", {}).get("raw_output", "")
        }

    def verify_and_git_gate(self, commit_message: str, target: Optional[str] = None, rollback_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Post-merge Git gate:
        1. Runs test verification.
        2. If passed: commits changes to git repository.
        3. If failed: automatically triggers git rollback and returns error.
        """
        verif = self.run_verification(target)
        if verif["passed"]:
            default_bus.publish(EventType.GIT_ACTION, {"action": "commit_attempt", "message": commit_message})
            commit_res = tools.execute_tool("git_tool", {
                "action": "commit",
                "message": commit_message,
                "cwd": self.repo_root
            })
            default_bus.publish(EventType.GIT_ACTION, {"action": "committed", "result": commit_res})
            return {
                "success": True,
                "action": "committed",
                "commit_info": commit_res.get("data", {}),
                "verification": verif
            }
        else:
            default_bus.publish(EventType.GIT_ACTION, {"action": "rollback_trigger", "reason": verif["error_details"]})
            rollback_params = {"action": "rollback", "cwd": self.repo_root}
            if rollback_path:
                rollback_params["path"] = rollback_path
            rollback_res = tools.execute_tool("git_tool", rollback_params)
            default_bus.publish(EventType.GIT_ACTION, {"action": "rolled_back", "result": rollback_res})
            return {
                "success": False,
                "action": "rolled_back",
                "rollback_info": rollback_res.get("data", {}),
                "verification": verif,
                "error": f"Verification failed. Changes rolled back. Details: {verif['error_details']}"
            }
