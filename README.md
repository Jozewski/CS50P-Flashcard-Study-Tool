# CS50P Flashcard Study Tool

#### Video Demo: <https://youtu.be/A30xvncHYF8>

#### Description:

## What This Project Is

I built this as my CS50P final project, and the concept came directly from the course itself. The idea is simple: a command-line flashcard app where the decks cover the material taught in CS50P. Functions, exceptions, file I/O, regular expressions, object-oriented programming, and libraries. You study the course by using a tool built with the course skills. That felt like the right kind of project to close with.

The app uses spaced repetition. That means it tracks how well you know each card across sessions and always puts your weakest cards in front. Cards you keep missing come back sooner. Cards you have mastered move to the back. Over time it focuses your study time where it actually needs to go instead of cycling through everything at the same pace regardless of how well you know it.

Your scores are saved to a JSON file every time you finish a session, so your progress carries over every time you run the program.

---

## How to Run It

**Install the dependencies:**
```
pip install -r requirements.txt
```

**Run the app:**
```
python project.py
```

**Run the tests:**
```
python -m pytest test_project.py
```

---

## Project Structure

```
project/
├── project.py          -- Main application logic
├── test_project.py     -- Pytest test suite (25 tests)
├── requirements.txt    -- Third-party dependencies
├── README.md           -- This file
├── decks/
│   ├── functions.csv
│   ├── exceptions.csv
│   ├── file_io.csv
│   ├── regex.csv
│   ├── oop.csv
│   └── libraries.csv
└── scores/
    └── scores.json     -- Auto-generated on first run
```

---

## File Breakdown

### `project.py`

This file contains `main()` and every supporting function. All functions are defined at the top level of the module, not nested inside anything else.

**`main()`**

This is where everything connects. It renders the title panel using `rich`, lists the available decks, handles the user's selection, runs the quiz loop card by card, and calls `print_session_summary()` when the session ends. If you want to study another deck, `main()` loops back to the menu without restarting the program.

**`load_deck(filepath)`**

Opens a CSV file and returns a list of card dictionaries, one per row. It raises `FileNotFoundError` if the path does not exist and `ValueError` if the file is empty. I used `csv.DictReader` so each card already comes back as a dictionary with named keys like `question`, `answer`, `topic`, and `id`. That keeps the rest of the code clean because nothing downstream has to worry about column positions.

**`score_card(scores, card_key, correct)`**

Takes the current scores dictionary, a unique card key in the format `deckname_cardid`, and a boolean for whether the user got it right. It creates a new entry if one does not exist yet, then increments either the correct or incorrect counter and returns the updated dictionary. This function does one thing and returns its result cleanly, which made it easy to test with pytest.

**`calculate_percentage(correct, incorrect)`**

Takes a correct count and an incorrect count and returns the correct percentage as a float. If both values are zero, meaning the card has never been seen before, it returns 0.0 instead of raising a ZeroDivisionError. That edge case matters because unseen cards need to sort to the front of the queue, which the next function handles.

**`get_weak_cards(cards, scores, deck_name)`**

Sorts the card list so the weakest cards come first. Any card with no score history gets assigned a sort value of -1.0, which puts it ahead of even cards with a 0% correct rate. This way brand-new cards always surface early. I used Python's built-in `sorted()` with a key function rather than writing a manual loop. It keeps the logic compact and the intent clear.

**`load_scores(filepath)`**

Opens the scores JSON file and returns its contents as a Python dictionary. If the file does not exist yet, which happens on the very first run, it returns an empty dictionary instead of raising an error. That means `main()` can always call `load_scores()` and always get a dictionary back. No extra logic needed to handle a first-run state.

**`save_scores(scores, filepath)`**

Writes the scores dictionary to disk as formatted JSON. I used `json.dump()` with `indent=2` so the file is readable if you ever want to open it and see what your scores actually look like, or reset a specific card. It also calls `os.makedirs()` with `exist_ok=True` before writing, so the `scores/` directory gets created automatically if it is not there yet.

**`format_question(card, index, total)`**

Builds and returns the formatted string that gets printed when a card is shown. It includes the card's position in the deck, the topic name, and the question text. I pulled this into its own function instead of putting it directly in `main()` so it could be tested independently and so changing the display format only requires touching one place.

**`print_session_summary(cards, scores, deck_name, session_correct, session_total)`**

