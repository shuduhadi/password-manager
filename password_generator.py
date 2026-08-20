import secrets
import string


UPPERCASE = string.ascii_uppercase
LOWERCASE = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"


def generate_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """Generate a random password using the cryptographically secure `secrets` module.

    Args:
        length: Total password length (recommend 8-64).
        use_upper: Include A-Z.
        use_lower: Include a-z.
        use_digits: Include 0-9.
        use_symbols: Include punctuation/symbols.

    Returns:
        A randomly generated password string.

    Raises:
        ValueError: If no character sets are selected, or length < 1.
    """
    if length < 1:
        raise ValueError("Password length must be at least 1")

    charset = ""
    required_chars = []

    if use_upper:
        charset += UPPERCASE
        required_chars.append(secrets.choice(UPPERCASE))
    if use_lower:
        charset += LOWERCASE
        required_chars.append(secrets.choice(LOWERCASE))
    if use_digits:
        charset += DIGITS
        required_chars.append(secrets.choice(DIGITS))
    if use_symbols:
        charset += SYMBOLS
        required_chars.append(secrets.choice(SYMBOLS))

    if not charset:
        raise ValueError("At least one character set must be selected")

    if length < len(required_chars):
        # Not enough room to guarantee one of each selected type;
        # just fill randomly from the combined charset instead.
        return "".join(secrets.choice(charset) for _ in range(length))

    # Guarantee at least one character from each selected set,
    # then fill the rest randomly, then shuffle so the guaranteed
    # characters aren't always in the same position.
    remaining_length = length - len(required_chars)
    password_chars = required_chars + [
        secrets.choice(charset) for _ in range(remaining_length)
    ]

    # Fisher-Yates shuffle using secrets for cryptographic randomness
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars)


def calculate_strength(password: str) -> tuple[int, str]:
    """Score a password's strength on a 0-4 scale.

    Args:
        password: The password to score.

    Returns:
        Tuple of (score 0-4, label). Labels: Very Weak, Weak, Moderate, Strong, Very Strong.
    """
    if not password:
        return 0, "Very Weak"

    score = 0

    # Length contributes most heavily
    length = len(password)
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1
    if length >= 16:
        score += 1

    # Character variety
    variety = sum([
        any(c.isupper() for c in password),
        any(c.islower() for c in password),
        any(c.isdigit() for c in password),
        any(c in SYMBOLS for c in password),
    ])
    if variety >= 3:
        score += 1

    score = min(score, 4)

    labels = ["Very Weak", "Weak", "Moderate", "Strong", "Very Strong"]
    return score, labels[score]