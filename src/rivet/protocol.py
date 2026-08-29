from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass


MAGIC = b"RVT1"
_HEADER = struct.Struct(">4sBBB IQI")
_CRC = struct.Struct(">I")


@dataclass(frozen=True)
class RivetFrame:
    device: str
    channel: str
    sequence: int
    timestamp_ns: int
    payload: bytes
    version: int = 1


class FrameCodec:
    """Small binary Rivet Link frame codec with length checks and CRC32."""

    def encode(self, frame: RivetFrame) -> bytes:
        device = frame.device.encode("utf-8")
        channel = frame.channel.encode("utf-8")
        if len(device) > 255 or len(channel) > 255:
            raise ValueError("device and channel names must be <=255 bytes")
        if frame.sequence < 0 or frame.timestamp_ns < 0:
            raise ValueError("sequence and timestamp must be non-negative")
        header = _HEADER.pack(MAGIC, frame.version, len(device), len(channel), frame.sequence, frame.timestamp_ns, len(frame.payload))
        body = header + device + channel + frame.payload
        return body + _CRC.pack(zlib.crc32(body) & 0xFFFFFFFF)

    def decode(self, packet: bytes) -> RivetFrame:
        if len(packet) < _HEADER.size + _CRC.size:
            raise ValueError("Rivet frame is truncated")
        magic, version, device_len, channel_len, sequence, timestamp_ns, payload_len = _HEADER.unpack_from(packet)
        if magic != MAGIC:
            raise ValueError("invalid Rivet frame magic")
        body_len = _HEADER.size + device_len + channel_len + payload_len
        if len(packet) != body_len + _CRC.size:
            raise ValueError("Rivet frame length does not match payload")
        body = packet[:body_len]
        expected = _CRC.unpack_from(packet, body_len)[0]
        if zlib.crc32(body) & 0xFFFFFFFF != expected:
            raise ValueError("Rivet frame CRC mismatch")
        cursor = _HEADER.size
        device = packet[cursor:cursor + device_len].decode("utf-8")
        cursor += device_len
        channel = packet[cursor:cursor + channel_len].decode("utf-8")
        cursor += channel_len
        return RivetFrame(device, channel, sequence, timestamp_ns, packet[cursor:cursor + payload_len], version)