Runs at the end of each session. It calculates the session score, prints a color-coded verdict using `rich` (green for 100%, yellow for 70% or above, red for below 70%), and renders a table with every card's all-time correct count, incorrect count, and score percentage. Each row is color-coded individually so you can see at a glance which topics still need work.

**`list_decks(decks_dir)`**

Scans the decks folder for CSV files and returns a list of name and filepath pairs sorted alphabetically. Because it discovers decks dynamically rather than hardcoding them, you can drop a new CSV into the `decks/` folder and it shows up in the menu automatically without touching any code.

---

### `test_project.py`

This file contains 25 pytest tests. The functions covered are `load_deck`, `score_card`, `calculate_percentage`, `get_weak_cards`, `format_question`, `load_scores`, and `save_scores`. Each function has multiple tests covering a normal case, at least one edge case, and where it makes sense a failure case as well.

The tests for `load_deck` use Python's `tempfile` module to create actual temporary CSV files on disk rather than mocking anything. That means they test the real file-reading behavior end to end. The tests for `load_scores` and `save_scores` do the same thing with temporary directories to verify the full persistence roundtrip.

---

### `requirements.txt`

Two libraries:

**`rich`** handles all the colored terminal output: the title panel, the per-card feedback, and the session summary table. Color-coded contrast in the terminal matters to me because I work with assistive technology and I think about accessibility in everything I build. `rich` makes it possible to do that without a lot of extra code.

---

### The `decks/` folder

Six CSV files, one per CS50P topic. The format is the same across all of them: `id`, `topic`, `question`, `answer`. The `id` column has to be unique within each deck because card keys in `scores.json` are built as `deckname_id`. If two cards in the same deck share an id, their scores would overwrite each other.

Here is what each deck covers:

**`functions.csv`** -- 15 cards on `def`, parameters, `*args`, `**kwargs`, scope, return values, lambda functions, and docstrings.

**`exceptions.csv`** -- 16 cards on `try`, `except`, `else`, `finally`, `raise`, the most common built-in exception types, and how to write a custom exception class.

**`file_io.csv`** -- 12 cards on `open()`, the `with` block, file modes, `csv.DictReader`, `csv.DictWriter`, `json.dump()`, and `json.load()`.

**`regex.csv`** -- 20 cards on `re.search()`, `re.match()`, `re.fullmatch()`, `re.sub()`, `re.findall()`, metacharacters, capture groups, and flags.

**`oop.csv`** -- 17 cards on classes, instances, `__init__`, `self`, class attributes, instance attributes, inheritance, `super()`, method overriding, properties, and decorators.

**`libraries.csv`** -- 20 cards on `requests`, Pillow, NumPy, pytest, the emoji library, `sys.argv`, `sys.exit()`, `random`, and `statistics`.

---

### `scores/scores.json`

This file is created automatically the first time you run the app and finish a session. It is a flat dictionary where each key is a unique card identifier in the format `deckname_cardid` and each value holds a correct count and an incorrect count. You can delete it any time to reset all progress. Because it is formatted with two-space indentation it is easy to open and read if you want to check on a specific card or topic.

---

## Design Choices

**Why CSV for the deck files instead of JSON?**

CSV is easier to edit without any special knowledge. Anyone who wants to add their own flashcards can open the file in a spreadsheet or a plain text editor and add a row. JSON would have made the loading code a little simpler, but the goal was for the decks to be usable and expandable by anyone, not just someone comfortable with JSON syntax.

**Why store scores in a separate file from the decks?**

Keeping scores separate means the deck files stay read-only. If I update a deck or replace it with a better version, the scores are still intact. It also means a single `scores.json` file can hold score data across all six decks in one place, which keeps the file structure clean.

**Why make the core functions pure?**

`score_card`, `calculate_percentage`, `get_weak_cards`, and `format_question` all take inputs and return outputs with no side effects. I made that choice specifically because it makes them testable with pytest without needing to mock a file system or fake terminal input. `main()` handles all the I/O. The logic functions stay clean.

**Why `rich` over plain print statements?**

Two reasons. First, accessibility. High-contrast color and clear visual hierarchy in the terminal matter to me personally as someone who is legally blind and uses assistive technology. `rich` gives me that control without a lot of extra code. Second, the output is just more readable. A color-coded score table at the end of a session is more useful than a block of plain text, and `rich` makes that straightforward to build.