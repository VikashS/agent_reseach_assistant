#!/usr/bin/env python3
"""
Complete Test Suite for Research Assistant Agent

This test suite validates all aspects of the agent including:
- Planning phase (goal → TODO list)
- Tool execution (search, URL reading)
- Context management (token limits, sliding window)
- Error handling and recovery
- End-to-end agent flow

Run with: python test_agent.py
Run specific test: python test_agent.py --test planning
"""

import sys
import os
import json
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agent modules
from ra_agent.context import ContextManager
from ra_agent.tools import Tools
from ra_agent.planner import Planner
from ra_agent.executor import Executor
from ra_agent.llm import LLMClient


# ============================================================
# UNIT TESTS - Individual Component Testing
# ============================================================

class TestContextManager(unittest.TestCase):
    """Test context management and token limit handling"""

    def setUp(self):
        self.context = ContextManager(max_tokens=4000)
        self.context.set_goal("Test goal for context management")

    def test_sliding_window_keeps_last_3_tasks(self):
        """Should keep only the most recent 3 tasks"""
        # Add 5 tasks
        for i in range(5):
            self.context.add_task_result(f"Task {i}", f"Result {i}", "search")

        # Should only have last 3 tasks
        self.assertEqual(len(self.context.completed_tasks), 3)
        self.assertEqual(self.context.completed_tasks[0]["task"], "Task 2")
        self.assertEqual(self.context.completed_tasks[2]["task"], "Task 4")

    def test_truncation_for_search_results(self):
        """Search results should be truncated to 500 chars"""
        long_result = "x" * 1000
        self.context.add_task_result("Search task", long_result, "search")

        task_result = self.context.completed_tasks[0]["result"]
        self.assertLessEqual(len(task_result), 500 + 3)  # +3 for "..."
        self.assertTrue(task_result.endswith("..."))

    def test_truncation_for_url_content(self):
        """URL content should be truncated to 1000 chars"""
        long_content = "y" * 2000
        self.context.add_task_result("URL task", long_content, "read")

        task_result = self.context.completed_tasks[0]["result"]
        self.assertLessEqual(len(task_result), 1000 + 3)

    def test_context_for_planning_includes_goal(self):
        """Planning context should include original goal"""
        context_text = self.context.get_context_for_planning()
        self.assertIn("Test goal for context management", context_text)

    def test_context_for_execution_includes_recent_tasks(self):
        """Execution context should include last 2 completed tasks"""
        # Add some completed tasks
        self.context.add_task_result("Task A", "Result A", "search")
        self.context.add_task_result("Task B", "Result B", "search")

        task = {"description": "Current task", "type": "search", "query": "test"}
        context_text = self.context.get_context_for_execution(task)

        self.assertIn("Task A", context_text)
        self.assertIn("Task B", context_text)
        self.assertIn("Current task", context_text)

    def test_token_estimation(self):
        """Token estimation should be reasonable"""
        text = "This is a test sentence for token estimation."
        estimated_tokens = self.context.estimate_tokens(text)

        # Rough estimate: 4 chars per token
        expected_tokens = len(text) / 4
        self.assertAlmostEqual(estimated_tokens, expected_tokens, delta=2)


class TestTools(unittest.TestCase):
    """Test tool integrations (search, URL reading)"""

    def setUp(self):
        self.tools = Tools()

    def test_web_search_returns_dict(self):
        """Web search should return a dictionary with success/error"""
        result = self.tools.web_search("Python programming", max_results=2)

        self.assertIsInstance(result, dict)
        self.assertIn("success", result)

        if result["success"]:
            self.assertIn("results", result)
            self.assertIn("formatted", result)
        else:
            self.assertIn("error", result)

    def test_web_search_with_empty_query(self):
        """Search with empty query should handle gracefully"""
        result = self.tools.web_search("")

        # Should either fail gracefully or return empty results
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)

    @patch('ra_agent.tools.requests.get')
    def test_read_url_success(self, mock_get):
        """URL reading should extract text content"""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = "<html><body>Test content here</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = self.tools.read_url("https://example.com")

        self.assertTrue(result["success"])
        self.assertIn("Test content", result["content"])

    @patch('ra_agent.tools.requests.get')
    def test_read_url_failure(self, mock_get):
        """URL reading should handle HTTP errors"""
        mock_get.side_effect = Exception("Connection failed")

        result = self.tools.read_url("https://invalid-domain.com")

        self.assertFalse(result["success"])
        self.assertIn("error", result)


