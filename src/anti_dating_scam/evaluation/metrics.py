from collections.abc import Iterable


def exact_match_rate(expected: Iterable[str], actual: Iterable[str]) -> float:
    pairs = list(zip(expected, actual, strict=False))
    if not pairs:
        return 0.0
    matches = sum(1 for left, right in pairs if left == right)
    return matches / len(pairs)
