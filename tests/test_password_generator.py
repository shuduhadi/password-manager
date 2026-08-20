import pytest
from password_generator import generate_password, calculate_strength, UPPERCASE, LOWERCASE, DIGITS, SYMBOLS


def test_generate_default_length():
    """Default call should produce a 16-character password."""
    password = generate_password()
    assert len(password) == 16


def test_generate_custom_length():
    """Length parameter should control output length."""
    password = generate_password(length=24)
    assert len(password) == 24


def test_generate_minimum_length():
    """Length of 1 should still work."""
    password = generate_password(length=1, use_upper=True, use_lower=False, use_digits=False, use_symbols=False)
    assert len(password) == 1


def test_generate_rejects_zero_length():
    """Length < 1 should raise ValueError."""
    with pytest.raises(ValueError):
        generate_password(length=0)


def test_generate_rejects_no_charset():
    """No character sets selected should raise ValueError."""
    with pytest.raises(ValueError):
        generate_password(use_upper=False, use_lower=False, use_digits=False, use_symbols=False)


def test_generate_only_uppercase():
    """With only uppercase selected, password should be all uppercase letters."""
    password = generate_password(length=20, use_upper=True, use_lower=False, use_digits=False, use_symbols=False)
    assert all(c in UPPERCASE for c in password)


def test_generate_only_digits():
    """With only digits selected, password should be all digits."""
    password = generate_password(length=20, use_upper=False, use_lower=False, use_digits=True, use_symbols=False)
    assert all(c in DIGITS for c in password)


def test_generate_includes_all_selected_types():
    """With all types selected and enough length, all types should appear at least once."""
    # Run a few times since it's random — with length 20 and all 4 sets required,
    # this should reliably include all 4 (guaranteed by generate_password's design).
    password = generate_password(length=20, use_upper=True, use_lower=True, use_digits=True, use_symbols=True)
    assert any(c in UPPERCASE for c in password)
    assert any(c in LOWERCASE for c in password)
    assert any(c in DIGITS for c in password)
    assert any(c in SYMBOLS for c in password)


def test_generate_is_random():
    """Two calls should (almost certainly) produce different passwords."""
    password1 = generate_password(length=16)
    password2 = generate_password(length=16)
    assert password1 != password2


def test_generate_short_length_falls_back_gracefully():
    """If length is shorter than the number of required charsets, should not crash."""
    # 4 types selected but length=2 — not enough room to guarantee one of each
    password = generate_password(length=2, use_upper=True, use_lower=True, use_digits=True, use_symbols=True)
    assert len(password) == 2


def test_strength_empty_password():
    """Empty password should score 0 / Very Weak."""
    score, label = calculate_strength("")
    assert score == 0
    assert label == "Very Weak"


def test_strength_short_simple_password():
    """Short, single-charset password should score low."""
    score, label = calculate_strength("abc")
    assert score <= 1


def test_strength_long_varied_password():
    """Long password with all character types should score highest."""
    score, label = calculate_strength("Xk9#mP2$vQ7!wZ4@")
    assert score == 4
    assert label == "Very Strong"


def test_strength_medium_password():
    """A reasonably long password with some variety should score moderately."""
    score, label = calculate_strength("password123")
    assert 1 <= score <= 3


def test_strength_increases_with_length():
    """Longer passwords with same variety should score >= shorter ones."""
    short_score, _ = calculate_strength("Ab1!")
    long_score, _ = calculate_strength("Ab1!Ab1!Ab1!Ab1!")
    assert long_score >= short_score


def test_strength_returns_valid_label():
    """Label should always be one of the five defined strength labels."""
    valid_labels = {"Very Weak", "Weak", "Moderate", "Strong", "Very Strong"}
    for pw in ["", "a", "abc123", "Abc123!@#", "Xk9#mP2$vQ7!wZ4@qR8&"]:
        _, label = calculate_strength(pw)
        assert label in valid_labels