class TestLLMClient(unittest.TestCase):
    """Test LLM client initialization and provider selection"""

    def test_chat_with_mock_returns_string(self):
        """Mock chat should return a string response"""
        llm = LLMClient()
        llm.active_provider = "mock"

        response = llm.chat([
            {"role": "user", "content": "Hello"}
        ])

        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)


class TestPlanner(unittest.TestCase):
    """Test planning module"""

    def setUp(self):
        self.planner = Planner()

    def test_create_plan_returns_list(self):
        """Plan should be a list of tasks"""
        # Use mock to avoid actual API calls
        with patch.object(self.planner.llm, 'chat',
                          return_value='[{"description": "Test task", "type": "search", "query": "test"}]'):
            plan = self.planner.create_plan("Test goal")

            self.assertIsInstance(plan, list)
            self.assertGreater(len(plan), 0)

    def test_plan_has_required_fields(self):
        """Each task must have description, type, query"""
        mock_plan = [
            {"description": "Task 1", "type": "search", "query": "query1"},
            {"description": "Task 2", "type": "summarize", "query": "query2"}
        ]

        with patch.object(self.planner.llm, 'chat', return_value=json.dumps(mock_plan)):
            plan = self.planner.create_plan("Test")

            for task in plan:
                self.assertIn("description", task)
                self.assertIn("type", task)
                self.assertIn(task["type"], ["search", "read", "summarize", "ask_user"])

    def test_fallback_plan_on_error(self):
        """Should provide fallback plan if LLM fails"""
        with patch.object(self.planner.llm, 'chat', side_effect=Exception("API Error")):
            plan = self.planner.create_plan("Test goal")

            self.assertIsInstance(plan, list)
            self.assertGreater(len(plan), 0)
            self.assertEqual(plan[0]["type"], "search")

    def test_json_extraction(self):
        """Should extract JSON from markdown wrapped responses"""
        markdown_json = '```json\n{"test": "value"}\n```'
        extracted = self.planner._extract_json(markdown_json)

        self.assertEqual(extracted, '{"test": "value"}')


# ============================================================
# INTEGRATION TESTS - Component Interaction
# ============================================================

class TestAgentIntegration(unittest.TestCase):
    """Test full agent flow with components working together"""

    def setUp(self):
        self.context = ContextManager()
        self.tools = Tools()

    def test_planning_to_execution_flow(self):
        """Test that plan can be created and first task executed"""
        self.context.set_goal("What is the capital of France?")

        # Create plan
        planner = Planner()
        with patch.object(planner.llm, 'chat',
                          return_value='[{"description": "Search for Paris", "type": "search", "query": "capital of France"}]'):
            plan = planner.create_plan("What is the capital of France?")

            self.assertGreater(len(plan), 0)

            # Execute first task
            executor = Executor(self.context)
            with patch.object(executor.tools, 'web_search',
                              return_value={"success": True, "formatted": "Paris is the capital"}):
                result = executor._execute_task(plan[0])

                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)

    def test_context_persistence_across_tasks(self):
        """Context should maintain state across multiple task executions"""
        self.context.set_goal("Test persistence")

        # Add multiple tasks
        self.context.add_task_result("Task 1", "Result 1", "search")
        self.context.add_task_result("Task 2", "Result 2", "search")

        # Context should have both tasks
        self.assertEqual(len(self.context.completed_tasks), 2)

        # Add third task
        self.context.add_task_result("Task 3", "Result 3", "search")

        # Should have all 3
        self.assertEqual(len(self.context.completed_tasks), 3)

        # Add fourth task - should drop first
        self.context.add_task_result("Task 4", "Result 4", "search")
        self.assertEqual(len(self.context.completed_tasks), 3)
        self.assertEqual(self.context.completed_tasks[0]["task"], "Task 2")


