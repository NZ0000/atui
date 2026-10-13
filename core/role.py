"""
Role and Agent Specification parser.
Parses agent configuration and prompt from Markdown (.md) or JSON files.
Supports permissions, allowed tools list, gate rules, and system prompts.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional

class Role:
    def __init__(
        self,
        name: str,
        description: str = "",
        system_prompt: str = "",
        tools: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        model: Optional[str] = None,
        gate_rules: Optional[Dict[str, Any]] = None,
        source_file: Optional[str] = None
    ):
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools if tools is not None else ["*"]
        self.permissions = permissions if permissions is not None else ["read", "write", "run"]
        self.model = model
        self.gate_rules = gate_rules or {
            "require_output_file": True,
            "require_diff": False,
            "require_test_pass": False
        }
        self.source_file = source_file

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "permissions": self.permissions,
            "model": self.model,
            "gate_rules": self.gate_rules,
            "source_file": self.source_file
        }

    def has_permission(self, perm: str) -> bool:
        return "*" in self.permissions or perm in self.permissions

    def is_tool_allowed(self, tool_name: str) -> bool:
        return "*" in self.tools or tool_name in self.tools

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_file: Optional[str] = None) -> "Role":
        return cls(
            name=data.get("name", "assistant"),
            description=data.get("description", ""),
            system_prompt=data.get("system_prompt", ""),
            tools=data.get("tools", ["*"]),
            permissions=data.get("permissions", ["read", "write", "run"]),
            model=data.get("model"),
            gate_rules=data.get("gate_rules", {}),
            source_file=source_file
        )

    @classmethod
    def from_file(cls, file_path: str) -> "Role":
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Role file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read().strip()

        if file_path.endswith(".json"):
            data = json.loads(content)
            return cls.from_dict(data, source_file=file_path)

        return cls._parse_markdown(content, file_path)

    @classmethod
    def _parse_markdown(cls, content: str, file_path: str) -> "Role":
        name = os.path.splitext(os.path.basename(file_path))[0]
        description = ""
        system_prompt = ""
        tools = ["*"]
        permissions = ["read", "write", "run"]
        model = None
        gate_rules = {"require_output_file": True}

        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", content, re.DOTALL)
        body = content
        if fm_match:
            frontmatter_raw = fm_match.group(1)
            body = fm_match.group(2)
            fm_dict = cls._parse_simple_yaml(frontmatter_raw)
            if "name" in fm_dict:
                name = str(fm_dict["name"])
            if "description" in fm_dict:
                description = str(fm_dict["description"])
            if "model" in fm_dict:
                model = str(fm_dict["model"])
            if "tools" in fm_dict:
                t = fm_dict["tools"]
                tools = t if isinstance(t, list) else [x.strip() for x in str(t).split(",") if x.strip()]
            if "permissions" in fm_dict:
                p = fm_dict["permissions"]
                permissions = p if isinstance(p, list) else [x.strip() for x in str(p).split(",") if x.strip()]
            if "gate_rules" in fm_dict and isinstance(fm_dict["gate_rules"], dict):
                gate_rules.update(fm_dict["gate_rules"])

        sections = re.split(r"\n(?=##?\s+)", body)
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue
            lines = sec.split("\n")
            header = lines[0].strip().lstrip("#").strip().lower()
            sec_body = "\n".join(lines[1:]).strip()

            if header.startswith("role") or header == "name":
                parts = lines[0].split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    name = parts[1].strip()
            elif header == "description":
                if not description:
                    description = sec_body
            elif header in ("tools", "allowed tools"):
                extracted_tools = [line.strip().lstrip("-* ").strip() for line in lines[1:] if line.strip().startswith(("-", "*"))]
                if extracted_tools:
                    tools = extracted_tools
            elif header in ("permissions", "permission"):
                extracted_perms = [line.strip().lstrip("-* ").strip() for line in lines[1:] if line.strip().startswith(("-", "*"))]
                if extracted_perms:
                    permissions = extracted_perms
            elif header in ("gate rules", "gates"):
                for line in lines[1:]:
                    line = line.strip().lstrip("-* ").strip()
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip().lower()
                        gate_rules[k] = (v in ("true", "1", "yes"))
            elif header in ("system prompt", "prompt", "instructions", "instructions / system prompt"):
                system_prompt = sec_body

        if not system_prompt:
            system_prompt = body.strip()

        return cls(
            name=name,
            description=description,
            system_prompt=system_prompt,
            tools=tools,
            permissions=permissions,
            model=model,
            gate_rules=gate_rules,
            source_file=file_path
        )

    @staticmethod
    def _parse_simple_yaml(text: str) -> Dict[str, Any]:
        result = {}
        current_list_key = None
        for line in text.split("\n"):
            line = line.rstrip()
            if not line or line.strip().startswith("#"):
                continue

            if line.strip().startswith("- ") and current_list_key:
                item = line.strip()[2:].strip()
                result[current_list_key].append(item)
                continue

            if ":" in line:
                k, v = line.split(":", 1)
                k = k.strip()
                v = v.strip()
                if not v:
                    result[k] = []
                    current_list_key = k
                else:
                    current_list_key = None
                    if v.lower() in ("true", "yes"):
                        result[k] = True
                    elif v.lower() in ("false", "no"):
                        result[k] = False
                    elif v.startswith("[") and v.endswith("]"):
                        try:
                            result[k] = json.loads(v)
                        except Exception:
                            result[k] = [x.strip() for x in v[1:-1].split(",")]
                    else:
                        result[k] = v
        return result
