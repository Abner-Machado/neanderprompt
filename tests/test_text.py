"""The lexical helpers every offline heuristic leans on."""
from __future__ import annotations

from utils.text import jaccard, signature, token_set, tokens


def test_tokens_lowercase_and_drop_stopwords():
    assert tokens("Why do we use Docker for the API?") == ["docker", "api"]


def test_tokens_keep_accented_words_whole():
    # A Portuguese answer must not be split into letter fragments.
    assert tokens("Configuração não sobe") == ["configuração", "não", "sobe"]
    assert "n" not in tokens("não")


def test_jaccard_is_symmetric_and_bounded():
    a, b = "we use postgres for storage", "postgres is used as storage"
    assert jaccard(a, b) == jaccard(b, a)
    assert 0.0 < jaccard(a, b) < 1.0
    assert jaccard(a, a) == 1.0
    assert jaccard("", a) == 0.0
    assert jaccard("the of and", a) == 0.0  # only stopwords -> empty set


def test_jaccard_does_not_inflate_on_accent_fragments():
    # Before the unicode-aware tokenizer, "não" contributed "n" and "o", and the
    # stray "o" matched the other answer, giving 0.5 for two unrelated answers.
    assert jaccard("não usar docker", "o docker") == 0.25


def test_signature_is_stable_under_paraphrase():
    a = signature("Why is the deployment failing?")
    b = signature("why deployment failing")
    assert a == b
    assert a == "deployment|failing"


def test_signature_keeps_n_longest_tokens_sorted():
    assert signature("alpha beta gamma delta", n=2) == "alpha|delta"
    assert signature("", n=3) == ""


def test_token_set_dedupes():
    assert token_set("docker docker DOCKER") == {"docker"}
