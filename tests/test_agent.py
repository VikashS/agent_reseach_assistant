import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ra_agent.context import ContextManager

def test_context_basic():
    """Test basic context management"""
    context = ContextManager()
    context.set_goal("Research Python")

    context.add_task_result("Search task", "Found Django", "search")
    context.add_task_result("Read docs", "Django is web framework", "read")

    summary = context.get_context_for_summary()
    assert "Research Python" in summary
    assert "Django" in summary
    assert len(context.completed_tasks) == 2


def test_context_limits():
    """Test context limits and truncation"""
    context = ContextManager()

    # Add 5 tasks (more than limit of 3)
    for i in range(5):
        context.add_task_result(f"Task {i}", f"Result {i}", "search")

    # Should keep only last 3
    assert len(context.completed_tasks) == 3
    assert context.completed_tasks[0]["task"] == "Task 2"

    # Test truncation
    long_result = "A" * 600
    context.add_task_result("Long task", long_result, "search")
    result = context.completed_tasks[-1]["result"]
    assert len(result) == 503
    assert result.endswith("...")


def test_research_workflow():
    """Test complete research workflow"""
    context = ContextManager()
    context.set_goal("Compare frameworks")

    # Simulate research tasks
    tasks = [
        ("Search React", "React is component-based", "search"),
        ("Search Vue", "Vue is progressive", "search"),
        ("Compare both", "React for large apps, Vue for small", "summarize")
    ]

    for desc, result, task_type in tasks:
        context.add_task_result(desc, result, task_type)

    final_context = context.get_context_for_summary()
    assert "Compare frameworks" in final_context
    assert "React" in final_context
    assert "Vue" in final_context
    assert len(context.completed_tasks) == 3
