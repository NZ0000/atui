"""
Acceptance Criteria & Burn-Down Checklist Engine for atui.
Provides structured tracking, automated item check-off, and burn-down gate enforcement.
Defeats LLM lazy exit by verifying every atomic acceptance criterion before allowing task completion.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional, Tuple

class AcceptanceCriterion:
    def __init__(
        self,
        item_id: str,
        description: str,
        category: str = "functional",
        passed: bool = False,
        rationale: str = ""
    ):
        self.item_id = str(item_id)
        self.description = description.strip()
        self.category = category.lower()  # "functional", "aesthetic", "environment", "general"
        self.passed = passed
        self.rationale = rationale.strip()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item_id,
            "description": self.description,
            "category": self.category,
            "passed": self.passed,
            "rationale": self.rationale
        }

    def format_markdown(self) -> str:
        check = "x" if self.passed else " "
        line = f"- [{check}] **[{self.item_id}]** ({self.category.capitalize()}) {self.description}"
        if self.rationale:
            line += f" — *{self.rationale}*"
        return line


class AcceptanceChecklist:
    def __init__(self, title: str = "任务燃尽验收清单 (Acceptance Checklist)"):
        self.title = title
        self.items: List[AcceptanceCriterion] = []

    def add_item(self, description: str, category: str = "functional", item_id: Optional[str] = None) -> AcceptanceCriterion:
        if not item_id:
            item_id = f"AC-{len(self.items) + 1}"
        item = AcceptanceCriterion(item_id, description, category)
        self.items.append(item)
        return item

    def mark_item(self, id_or_keyword: str, passed: bool = True, rationale: str = "") -> bool:
        """Mark item by ID or matching keyword in description."""
        id_str = str(id_or_keyword).strip().lower()
        for it in self.items:
            if it.item_id.lower() == id_str or id_str in it.description.lower():
                it.passed = passed
                it.rationale = rationale
                return True
        return False

    def get_status(self) -> Dict[str, Any]:
        total = len(self.items)
        passed = sum(1 for it in self.items if it.passed)
        remaining = total - passed
        percent = (passed / total * 100.0) if total > 0 else 100.0
        return {
            "total": total,
            "passed": passed,
            "remaining": remaining,
            "percent": round(percent, 1),
            "is_burned_down": (remaining == 0 and total > 0),
            "remaining_items": [it.to_dict() for it in self.items if not it.passed],
            "passed_items": [it.to_dict() for it in self.items if it.passed]
        }

    def render_markdown(self) -> str:
        status = self.get_status()
        lines = [
            f"# {self.title}",
            "",
            f"> **验收进度**：已达成 `{status['passed']}/{status['total']}` 项（`{status['percent']}%`）"
            + (" ✔ 全部燃尽放行！" if status['is_burned_down'] else " ⏳ 尚有未达标项需修复"),
            ""
        ]

        # Group by category
        categories = ["environment", "functional", "aesthetic", "general"]
        cat_names = {
            "environment": "🌐 环境与部署指标 (Environment & Deploy)",
            "functional": "⚙️ 核心功能与架构指标 (Functional & Code)",
            "aesthetic": "🎨 视觉审美与交互体验 (Aesthetic & UX)",
            "general": "📋 通用工程交付指标 (General Delivery)"
        }

        for cat in categories:
            cat_items = [it for it in self.items if it.category == cat]
            if cat_items:
                lines.append(f"### {cat_names.get(cat, cat.capitalize())}")
                for it in cat_items:
                    lines.append(it.format_markdown())
                lines.append("")

        # Other categories
        other_items = [it for it in self.items if it.category not in categories]
        if other_items:
            lines.append("### 其他指标")
            for it in other_items:
                lines.append(it.format_markdown())
            lines.append("")

        if status["remaining"] > 0:
            lines.append("---")
            lines.append(f"**待自修复清单（剩余 {status['remaining']} 项）**：")
            for r in status["remaining_items"]:
                lines.append(f"- ❌ **[{r['id']}]** {r['description']}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def from_markdown(cls, md_text: str) -> "AcceptanceChecklist":
        """Parse markdown checklist containing lines like '- [ ] [AC-1] (Functional) ...' or '- [x] ...'"""
        checklist = cls()
        lines = md_text.split("\n")
        item_pattern = re.compile(r'^\s*[-*]\s*\[([ xX])\]\s*(.*)$')
        id_pattern = re.compile(r'\*\*\[(.*?)\]\*\*\s*(?:\((.*?)\))?\s*(.*)$')

        for line in lines:
            m = item_pattern.match(line)
            if m:
                checked = (m.group(1).lower() == 'x')
                rest = m.group(2).strip()

                cat = "functional"
                item_id = None
                desc = rest
                rationale = ""

                # Extract rationale if present (separated by ' — *...*' or ' - ...')
                if " — *" in rest and rest.endswith("*"):
                    parts = rest.rsplit(" — *", 1)
                    desc = parts[0].strip()
                    rationale = parts[1][:-1].strip()

                # Extract id & category
                id_m = id_pattern.match(desc)
                if id_m:
                    item_id = id_m.group(1).strip()
                    if id_m.group(2):
                        cat = id_m.group(2).strip().lower()
                    desc = id_m.group(3).strip()

                # Infer category from text if not explicit
                if any(w in desc.lower() for w in ["ui", "审美", "外观", "颜色", "色彩", "光照", "死黑", "美观", "排版", "视觉", "hud"]):
                    cat = "aesthetic"
                elif any(w in desc.lower() for w in ["服务", "端口", "http", "websocket", "mqtt", "环境", "依赖", "部署"]):
                    cat = "environment"

                item = checklist.add_item(desc, category=cat, item_id=item_id)
                item.passed = checked
                item.rationale = rationale

        return checklist

    def save_to_file(self, file_path: str):
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.render_markdown())

    @classmethod
    def load_from_file(cls, file_path: str) -> Optional["AcceptanceChecklist"]:
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return cls.from_markdown(content)
        except Exception:
            return None


def evaluate_burn_down_gate(checklist_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    """Evaluates whether an acceptance checklist is 100% burned down."""
    if not os.path.exists(checklist_path):
        return True, "No acceptance checklist file present, gate skipped.", {}

    cl = AcceptanceChecklist.load_from_file(checklist_path)
    if not cl or len(cl.items) == 0:
        return True, "Acceptance checklist is empty, gate passed.", {}

    status = cl.get_status()
    if status["is_burned_down"]:
        return True, f"All {status['total']} acceptance criteria are 100% burned down and verified.", status

    reason = (
        f"[ACCEPTANCE BURN-DOWN GATE FAILED]\n"
        f"当前任务验收清单尚未燃尽！达成度: {status['passed']}/{status['total']} ({status['percent']}%)\n"
        f"仍有 {status['remaining']} 项指标未满足，门禁拒绝退出：\n"
    )
    for rem in status["remaining_items"]:
        reason += f"  ❌ [{rem['id']}] ({rem['category']}) {rem['description']}\n"
    reason += "\n请调度 Coder 或对应智能体继续修复上述剩余未达标项，直至全部标记为 [x] 方可交付。"

    return False, reason, status
