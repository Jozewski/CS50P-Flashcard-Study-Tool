import csv
import json
import os
import sys

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text

console = Console()

SCORES_PATH = "scores/scores.json"
DECKS_DIR = "decks"


def main():
    console.print(Panel.fit(
        "[bold cyan]CS50P Flashcard Study Tool[/bold cyan]\n"
        "[dim]Spaced repetition — weakest cards come first[/dim]",
        border_style="cyan"
    ))

    while True:
        # ── Deck selection ──────────────────────────────────────────
        decks = list_decks(DECKS_DIR)
        if not decks:
            console.print("[red]No deck files found in the decks/ folder.[/red]")
            sys.exit(1)

        console.print("\n[bold]Available decks:[/bold]")
        for i, (name, _) in enumerate(decks, 1):
            label = name.replace("_", " ").title()
            console.print(f"  [cyan]{i}.[/cyan] {label}")

        console.print("  [cyan]q.[/cyan] Quit\n")

        choice = console.input("[bold]Choose a deck: [/bold]").strip().lower()

        if choice == "q":
            console.print("\n[dim]See you next time. Keep studying![/dim]\n")
            break

        if not choice.isdigit() or not (1 <= int(choice) <= len(decks)):
            console.print("[yellow]Invalid choice. Please enter a number from the list.[/yellow]")
            continue

        deck_name, filepath = decks[int(choice) - 1]

        # ── Load deck and scores ────────────────────────────────────
        try:
            cards = load_deck(filepath)
        except (FileNotFoundError, ValueError) as e:
            console.print(f"[red]Error loading deck: {e}[/red]")
            continue

        scores = load_scores(SCORES_PATH)
        cards = get_weak_cards(cards, scores, deck_name)

        label = deck_name.replace("_", " ").title()
        console.print(f"\n[bold green]Starting:[/bold green] {label}  "
                      f"[dim]({len(cards)} cards)[/dim]\n")

        # ── Quiz loop ───────────────────────────────────────────────
        session_correct = 0
        session_total = len(cards)

        for i, card in enumerate(cards):
            card_key = f"{deck_name}_{card['id']}"

            # Show question
            console.print(format_question(card, i + 1, session_total))
            console.input("[dim]Press Enter to reveal answer...[/dim]")

            # Show answer
            console.print(f"\n[bold green]Answer:[/bold green] {card['answer']}\n")

            # Get response with validation
            while True:
                response = console.input(
                    "[bold]Did you get it right?[/bold] [dim](y/n):[/dim] "
                ).strip().lower()
                if response in ("y", "n"):
                    break
                console.print("[yellow]Please enter y or n.[/yellow]")

            got_it = response == "y"
            scores = score_card(scores, card_key, got_it)

            if got_it:
                session_correct += 1
                console.print("[green]✓ Nice work![/green]\n")
            else:
                console.print("[red]✗ Keep at it — this card will come back around.[/red]\n")

        # ── Save scores ─────────────────────────────────────────────
        save_scores(scores, SCORES_PATH)

        # ── Session summary ─────────────────────────────────────────
        print_session_summary(cards, scores, deck_name, session_correct, session_total)

        # ── Play again? ─────────────────────────────────────────────
        again = console.input(
            "\n[bold]Study another deck?[/bold] [dim](y/n):[/dim] "
        ).strip().lower()
        if again != "y":
            console.print("\n[dim]Scores saved. See you next time![/dim]\n")
            break


# --- Deck Loading ---

def load_deck(filepath):
    """Load flashcards from a CSV file. Returns a list of card dicts."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Deck file not found: {filepath}")
    cards = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cards.append(row)
    if not cards:
        raise ValueError(f"Deck file is empty: {filepath}")
    return cards


# --- Score Logic ---

def score_card(scores, card_key, correct):
    """Update scores dict for a given card key. Returns updated scores dict."""
    if card_key not in scores:
        scores[card_key] = {"correct": 0, "incorrect": 0}
    if correct:
        scores[card_key]["correct"] += 1
    else:
        scores[card_key]["incorrect"] += 1
    return scores


def calculate_percentage(correct, incorrect):
    """Return correct percentage as a float. Returns 0.0 if no attempts."""
    total = correct + incorrect
    if total == 0:
        return 0.0
    return round((correct / total) * 100, 2)


def get_weak_cards(cards, scores, deck_name):
    """Sort cards so unseen and weakest cards come first. Returns sorted list."""
    def weakness_score(card):
        key = f"{deck_name}_{card['id']}"
        if key not in scores:
            return -1.0  # unseen cards always come first
        c = scores[key]["correct"]
        i = scores[key]["incorrect"]
        return calculate_percentage(c, i)

    return sorted(cards, key=weakness_score)


# --- Persistence ---

def load_scores(filepath):
    """Load scores from JSON file. Returns empty dict if file doesn't exist."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_scores(scores, filepath):
    """Write scores dict to JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)


# --- Display ---

def format_question(card, index, total):
    """Return a formatted question string for display."""
    return (
        f"\n{'='*50}\n"
        f"[{index}/{total}]  Topic: {card.get('topic', 'General')}\n"
        f"{'='*50}\n"
        f"\n{card['question']}\n"
    )


# --- Session Summary ---

def print_session_summary(cards, scores, deck_name, session_correct, session_total):
    """Print a rich table summarising this session's results."""
    pct = calculate_percentage(session_correct, session_total - session_correct)

    if pct == 100.0:
        color = "bold green"
        verdict = "Perfect session!"
    elif pct >= 70.0:
        color = "bold yellow"
        verdict = "Good work — review the ones you missed."
    else:
        color = "bold red"
        verdict = "Keep practicing — the weak cards will keep coming first."

    console.print(f"\n[{color}]Session complete: {session_correct}/{session_total} correct ({pct}%)[/{color}]")
    console.print(f"[dim]{verdict}[/dim]\n")

    # Build per-card summary table
    table = Table(
        title=f"Card Results — {deck_name.replace('_', ' ').title()}",
        box=box.SIMPLE_HEAVY,
        show_lines=True
    )
    table.add_column("Topic", style="cyan", no_wrap=True)
    table.add_column("Question", style="white", max_width=45)
    table.add_column("All-time Correct", justify="center")
    table.add_column("All-time Incorrect", justify="center")
    table.add_column("Score %", justify="center")

    for card in cards:
        key = f"{deck_name}_{card['id']}"
        c = scores.get(key, {}).get("correct", 0)
        inc = scores.get(key, {}).get("incorrect", 0)
        p = calculate_percentage(c, inc)
        score_str = f"{p}%"
        if p >= 80:
            score_str = f"[green]{score_str}[/green]"
        elif p >= 50:
            score_str = f"[yellow]{score_str}[/yellow]"
        else:
            score_str = f"[red]{score_str}[/red]"
        table.add_row(
            card.get("topic", ""),
            card["question"],
            str(c),
            str(inc),
            score_str
        )

    console.print(table)


# --- Deck Selection ---

def list_decks(decks_dir):
    """Return a list of (deck_name, filepath) tuples from the decks directory."""
    if not os.path.exists(decks_dir):
        return []
    decks = []
    for filename in sorted(os.listdir(decks_dir)):
        if filename.endswith(".csv"):
            name = filename.replace(".csv", "")
            decks.append((name, os.path.join(decks_dir, filename)))
    return decks


if __name__ == "__main__":
    main()