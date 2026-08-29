import pytest

from rivet.protocol import FrameCodec, RivetFrame


def test_frame_round_trip():
    frame = RivetFrame("pico-1", "motion", 12, 99, b"velocity=0.4")
    assert FrameCodec().decode(FrameCodec().encode(frame)) == frame


def test_frame_crc_rejects_corruption():
    encoded = bytearray(FrameCodec().encode(RivetFrame("pico", "io", 1, 2, b"x")))
    encoded[-1] ^= 0xFF
    with pytest.raises(ValueError, match="CRC"):
        FrameCodec().decode(bytes(encoded))
