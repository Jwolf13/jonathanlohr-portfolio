# tests/test_coinflip.py
from src.coinflip import flip_probability, compute_probability

def is_heads(outcome):
    return outcome == "Heads"

def test_flip_probability():
    sample_space = {"Heads", "Tails"}
    assert flip_probability(sample_space) == 0.5

def test_heads_probability():
    sample_space = {"Heads", "Tails"}
    assert compute_probability(is_heads, sample_space) == 0.5