import os
import sys
from pathlib import Path

from specsmith.agent.broker import (
    classify_intent,
    execute_with_governance,
    infer_scope,
    narrate_plan,
    run_preflight,
)
from specsmith.agent.orchestrator import Orchestrator

NEXUS_BANNER = "Nexus — Local-first Agentic Development Environment (Specsmith-governed)"

def main():
    print(NEXUS_BANNER)
    print("Initializing Nexus runtime...")
    
    try:
        orchestrator = Orchestrator()
    except ImportError as e:
        print(f"Failed to initialize orchestrator: {e}")
        print("Falling back to basic CLI without full agent support.")
        sys.exit(1)
        
    print(
        "Agents ready. Type plain English to use the natural-language broker, "
        "or use slash commands (/plan, /ask, /fix, /why, /exit). "
        "Toggle governance details with /why."
    )
    
    project_dir = Path(os.getcwd())
    verbose_governance = False
    
    while True:
        try:
            user_input = input("\nnexus> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break
            
        if not user_input:
            continue
            
        if user_input.lower() in ["/exit", "/quit"]:
            print("Goodbye.")
            break
            
        # Parse command and args
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in ("/why", "/show-governance"):
            verbose_governance = not verbose_governance
            state = "on" if verbose_governance else "off"
            print(f"Governance details: {state}")
            continue
        
        if command == "/plan":
            if not args:
                print("Usage: /plan <task description>")
                continue
            orchestrator.run_task(f"[PLAN] Create a step-by-step plan for: {args}")
            
        elif command == "/ask":
            if not args:
                print("Usage: /ask <question>")
                continue
            orchestrator.run_task(f"[ASK] Clarify intent and answer the following question: {args}")
            
        elif command == "/fix":
            if not args:
                print("Usage: /fix <issue description or file>")
                continue
            orchestrator.run_task(f"[FIX] Modify code to fix the following issue: {args}")
            
        elif command == "/test":
            orchestrator.run_task(f"[TEST] Run tests for the project. {args}")
            
        elif command == "/commit":
            orchestrator.run_task(f"[COMMIT] Create a git commit for the current changes. {args}")
            
        elif command == "/pr":
            orchestrator.run_task(f"[PR] Prepare a pull request for the current branch. {args}")
            
        elif command == "/undo":
            orchestrator.run_task(f"[UNDO] Revert the last action or commit. {args}")
            
        elif command == "/context":
            orchestrator.run_task(f"[CONTEXT] Show repo knowledge and search context for: {args}")
            
        else:
            # Default mode (REQ-084 + REQ-086): plain English flows through the
            # broker. The broker classifies intent, infers scope, calls Specsmith
            # `preflight`, and renders a plain-language plan. The AG2 orchestrator
            # is only invoked when the preflight decision is `accepted`.
            try:
                intent = classify_intent(user_input)
                scope = infer_scope(
                    user_input,
                    project_dir / "REQUIREMENTS.md",
                    repo_index_path=project_dir / ".repo-index" / "files.json",
                )
                decision = run_preflight(user_input, project_dir)
                print(narrate_plan(intent, scope, decision, verbose=verbose_governance))
            except Exception as e:  # noqa: BLE001 - broker must never crash REPL
                print(f"(broker note: {e})")
                continue

            # REQ-086: gate execution on preflight acceptance.
            if decision.accepted:
                # REQ-087: drive orchestrator through the bounded-retry harness.
                # The executor closure is the ONLY place the broker branch is
                # allowed to call orchestrator.run_task; calling it directly
                # outside the harness would bypass REQ-014 retry bounds and
                # REQ-063 stop-and-align escalation.
                def _executor(_decision, attempt):
                    summary = orchestrator.run_task(user_input)
                    # The orchestrator currently returns a free-form string or
                    # None. Until the orchestrator emits a structured result
                    # the broker treats a successful, non-empty response as
                    # equilibrium with a confidence at the decision target.
                    confident = bool(summary) if summary is not None else True
                    return {
                        "equilibrium": confident,
                        "confidence": _decision.confidence_target if confident else 0.0,
                        "summary": summary if isinstance(summary, str) else "",
                    }

                result = execute_with_governance(decision, executor=_executor)
                if not result.success and result.clarifying_question:
                    print(result.clarifying_question)
            else:
                print("(no execution \u2014 preflight did not accept this request)")

if __name__ == "__main__":
    main()