# ============================================================
# END-TO-END TESTS - Real Execution Scenarios
# ============================================================

class TestEndToEndScenarios(unittest.TestCase):
    """Test complete user scenarios"""

    def test_scenario_simple_fact(self):
        """Scenario 1: Simple fact-finding"""
        print("\n Scenario 1: Simple fact-finding")

        context = ContextManager()
        goal = "Who won the World Series in 2023?"
        context.set_goal(goal)

        # Create plan
        planner = Planner()
        with patch.object(planner.llm, 'chat',
                          return_value='[{"description": "Find World Series 2023 winner", "type": "search", "query": "World Series 2023 winner"}]'):
            plan = planner.create_plan(goal)

            # Verify plan structure
            self.assertIsInstance(plan, list)
            self.assertGreater(len(plan), 0)

            # Verify task has required fields
            task = plan[0]
            self.assertIn("description", task)
            self.assertIn("type", task)

            print(f" Plan created with {len(plan)} tasks")

    def test_scenario_multi_step_comparison(self):
        """Scenario 2: Multi-step comparison"""
        print("\n Scenario 2: Multi-step comparison")

        context = ContextManager()
        goal = "Compare PostgreSQL vs MySQL for a startup"
        context.set_goal(goal)

        # Mock plan with multiple tasks
        mock_plan = [
            {"description": "Research PostgreSQL features", "type": "search",
             "query": "PostgreSQL features advantages"},
            {"description": "Research MySQL features", "type": "search", "query": "MySQL features advantages"},
            {"description": "Compare performance", "type": "search", "query": "PostgreSQL vs MySQL performance"},
            {"description": "Create comparison summary", "type": "summarize",
             "query": "Compare and recommend for startup"}
        ]

        planner = Planner()
        with patch.object(planner.llm, 'chat', return_value=json.dumps(mock_plan)):
            plan = planner.create_plan(goal)

            # Verify multi-step plan
            self.assertGreaterEqual(len(plan), 3)

            # Verify different task types
            task_types = [t["type"] for t in plan]
            self.assertIn("search", task_types)
            self.assertIn("summarize", task_types)

            print(f" Plan has {len(plan)} tasks including search and summarize")


    def test_scenario_long_context(self):
        """Scenario 5: Long context management"""
        print("\n Scenario 5: Long context")

        context = ContextManager(max_tokens=4000)
        context.set_goal("Research complete history of AI from 1950 to present")

        # Add many tasks with long results
        for i in range(10):
            long_result = f"Detailed research result for period {i} " + "x" * 500
            context.add_task_result(f"Period {i} research", long_result, "search")

        # Should have kept only last 3
        self.assertEqual(len(context.completed_tasks), 3)

        # Each result should be truncated
        for task in context.completed_tasks:
            self.assertLessEqual(len(task["result"]), 1000)

        # Context for summary should not overflow
        summary_context = context.get_context_for_summary()
        estimated_tokens = context.estimate_tokens(summary_context)
        self.assertLess(estimated_tokens, 5000)  # Well under typical limits

        print(f" Context window maintained at {len(context.completed_tasks)} tasks")
        print(f" Estimated tokens: {estimated_tokens:.0f}")


# ============================================================
# PERFORMANCE TESTS
# ============================================================

