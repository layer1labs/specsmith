"""Service layer for the Todo API.

T4 REFACTOR TARGET: process_todo_batch() is intentionally monolithic.
Cyclomatic complexity ~14. The T4 task extracts 5 named helper functions.

Do NOT refactor this file unless you are running the T4 benchmark task.
"""

from __future__ import annotations

from app.models import TodoCreate, TodoItem

_BATCH_ID_COUNTER: int = 10000  # batch IDs start here to avoid collision with store IDs


def process_todo_batch(items: list[TodoCreate]) -> list[TodoItem]:  # noqa: C901  # complexity intentional for T4
    """Process a batch of todo creation requests.

    Steps (all interleaved — T4 will extract these into helpers):
      1. Validate each item (skip items with empty titles)
      2. Deduplicate by title (keep first occurrence)
      3. Assign sequential batch IDs
      4. Filter out already-completed items (completed flag on input)
      5. Sort by priority descending (high priority first)

    Returns the processed list of TodoItem objects.
    """
    global _BATCH_ID_COUNTER

    # --- Step 1: Validate ---
    validated = []
    for item in items:
        if not item.title or not item.title.strip():
            # Skip items with empty or whitespace-only titles
            continue
        if len(item.title.strip()) > 200:
            # Skip titles that are too long
            continue
        validated.append(item)

    # --- Step 2: Deduplicate by title (case-insensitive, keep first) ---
    seen_titles: set[str] = set()
    deduplicated = []
    for item in validated:
        normalised = item.title.strip().lower()
        if normalised in seen_titles:
            continue
        seen_titles.add(normalised)
        deduplicated.append(item)

    # --- Step 3: Assign batch IDs ---
    with_ids: list[TodoItem] = []
    for item in deduplicated:
        todo_item = TodoItem(
            id=_BATCH_ID_COUNTER,
            title=item.title.strip(),
            description=item.description,
            completed=False,
            priority=item.priority if 1 <= item.priority <= 3 else 1,
        )
        _BATCH_ID_COUNTER += 1
        with_ids.append(todo_item)

    # --- Step 4: Filter completed (input items with priority < 0 are pre-completed) ---
    # (Using priority < 0 as a sentinel for 'already done' since TodoCreate has no completed flag)
    active: list[TodoItem] = []
    for todo_item in with_ids:
        original = next(
            (i for i in deduplicated if i.title.strip() == todo_item.title),
            None,
        )
        if original is not None and original.priority < 0:
            # Marked as already completed — skip
            continue
        active.append(todo_item)

    # --- Step 5: Sort by priority descending ---
    active.sort(key=lambda x: x.priority, reverse=True)

    return active
