"""
Shared Blackboard Engine for Multi-Agent Collaboration.

Provides a thread-safe, centralized blackboard (共享黑板) where concurrent agents
(multiple Analysts, Coders, Reviewers, Orchestrator) can asynchronously post findings,
read architectural contracts, register discovered bugs, and coordinate without
inflating individual context windows with full file transcripts.
"""

import os
import json
import time
import threading
from typing import Dict, Any, List, Optional, Union

class SharedBlackboard:
    """Thread-safe multi-topic blackboard for multi-agent swarm collaboration."""

    def __init__(self, project_path: Optional[str] = None):
        self._lock = threading.Lock()
        self._topics: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.project_path = project_path or os.getcwd()

    def post(
        self,
        topic: str,
        key: str,
        value: Any,
        author: str = "agent",
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Post or update an entry under a topic in a thread-safe manner."""
        with self._lock:
            if topic not in self._topics:
                self._topics[topic] = {}
            
            entry = {
                "key": str(key),
                "value": value,
                "author": author,
                "tags": tags or [],
                "updated_at": time.time(),
                "created_at": self._topics[topic].get(str(key), {}).get("created_at", time.time())
            }
            self._topics[topic][str(key)] = entry
            return entry

    def get(self, topic: str, key: Optional[str] = None) -> Union[List[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Get all entries under a topic, or a specific entry by key."""
        with self._lock:
            topic_dict = self._topics.get(topic, {})
            if key is not None:
                return topic_dict.get(str(key))
            return list(topic_dict.values())

    def get_all(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Return a snapshot copy of the full blackboard."""
        with self._lock:
            import copy
            return copy.deepcopy(self._topics)

    def list_topics(self) -> List[str]:
        """List all active topics on the blackboard."""
        with self._lock:
            return sorted(list(self._topics.keys()))

    def clear(self, topic: Optional[str] = None):
        """Clear a specific topic or the entire blackboard."""
        with self._lock:
            if topic:
                self._topics.pop(topic, None)
            else:
                self._topics.clear()

    def export_markdown(self) -> str:
        """Format the blackboard contents into readable Markdown."""
        with self._lock:
            lines = ["# 智能体共享黑板协作快照 (Shared Blackboard Snapshot)\n"]
            if not self._topics:
                lines.append("*（黑板当前为空）*\n")
                return "\n".join(lines)

            for topic, entries in self._topics.items():
                lines.append(f"## 主题: {topic}")
                if not entries:
                    lines.append("*（暂无条目）*\n")
                    continue

                for key, data in entries.items():
                    author = data.get("author", "unknown")
                    val = data.get("value")
                    tags = ", ".join(data.get("tags", []))
                    tag_str = f" `[{tags}]`" if tags else ""
                    lines.append(f"### 📌 `{key}`{tag_str} (由 {author} 登记)")
                    if isinstance(val, (dict, list)):
                        lines.append("```json\n" + json.dumps(val, ensure_ascii=False, indent=2) + "\n```")
                    else:
                        lines.append(f"{val}\n")
                lines.append("")
            return "\n".join(lines)

    def save_to_file(self, file_path: str):
        """Persist blackboard to JSON and Markdown files."""
        with self._lock:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self._topics, f, ensure_ascii=False, indent=2)

        # Also write readable markdown counterpart
        base, _ = os.path.splitext(file_path)
        md_path = f"{base}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.export_markdown())

    def load_from_file(self, file_path: str):
        """Load blackboard state from a JSON file."""
        if not os.path.exists(file_path):
            return
        with self._lock:
            with open(file_path, "r", encoding="utf-8") as f:
                self._topics = json.load(f)


_GLOBAL_BLACKBOARD: Optional[SharedBlackboard] = None
_BB_LOCK = threading.Lock()

def get_blackboard(project_path: Optional[str] = None) -> SharedBlackboard:
    """Global singleton accessor for current project blackboard."""
    global _GLOBAL_BLACKBOARD
    with _BB_LOCK:
        if _GLOBAL_BLACKBOARD is None:
            _GLOBAL_BLACKBOARD = SharedBlackboard(project_path)
        return _GLOBAL_BLACKBOARD

def reset_blackboard():
    """Reset the global blackboard instance."""
    global _GLOBAL_BLACKBOARD
    with _BB_LOCK:
        _GLOBAL_BLACKBOARD = None
