"""Utils used in SDK."""
import re


def camelize(word: str, uppercase_first_letter: bool = True) -> str:
    """
    Convert under_scored string to CamelCase
    """
    if not word:
        return ""

    result = re.sub(r"(?:^|_)(.)", lambda m: m.group(1).upper(), word)
    if result and not uppercase_first_letter:
        result = result[0].lower() + result[1:]
    return result


def underscore(word: str) -> str:
    """
    Make an underscored, lowercase form from the expression in the string.
    """
    word = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", word)
    word = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", word)
    word = word.replace("-", "_")
    return word.lower()
