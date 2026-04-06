"""Entry point for the Research Assistant Agent"""

import sys
import time
from ra_agent.planner import Planner
from ra_agent.executor import Executor
from ra_agent.context import ContextManager


def main():
    # Get user goal
    print("\nWhat goal would you like help with?")
    print("Examples: research a topic, compare technologies, plan a project\n")
    user_goal = input(" Your goal: ").strip()

    if not user_goal:
        print("Please provide a goal to work on.")
        return

    print(f"\n Goal received: {user_goal}")

    # Initialize components
    context = ContextManager()
    context.set_goal(user_goal)

    planner = Planner()
    executor = Executor(context)

    # Step 1: Planning
    print("\n" + "=" * 60)
    print(" PHASE 1: PLANNING")
    print("=" * 60)
    print("Creating structured TODO plan from your goal...")

    plan = planner.create_plan(user_goal)
    context.set_plan(plan)

    print(f"\n Generated plan with {len(plan)} tasks:")
    for i, task in enumerate(plan, 1):
        print(f"   {i}. [{task['type'].upper()}] {task['description']}")

    # Step 2: Confirmation
    print("\n" + "=" * 60)
    proceed = input("\n Proceed with execution? (y/n): ").strip().lower()

    if proceed != 'y':
        print("Execution cancelled. Bye")
        return

    # Step 3: Execution
    print("\n" + "=" * 60)
    print("  PHASE 2: EXECUTION")
    print("=" * 60)

    start_time = time.time()
    results = executor.execute_plan(plan)
    execution_time = time.time() - start_time

    # Step 4: Final output
    print("\n" + "=" * 60)
    print(" PHASE 3: FINAL RESULTS")
    print("=" * 60)

    final_output = executor.generate_final_output(results)
    print(f"\n{final_output}")

    # Summary
    print("\n" + "=" * 60)
    print(" AGENT COMPLETE")
    print("=" * 60)
    print(f"Tasks executed: {len(results)}")
    print(f"Execution time: {execution_time:.2f} seconds")
    print("\nThanks for using the Research Assistant Agent!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n️  Interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n Error: {e}")
        print("Please add your details in .env file")
        sys.exit(1)