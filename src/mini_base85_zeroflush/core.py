"""Z85 (ZeroMQ Base85) encoding and decoding.

Z85 is a variant of Ascii85 defined by ZeroMQ (ZMTP / RFC 32).
Unlike Adobe Ascii85, Z85 operates strictly on 4-byte blocks
and therefore requires the input byte length to be a multiple of
4 for encoding and the input character count to be a multiple of
5 for decoding. There is no special handling for trailing zeros,
which is why this implementation is called "zeroflush": every
block is emitted verbatim, with no shortcut for all-zero frames.
"""

from __future__ import annotations

# Encoder alphabet defined by the Z85 specification (RFC 32).
# It is intentionally NOT ASCII-ordered: digits 0-9 come after
# the uppercase letters, which differs from both base64 and
# Adobe Ascii85. Reordering would break interop with every
# other Z85 implementation.
ALPHABET: bytes = (
    b"0123456789"
    b"abcdefghijklmnopqrstuvwxyz"
    b"ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    b".-:+=^!/*?&<>()[]{}@%$#"
)

# Precomputed reverse lookup table mapping each Z85 byte value
# to its index in ALPHABET. Using a bytes object indexed by the
# raw input byte makes decode() branch-free and allocation-light.
# Values 0..127 map to the Z85 digit or 0xFF (invalid); bytes
# with the high bit set are always invalid.
_REVERSE: bytes = bytes(
    ALPHABET.index(i) if i in ALPHABET else 0xFF for i in range(128)
)

ENCODED_CHARS: int = 5  # Z85 expands 4 bytes to 5 chars.
DECODED_BYTES: int = 4  # Z85 shrinks 5 chars to 4 bytes.


def encode(data: bytes) -> str:
    """Encode *data* to a Z85 string.

    The length of *data* MUST be a multiple of 4. This is a
    hard requirement of the Z85 format: a partial block has
    no defined representation. We raise ``ValueError`` rather
    than silently padding because silent padding would make
    round-tripping impossible and diverge from every other
    Z85 codec.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("encode() expects bytes-like input")
    data = bytes(data)
    if len(data) % DECODED_BYTES != 0:
        raise ValueError(
            f"input length {len(data)} is not a multiple of {DECODED_BYTES}"
        )
    out = bytearray(len(data) // DECODED_BYTES * ENCODED_CHARS)
    out_pos = 0
    for i in range(0, len(data), DECODED_BYTES):
        chunk = data[i] << 24 | data[i + 1] << 16 | data[i + 2] << 8 | data[i + 3]
        for j in range(ENCODED_CHARS - 1, -1, -1):
            out[out_pos + j] = ALPHABET[chunk % 85]
            chunk //= 85
        out_pos += ENCODED_CHARS
    return out.decode("ascii")


def decode(text: str) -> bytes:
    """Decode a Z85 *text* string back to bytes.

    The length of *text* MUST be a multiple of 5, matching the
    Z85 block size. Characters outside the 85-symbol alphabet
    are rejected with ``ValueError``.
    """
    if not isinstance(text, str):
        raise TypeError("decode() expects str input")
    if len(text) % ENCODED_CHARS != 0:
        raise ValueError(
            f"input length {len(text)} is not a multiple of {ENCODED_CHARS}"
        )
    raw = text.encode("ascii")
    out = bytearray(len(raw) // ENCODED_CHARS * DECODED_BYTES)
    out_pos = 0
    for i in range(0, len(raw), ENCODED_CHARS):
        value = 0
        for j in range(ENCODED_CHARS):
            b = raw[i + j]
            if b & 0x80:
                raise ValueError(
                    f"non-ASCII byte 0x{b:02x} at position {i + j}"
                )
            digit = _REVERSE[b]
            if digit == 0xFF:
                raise ValueError(
                    f"invalid Z85 character {chr(b)!r} at position {i + j}"
                )
            value = value * 85 + digit
        out[out_pos] = (value >> 24) & 0xFF
        out[out_pos + 1] = (value >> 16) & 0xFF
        out[out_pos + 2] = (value >> 8) & 0xFF
        out[out_pos + 3] = value & 0xFF
        out_pos += DECODED_BYTES
    return bytes(out)
