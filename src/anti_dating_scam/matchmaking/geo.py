"""Coarse location buckets for nearby discovery.

Privacy rule (docs/12, threat model "location stalking"): the geohash is derived
**client-side** and only the coarse bucket string is ever sent to the server. Raw
coordinates must never appear in a request payload or server log.

Default precision 4 is a cell of roughly 39 km x 20 km — metro-area granularity,
deliberately too coarse to locate a person. Finer precision is an explicit user
opt-in, never a default.

Known limitation (accepted for the P0 prototype): plain prefix matching misses
neighbors across bucket borders. P1 may add neighbor-cell search; do not "fix"
this by increasing precision.
"""

from __future__ import annotations

DEFAULT_PRECISION = 4
_BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"


def encode_geohash(latitude: float, longitude: float, precision: int = DEFAULT_PRECISION) -> str:
    """Standard geohash encoding (client-side only; see module docstring)."""
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("latitude must be within [-90, 90]")
    if not -180.0 <= longitude <= 180.0:
        raise ValueError("longitude must be within [-180, 180]")
    if precision < 1:
        raise ValueError("precision must be >= 1")

    lat_lo, lat_hi = -90.0, 90.0
    lon_lo, lon_hi = -180.0, 180.0
    bits: list[int] = []
    use_longitude = True
    while len(bits) < precision * 5:
        if use_longitude:
            mid = (lon_lo + lon_hi) / 2
            if longitude >= mid:
                bits.append(1)
                lon_lo = mid
            else:
                bits.append(0)
                lon_hi = mid
        else:
            mid = (lat_lo + lat_hi) / 2
            if latitude >= mid:
                bits.append(1)
                lat_lo = mid
            else:
                bits.append(0)
                lat_hi = mid
        use_longitude = not use_longitude

    chars: list[str] = []
    for index in range(0, len(bits), 5):
        value = 0
        for bit in bits[index : index + 5]:
            value = (value << 1) | bit
        chars.append(_BASE32[value])
    return "".join(chars)


def is_valid_geohash(value: str) -> bool:
    return isinstance(value, str) and bool(value) and all(char in _BASE32 for char in value)


def same_bucket(geohash_a: str, geohash_b: str, precision: int = DEFAULT_PRECISION) -> bool:
    """Whether two geohashes fall in the same coarse bucket (prefix comparison)."""
    if precision < 1:
        raise ValueError("precision must be >= 1")
    prefix_a = geohash_a[:precision]
    prefix_b = geohash_b[:precision]
    if len(prefix_a) < precision or len(prefix_b) < precision:
        return False
    return prefix_a == prefix_b
