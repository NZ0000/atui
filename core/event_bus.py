"""
Event Bus for atui.
Provides structured event streaming and subscription hooks for CLI, GUI, H5, App, and desktop UIs.
"""

import json
import time
from typing import Callable, List, Dict, Any, Optional
from enum import Enum

class EventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_STEP = "agent_step"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    GATE_CHECK = "gate_check"
    GATE_RESULT = "gate_result"
    TDD_CYCLE = "tdd_cycle"
    GIT_ACTION = "git_action"
    AGENT_FINISH = "agent_finish"
    PIPELINE_STEP = "pipeline_step"
    LOG = "log"

class Event:
    def __init__(self, event_type: EventType, data: Dict[str, Any], agent_name: Optional[str] = None):
        self.type = event_type.value if isinstance(event_type, EventType) else str(event_type)
        self.timestamp = time.time()
        self.agent_name = agent_name
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "timestamp": self.timestamp,
            "agent_name": self.agent_name,
            "data": self.data
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

class EventBus:
    def __init__(self):
        self._subscribers: List[Callable[[Event], None]] = []
        self._history: List[Event] = []

    def subscribe(self, callback: Callable[[Event], None]):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Event], None]):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def publish(self, event_type: EventType, data: Dict[str, Any], agent_name: Optional[str] = None) -> Event:
        event = Event(event_type, data, agent_name)
        self._history.append(event)
        for sub in self._subscribers:
            try:
                sub(event)
            except Exception as e:
                print(f"[EventBus Error] Subscriber failed: {e}")
        return event

    def get_history(self) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._history]

# Global default bus instance
default_bus = EventBus()
