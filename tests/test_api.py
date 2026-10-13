"""
Tests for API service layer and event bus.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.service import (
    list_available_agents,
    list_available_tools,
    get_agent_info,
    execute_tool_api,
    subscribe_events,
    unsubscribe_events
)
from core.event_bus import default_bus, EventType

class TestApiService(unittest.TestCase):
    def test_list_agents(self):
        agents = list_available_agents()
        agent_ids = [a["id"] for a in agents]
        self.assertIn("coder", agent_ids)
        self.assertIn("planner", agent_ids)
        self.assertIn("tester", agent_ids)

    def test_list_tools(self):
        tools_list = list_available_tools()
        tool_names = [t["name"] for t in tools_list]
        self.assertIn("read", tool_names)
        self.assertIn("write", tool_names)
        self.assertIn("run", tool_names)

    def test_get_agent_info(self):
        info = get_agent_info("coder")
        self.assertIsNotNone(info)
        self.assertEqual(info["name"], "coder")

    def test_execute_tool_api(self):
        res = execute_tool_api("read", {"path": "rule/rule.md"})
        self.assertTrue(res["success"])
        self.assertIn("万物皆插件", res["data"]["content"])

    def test_event_subscription(self):
        received = []
        def handler(event):
            received.append(event)

        subscribe_events(handler)
        default_bus.publish(EventType.LOG, {"msg": "test event"}, "test_agent")
        unsubscribe_events(handler)

        self.assertTrue(any(e.data.get("msg") == "test event" for e in received))

if __name__ == "__main__":
    unittest.main()
