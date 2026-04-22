import pytest
import os
import json
import tempfile
import csv

from project import (
    load_deck,
    score_card,
    calculate_percentage,
    get_weak_cards,
    format_question,
    load_scores,
    save_scores,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def make_temp_deck(rows):
    """Write a list of row dicts to a temp CSV and return the filepath."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="", encoding="utf-8"
    )
    fieldnames = ["id", "topic", "question", "answer"]
    writer = csv.DictWriter(tmp, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    tmp.close()
    return tmp.name


# ─────────────────────────────────────────────
# load_deck
# ─────────────────────────────────────────────

def test_load_deck_returns_list():
    filepath = make_temp_deck([
        {"id": "1", "topic": "File I/O", "question": "What does 'with' do?", "answer": "Auto-closes the file."}
    ])
    result = load_deck(filepath)
    assert isinstance(result, list)
    os.unlink(filepath)


def test_load_deck_has_required_keys():
    filepath = make_temp_deck([
        {"id": "1", "topic": "File I/O", "question": "What does 'with' do?", "answer": "Auto-closes the file."}
    ])
    result = load_deck(filepath)
    assert "question" in result[0]
    assert "answer" in result[0]
    assert "topic" in result[0]
    os.unlink(filepath)


def test_load_deck_correct_card_count():
    rows = [
        {"id": str(i), "topic": "Test", "question": f"Q{i}", "answer": f"A{i}"}
        for i in range(1, 6)
    ]
    filepath = make_temp_deck(rows)
    result = load_deck(filepath)
    assert len(result) == 5
    os.unlink(filepath)


def test_load_deck_invalid_path():
    with pytest.raises(FileNotFoundError):
        load_deck("decks/this_does_not_exist.csv")


def test_load_deck_empty_file_raises():
    filepath = make_temp_deck([])
    with pytest.raises(ValueError):
        load_deck(filepath)
    os.unlink(filepath)


# ─────────────────────────────────────────────
# score_card
# ─────────────────────────────────────────────

def test_score_card_correct_new_key():
    scores = {}
    result = score_card(scores, "file_io_1", True)
    assert result["file_io_1"]["correct"] == 1
    assert result["file_io_1"]["incorrect"] == 0


def test_score_card_incorrect_new_key():
    scores = {}
    result = score_card(scores, "file_io_1", False)
    assert result["file_io_1"]["correct"] == 0
    assert result["file_io_1"]["incorrect"] == 1


def test_score_card_accumulates_existing():
    scores = {"file_io_1": {"correct": 2, "incorrect": 1}}
    result = score_card(scores, "file_io_1", True)
    assert result["file_io_1"]["correct"] == 3
    assert result["file_io_1"]["incorrect"] == 1


def test_score_card_returns_dict():
    result = score_card({}, "regex_3", True)
    assert isinstance(result, dict)


def test_score_card_multiple_cards():
    scores = {}
    scores = score_card(scores, "deck_1", True)
    scores = score_card(scores, "deck_2", False)
    assert "deck_1" in scores
    assert "deck_2" in scores
    assert scores["deck_1"]["correct"] == 1
    assert scores["deck_2"]["incorrect"] == 1


# ─────────────────────────────────────────────
# calculate_percentage
# ─────────────────────────────────────────────

def test_calculate_percentage_normal():
    assert calculate_percentage(3, 1) == 75.0


def test_calculate_percentage_all_correct():
    assert calculate_percentage(10, 0) == 100.0


def test_calculate_percentage_all_incorrect():
    assert calculate_percentage(0, 5) == 0.0


def test_calculate_percentage_zero_attempts():
    assert calculate_percentage(0, 0) == 0.0


def test_calculate_percentage_returns_float():
    result = calculate_percentage(1, 3)
    assert isinstance(result, float)


# ─────────────────────────────────────────────
# get_weak_cards
# ─────────────────────────────────────────────

def test_get_weak_cards_unseen_comes_first():
    cards = [{"id": "1"}, {"id": "2"}]
    # card 1 has a perfect score, card 2 is unseen
    scores = {"deck_1": {"correct": 5, "incorrect": 0}}
    result = get_weak_cards(cards, scores, "deck")
    assert result[0]["id"] == "2"


def test_get_weak_cards_weakest_before_strongest():
    cards = [{"id": "1"}, {"id": "2"}]
    scores = {
        "deck_1": {"correct": 4, "incorrect": 1},   # 80%
        "deck_2": {"correct": 1, "incorrect": 4},   # 20%
    }
    result = get_weak_cards(cards, scores, "deck")
    assert result[0]["id"] == "2"


def test_get_weak_cards_returns_all_cards():
    cards = [{"id": str(i)} for i in range(1, 6)]
    result = get_weak_cards(cards, {}, "deck")
    assert len(result) == 5


def test_get_weak_cards_all_unseen_preserves_count():
    cards = [{"id": "1"}, {"id": "2"}, {"id": "3"}]
    result = get_weak_cards(cards, {}, "anydeck")
    assert len(result) == 3


# ─────────────────────────────────────────────
# format_question
# ─────────────────────────────────────────────

def test_format_question_contains_question_text():
    card = {"id": "1", "topic": "Regex", "question": "What does re.search return?", "answer": "A match object or None."}
    result = format_question(card, 1, 10)
    assert "What does re.search return?" in result


def test_format_question_contains_index():
    card = {"id": "1", "topic": "OOP", "question": "What is a class?", "answer": "A blueprint."}
    result = format_question(card, 3, 10)
    assert "3/10" in result


def test_format_question_contains_topic():
    card = {"id": "1", "topic": "Exceptions", "question": "What is try/except?", "answer": "Error handling."}
    result = format_question(card, 1, 5)
    assert "Exceptions" in result


# ─────────────────────────────────────────────
# load_scores / save_scores (persistence)
# ─────────────────────────────────────────────

def test_load_scores_returns_empty_dict_if_no_file():
    result = load_scores("/tmp/definitely_not_a_real_scores_file.json")
    assert result == {}


def test_save_and_load_scores_roundtrip():
    scores = {"file_io_1": {"correct": 3, "incorrect": 1}}
    tmpdir = tempfile.mkdtemp()
    filepath = os.path.join(tmpdir, "scores.json")
    save_scores(scores, filepath)
    loaded = load_scores(filepath)
    assert loaded == scores


def test_save_scores_creates_file():
    tmpdir = tempfile.mkdtemp()
    filepath = os.path.join(tmpdir, "scores.json")
    save_scores({"test_1": {"correct": 1, "incorrect": 0}}, filepath)
    assert os.path.exists(filepath)