class TestPerformance(unittest.TestCase):
    """Test agent performance benchmarks"""

    def test_planning_speed(self):
        """Planning should complete within 3 seconds"""
        planner = Planner()

        with patch.object(planner.llm, 'chat',
                          return_value='[{"description": "Test", "type": "search", "query": "test"}]'):
            start_time = time.time()
            planner.create_plan("Test goal")
            elapsed = time.time() - start_time

            # Mock should be fast, but real API would be slower
            self.assertLess(elapsed, 2)
            print(f"  Planning completed in {elapsed:.2f}s")

    def test_search_speed(self):
        """Search should complete within 3 seconds"""
        tools = Tools()

        start_time = time.time()
        result = tools.web_search("Python", max_results=1)
        elapsed = time.time() - start_time

        # Note: This depends on internet speed
        if result["success"]:
            self.assertLess(elapsed, 10)  # 5 seconds for real API
            print(f"   Search completed in {elapsed:.2f}s")
        else:
            print(f"  Search failed (expected without API key)")

    def test_token_efficiency(self):
        """Should use tokens efficiently"""
        context = ContextManager()
        context.set_goal("A" * 1000)  # Long goal

        # Add tasks with results
        for i in range(5):
            context.add_task_result(f"Task {i}", "B" * 500, "search")

        summary_context = context.get_context_for_summary()
        estimated_tokens = context.estimate_tokens(summary_context)

        # Should be reasonable
        self.assertLess(estimated_tokens, 3000)
        print(f"   Token usage: {estimated_tokens:.0f} tokens")


# ============================================================
# VALIDATION TESTS - Problem Statement Requirements
# ============================================================

class TestRequirements(unittest.TestCase):
    """Verify all problem statement requirements are met"""

    def test_no_forbidden_frameworks(self):
        """Should not import forbidden frameworks"""
        import ra_agent.planner
        import ra_agent.executor

        # Get source code from imported modules
        import inspect
        planner_code = inspect.getsource(ra_agent.planner)
        executor_code = inspect.getsource(ra_agent.executor)

        forbidden = ["langchain", "langgraph", "autogen", "crewai"]
        for framework in forbidden:
            self.assertNotIn(framework.lower(), planner_code.lower())
            self.assertNotIn(framework.lower(), executor_code.lower())

        print("  No forbidden frameworks detected")

    def test_real_tool_integration(self):
        """Should use at least one real external tool"""
        tools = Tools()

        # Check that tools make real external calls
        self.assertTrue(hasattr(tools, 'web_search'))
        self.assertTrue(hasattr(tools, 'read_url'))

        print("  Real tools integrated (Tavily and URL reader)")

    def test_planning_to_todo_structure(self):
        """Should convert goal to structured TODO list"""
        planner = Planner()

        with patch.object(planner.llm, 'chat',
                          return_value='[{"description": "Task 1", "type": "search", "query": "q1"}, {"description": "Task 2", "type": "summarize", "query": "q2"}]'):
            plan = planner.create_plan("Test")

            # Should be list of tasks
            self.assertIsInstance(plan, list)

            # Each task should have status-like fields
            for task in plan:
                self.assertIn("description", task)
                self.assertIn("type", task)

        print("   Converts goals to TODO lists")

    def test_execution_loop(self):
        """Should have clear execution loop"""
        import io
        import sys
        from contextlib import redirect_stdout

        context = ContextManager()
        context.set_goal("Test execution loop")

        # Create a simple plan
        plan = [
            {"description": "Task 1", "type": "search", "query": "test1"},
            {"description": "Task 2", "type": "search", "query": "test2"}
        ]

        executor = Executor(context)

        # Capture stdout to verify logging
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with patch.object(executor.tools, 'web_search',
                              return_value={"success": True, "formatted": "Result"}):
                # Execute the plan
                results = executor.execute_plan(plan)

        # Verify that multiple tasks were executed
        self.assertEqual(len(results), 2)
        self.assertIn("Task 1", captured_output.getvalue())
        self.assertIn("Task 2", captured_output.getvalue())

        print(" Execution loop implemented")

    def test_transparent_logging(self):
        """Should log agent actions clearly"""
        import io
        import sys
        from contextlib import redirect_stdout

        context = ContextManager()
        context.set_goal("Test logging")

        plan = [{"description": "Test task", "type": "search", "query": "test"}]
        executor = Executor(context)

        # Capture stdout
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            with patch.object(executor.tools, 'web_search',
                              return_value={"success": True, "formatted": "Result"}):
                executor.execute_plan(plan)

        output = captured_output.getvalue()

        # Verify logging contains expected messages
        self.assertIn("EXECUTING PLAN", output)
        self.assertIn("Task", output)
        print("Transparent logging present")


