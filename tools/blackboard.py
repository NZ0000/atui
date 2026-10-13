#!/usr/bin/env python3
"""
Tool: blackboard
Centralized shared blackboard for multi-agent swarm collaboration.
Enables agents to post bug findings, read architectural contracts, and coordinate
without passing huge transcripts across agent contexts.
"""

import sys
import os
import json
from typing import Dict, Any, List, Optional

try:
    from tools.base import make_result, cli_runner
    from core.blackboard import get_blackboard
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from tools.base import make_result, cli_runner
    from core.blackboard import get_blackboard

TOOL_SPEC = {
    "name": "blackboard",
    "description": "智能体共享黑板协作工具。支持在多智能体之间跨角色读写、发布Bug发现、登记架构接口契约、检索其他Agent的分析成果，避免重复劳动与上下文膨胀。",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["post", "get", "list", "export", "clear", "save"],
                "description": "操作类型：post (登记发布), get (查询获取), list (列出所有主题), export (导出Markdown快照), clear (清空), save (持久化到文件)"
            },
            "topic": {
                "type": "string",
                "description": "黑板分类主题，例如 'bug_findings', 'architecture_contracts', 'sub_tasks', 'design_specs'"
            },
            "key": {
                "type": "string",
                "description": "条目唯一标识，例如 'MOD-buildings', 'threejs_msaa_bug', 'api_port'"
            },
            "value": {
                "type": "string",
                "description": "条目详细内容（字符串或JSON格式数据）"
            },
            "author": {
                "type": "string",
                "description": "发布者身份（例如 'analyst-1', 'orchestrator', 'coder-2'）"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "标签列表（如 ['critical', '3d', 'rendering']）"
            },
            "file_path": {
                "type": "string",
                "description": "save 操作时的目标文件路径（默认: deliverables/blackboard.json）"
            }
        },
        "required": ["action"]
    }
}

def execute(params: Dict[str, Any]) -> Dict[str, Any]:
    action = params.get("action", "").lower().strip()
    bb = get_blackboard()

    if not action:
        return make_result(False, error="Parameter 'action' is required.")

    if action == "post":
        topic = params.get("topic")
        key = params.get("key")
        value = params.get("value")
        author = params.get("author", "agent")
        tags = params.get("tags")
        if not topic or not key:
            return make_result(False, error="Posting requires both 'topic' and 'key'.")
        
        # If value is a JSON string, try parsing it to keep structured data
        if isinstance(value, str):
            try:
                parsed_val = json.loads(value)
                value = parsed_val
            except Exception:
                pass

        entry = bb.post(topic=topic, key=key, value=value, author=author, tags=tags)
        return make_result(True, data={"entry": entry, "message": f"Successfully posted '{key}' to topic '{topic}'"})

    elif action == "get":
        topic = params.get("topic")
        key = params.get("key")
        if not topic:
            return make_result(False, error="Getting entries requires 'topic'.")
        res = bb.get(topic=topic, key=key)
        return make_result(True, data=res)

    elif action == "list":
        topics = bb.list_topics()
        return make_result(True, data={"topics": topics})

    elif action == "export":
        md = bb.export_markdown()
        return make_result(True, data={"markdown": md})

    elif action == "save":
        fp = params.get("file_path", "deliverables/blackboard.json")
        bb.save_to_file(fp)
        return make_result(True, data={"saved_file": fp, "message": f"Blackboard persisted to {fp}"})

    elif action == "clear":
        topic = params.get("topic")
        bb.clear(topic=topic)
        return make_result(True, data={"message": f"Cleared topic '{topic}'" if topic else "Cleared entire blackboard"})

    else:
        return make_result(False, error=f"Unknown blackboard action '{action}'.")

if __name__ == "__main__":
    cli_runner("blackboard", TOOL_SPEC, execute)
