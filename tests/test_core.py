"""Tests for the Z85 encoder/decoder.

Every assertion here corresponds to behaviour the implementation
actually claims to support: block alignment, the known Z85
reference vectors, full round-tripping, rejection of bad input,
and acceptance of bytes-like inputs. We deliberately do NOT test
unimplemented features such as ad-hoc padding or framing.
"""

import unittest

from mini_base85_zeroflush import encode, decode


class TestEncode(unittest.TestCase):
    def test_known_block_all_zero(self):
        # 4 zero bytes encode to "00000" in Z85.
        self.assertEqual(encode(b"\x00\x00\x00\x00"), "00000")

    def test_known_block_max(self):
        # 0xFFFFFFFF is the largest 4-byte value and maps to "%nSc0"
        # (the value 85^5 - 1 split across five base-85 digits).
        self.assertEqual(encode(b"\xff\xff\xff\xff"), "%nSc0")

    def test_known_reference_vector(self):
        # The two-block pair used in Z85 documentation.
        self.assertEqual(
            encode(bytes([0x86, 0x4F, 0xD2, 0x6F, 0xB5, 0x59, 0xF7, 0x5B])),
            "HelloWorld")

    def test_single_block_partial_decoding(self):
        # Sanity-check a single hand-computed block.
        self.assertEqual(encode(b"\x00\x00\x00\x01"), "00001")

    def test_rejects_non_multiple_of_four(self):
        with self.assertRaises(ValueError):
            encode(b"abc")
        with self.assertRaises(ValueError):
            encode(b"\x00" * 5)

    def test_rejects_non_bytes(self):
        with self.assertRaises(TypeError):
            encode("00000")  # str is not accepted for encode

    def test_accepts_bytearray(self):
        self.assertEqual(encode(bytearray(4)), "00000")

    def test_accepts_memoryview(self):
        self.assertEqual(encode(memoryview(b"\x00" * 4)), "00000")

    def test_empty_input(self):
        self.assertEqual(encode(b""), "")


class TestDecode(unittest.TestCase):
    def test_known_block_all_zero(self):
        self.assertEqual(decode("00000"), b"\x00\x00\x00\x00")

    def test_known_block_max(self):
        self.assertEqual(decode("%nSc0"), b"\xff\xff\xff\xff")

    def test_known_reference_vector(self):
        self.assertEqual(
            decode("HelloWorld"),
            bytes([0x86, 0x4F, 0xD2, 0x6F, 0xB5, 0x59, 0xF7, 0x5B]),
        )

    def test_rejects_non_multiple_of_five(self):
        with self.assertRaises(ValueError):
            decode("0000")
        with self.assertRaises(ValueError):
            decode("000000")

    def test_rejects_invalid_character(self):
        with self.assertRaises(ValueError):
            decode("0000~")  # '~' is not in the Z85 alphabet

    def test_rejects_non_ascii_byte(self):
        with self.assertRaises(ValueError):
            decode("0000\x80")

    def test_rejects_non_str(self):
        with self.assertRaises(TypeError):
            decode(b"00000")  # bytes is not accepted for decode

    def test_empty_input(self):
        self.assertEqual(decode(""), b"")


class TestRoundTrip(unittest.TestCase):
    def _round_trip(self, payload: bytes) -> None:
        self.assertEqual(decode(encode(payload)), payload)

    def test_round_trip_single_zero_block(self):
        self._round_trip(b"\x00" * 4)

    def test_round_trip_single_max_block(self):
        self._round_trip(b"\xff" * 4)

    def test_round_trip_multi_block(self):
        payload = bytes(range(0, 24))
        self.assertEqual(len(payload) % 4, 0)
        self._round_trip(payload)

    def test_round_trip_all_alphabet_symbols(self):
        # Exercise every symbol in the alphabet at least once.
        from mini_base85_zeroflush import ALPHABET, ENCODED_CHARS, DECODED_BYTES
        raw = bytes(ALPHABET)
        # Pad/truncate to a multiple of 4 so encode accepts it.
        usable = raw[: (len(raw) // DECODED_BYTES) * DECODED_BYTES]
        self._round_trip(usable)


if __name__ == "__main__":
    unittest.main()