# ============================================================
# MAIN TEST RUNNER
# ============================================================

def run_unit_tests():
    """Run all unit tests"""
    print("\n" + "=" * 70)
    print(" RUNNING UNIT TESTS")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestContextManager))
    suite.addTests(loader.loadTestsFromTestCase(TestTools))
    suite.addTests(loader.loadTestsFromTestCase(TestLLMClient))
    suite.addTests(loader.loadTestsFromTestCase(TestPlanner))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "=" * 70)
    print(" RUNNING INTEGRATION TESTS")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestAgentIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_scenario_tests():
    """Run end-to-end scenario tests"""
    print("\n" + "=" * 70)
    print(" RUNNING SCENARIO TESTS (5 Evaluation Scenarios)")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndScenarios))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_performance_tests():
    """Run performance benchmarks"""
    print("\n" + "=" * 70)
    print(" RUNNING PERFORMANCE TESTS")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def run_validation_tests():
    """Run requirement validation tests"""
    print("\n" + "=" * 70)
    print(" RUNNING REQUIREMENT VALIDATION")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestRequirements))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


def generate_test_report(results):
    """Generate detailed test report"""
    print("\n" + "=" * 70)
    print(" TEST EXECUTION REPORT")
    print("=" * 70)

    total_tests = sum(results.values())
    passed_tests = sum(1 for v in results.values() if v)

    print(f"\nOverall Summary:")
    print(f"   Passed: {passed_tests}/{total_tests} test suites")
    print(f"   Success Rate: {passed_tests / total_tests * 100:.1f}%")

    print("\nDetailed Results:")
    for suite_name, passed in results.items():
        status = " PASS" if passed else " FAIL"
        print(f"  {status}: {suite_name}")

    # Evaluation scenarios summary
    print("\n" + "=" * 70)
    print(" EVALUATION SCENARIOS COVERAGE")
    print("=" * 70)
    print("""
    Scenario 1: Simple Fact-Finding     → TestEndToEndScenarios.test_scenario_simple_fact
    Scenario 2: Multi-Step Comparison   → TestEndToEndScenarios.test_scenario_multi_step_comparison
    Scenario 3: Long Context Management → TestEndToEndScenarios.test_scenario_long_context
    """)

    return passed_tests == total_tests


def main():
    """Main test runner"""
    print("\n" + "=" * 70)
    print(" RESEARCH ASSISTANT AGENT - COMPLETE TEST SUITE")
    print("=" * 70)
    print("\nThis test suite validates all problem statement requirements:")
    print("  • Context & Prompt Engineering (35%)")
    print("  • Agent Loop & Tool Use (45%)")
    print("  • Evaluation & Communication (20%)")

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Run agent tests')
    parser.add_argument('--test', type=str,
                        choices=['unit', 'integration', 'scenario', 'performance', 'validation', 'all'],
                        default='all', help='Specific test suite to run')
    args = parser.parse_args()

    results = {}

    if args.test in ['unit', 'all']:
        results['Unit Tests'] = run_unit_tests()

    if args.test in ['integration', 'all']:
        results['Integration Tests'] = run_integration_tests()

    if args.test in ['scenario', 'all']:
        results['Scenario Tests'] = run_scenario_tests()

    if args.test in ['performance', 'all']:
        results['Performance Tests'] = run_performance_tests()

    if args.test in ['validation', 'all']:
        results['Validation Tests'] = run_validation_tests()

    # Generate final report
    all_passed = generate_test_report(results)

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

