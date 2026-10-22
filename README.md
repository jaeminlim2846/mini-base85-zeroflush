# mini-base85-zeroflush

Encodes and decodes ZeroMQ Z85, a block-aligned variant of Ascii85 used by the ZeroMQ protocol.

## Usage

```python
from mini_base85_zeroflush import encode, decode

assert encode(b"\x00\x00\x00\x00") == "00000"
assert decode("%nSc0") == b"\xff\xff\xff\xff"
```

## Why

Z85 is the encoding ZeroMQ uses for CURVE keys, ZMTP metadata, and other protocol data where a compact ASCII representation of binary is required. There are existing Python implementations, but most live inside larger ZeroMQ bindings or pull in optional C extensions. This package exists to provide a single, pure-Python, standard-library-only encoder/decoder with no dependencies and no optional acceleration paths to maintain.

The trade-off: Z85 is strictly block-aligned — input bytes must be a multiple of 4 and input characters a multiple of 5. This implementation enforces that invariant with `ValueError` rather than silently padding, because silent padding would break round-tripping and diverge from the ZeroMQ wire format. If your data is not block-aligned you must pad or truncate it yourself before calling `encode`.

## Edge cases

- `encode` accepts `bytes`, `bytearray`, and `memoryview`. `decode` accepts `str` only; it rejects bytes so callers do not accidentally pass a previously-encoded binary buffer.
- Empty input round-trips to empty output.
- Bytes outside the 85-symbol Z85 alphabet (including high-bit bytes and whitespace) raise `ValueError` on decode. There is no lenient mode.
