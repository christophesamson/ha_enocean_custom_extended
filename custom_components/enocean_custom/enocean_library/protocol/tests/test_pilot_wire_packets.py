# -*- encoding: utf-8 -*-
"""Tests for D2-01-0C Pilot Wire VLD packet structure.

These tests verify the EnOcean D2-01-0C (Pilot Wire Heating Module) packet
structure without requiring Home Assistant dependencies.

Run with: pytest custom_components/enocean_custom/enocean_library/protocol/tests/test_pilot_wire_packets.py -v
"""
from __future__ import print_function, unicode_literals, division, absolute_import

# Pilot Wire mode values (from D2-01-0C EEP specification)
PILOT_WIRE_MODE_OFF = 0
PILOT_WIRE_MODE_COMFORT = 1
PILOT_WIRE_MODE_ECO = 2
PILOT_WIRE_MODE_FROST_PROTECTION = 3
PILOT_WIRE_MODE_COMFORT_MINUS_1 = 4
PILOT_WIRE_MODE_COMFORT_MINUS_2 = 5

# VLD packet constants
RORG_VLD = 0xD2
RORG_UTE = 0xD4
CMD_SET_PILOT_WIRE_MODE = 0x08
CMD_PILOT_WIRE_MODE_RESPONSE = 0x0A

# EEP D2-01-0C
EEP_RORG = 0xD2
EEP_FUNC = 0x01
EEP_TYPE = 0x0C


def build_set_pilot_wire_mode_packet(sender_id: list, mode: int, channel: int = 0) -> list:
    """Build a Set Pilot Wire Mode packet (CMD 0x08).

    Args:
        sender_id: 4-byte sender ID [byte0, byte1, byte2, byte3]
        mode: Pilot wire mode value (0-5)
        channel: I/O channel (default 0)

    Returns:
        List of bytes representing the packet data
    """
    packet = [RORG_VLD]  # RORG = VLD
    packet.append((CMD_SET_PILOT_WIRE_MODE << 4) | (channel & 0x0F))  # CMD + channel
    packet.append(mode & 0x0F)  # Mode value
    packet.extend(sender_id)
    packet.append(0x00)  # Status
    return packet


def parse_pilot_wire_response(data: list) -> dict:
    """Parse a Pilot Wire Mode Response packet (CMD 0x0A).

    Args:
        data: Raw packet data bytes

    Returns:
        Dictionary with parsed values: rorg, cmd, channel, mode, sender_id
    """
    if len(data) < 3:
        raise ValueError("Packet too short")

    rorg = data[0]
    cmd = (data[1] >> 4) & 0x0F
    channel = data[1] & 0x0F
    mode = data[2] & 0x0F

    sender_id = data[3:7] if len(data) >= 7 else []

    return {
        "rorg": rorg,
        "cmd": cmd,
        "channel": channel,
        "mode": mode,
        "sender_id": sender_id,
    }


def build_ute_teach_in_packet(sender_id: list, manufacturer_id: int = 0x0046) -> list:
    """Build a UTE teach-in packet for D2-01-0C.

    Args:
        sender_id: 4-byte sender ID
        manufacturer_id: 11-bit manufacturer ID (default 0x0046 = NodOn)

    Returns:
        List of bytes representing the UTE packet
    """
    packet = [RORG_UTE]  # UTE RORG
    packet.append(0x20)  # Teach-in request, bidirectional
    packet.append(EEP_RORG)  # EEP RORG
    packet.append(EEP_FUNC)  # EEP FUNC
    packet.append(EEP_TYPE)  # EEP TYPE
    packet.append((manufacturer_id >> 8) & 0xFF)  # Manufacturer ID high byte
    packet.append(manufacturer_id & 0xFF)  # Manufacturer ID low byte
    packet.extend(sender_id)
    packet.append(0x00)  # Status
    return packet


class TestPilotWireModeConstants:
    """Test pilot wire mode constant values."""

    def test_mode_off(self):
        """Test OFF mode value."""
        assert PILOT_WIRE_MODE_OFF == 0

    def test_mode_comfort(self):
        """Test COMFORT mode value."""
        assert PILOT_WIRE_MODE_COMFORT == 1

    def test_mode_eco(self):
        """Test ECO mode value."""
        assert PILOT_WIRE_MODE_ECO == 2

    def test_mode_frost_protection(self):
        """Test FROST_PROTECTION mode value."""
        assert PILOT_WIRE_MODE_FROST_PROTECTION == 3

    def test_mode_comfort_minus_1(self):
        """Test COMFORT_MINUS_1 mode value."""
        assert PILOT_WIRE_MODE_COMFORT_MINUS_1 == 4

    def test_mode_comfort_minus_2(self):
        """Test COMFORT_MINUS_2 mode value."""
        assert PILOT_WIRE_MODE_COMFORT_MINUS_2 == 5

    def test_all_modes_unique(self):
        """Test all mode values are unique."""
        modes = [
            PILOT_WIRE_MODE_OFF,
            PILOT_WIRE_MODE_COMFORT,
            PILOT_WIRE_MODE_ECO,
            PILOT_WIRE_MODE_FROST_PROTECTION,
            PILOT_WIRE_MODE_COMFORT_MINUS_1,
            PILOT_WIRE_MODE_COMFORT_MINUS_2,
        ]
        assert len(modes) == len(set(modes))

    def test_modes_in_valid_range(self):
        """Test all mode values fit in 4 bits (0-15)."""
        modes = [
            PILOT_WIRE_MODE_OFF,
            PILOT_WIRE_MODE_COMFORT,
            PILOT_WIRE_MODE_ECO,
            PILOT_WIRE_MODE_FROST_PROTECTION,
            PILOT_WIRE_MODE_COMFORT_MINUS_1,
            PILOT_WIRE_MODE_COMFORT_MINUS_2,
        ]
        for mode in modes:
            assert 0 <= mode <= 15


class TestVldPacketConstants:
    """Test VLD packet constant values."""

    def test_rorg_vld(self):
        """Test VLD RORG value."""
        assert RORG_VLD == 0xD2

    def test_rorg_ute(self):
        """Test UTE RORG value."""
        assert RORG_UTE == 0xD4

    def test_cmd_set_pilot_wire_mode(self):
        """Test Set Pilot Wire Mode command value."""
        assert CMD_SET_PILOT_WIRE_MODE == 0x08

    def test_cmd_pilot_wire_mode_response(self):
        """Test Pilot Wire Mode Response command value."""
        assert CMD_PILOT_WIRE_MODE_RESPONSE == 0x0A

    def test_eep_values(self):
        """Test EEP D2-01-0C values."""
        assert EEP_RORG == 0xD2
        assert EEP_FUNC == 0x01
        assert EEP_TYPE == 0x0C


class TestBuildSetPilotWireModePacket:
    """Test build_set_pilot_wire_mode_packet function."""

    def test_comfort_mode_packet(self):
        """Test building a comfort mode packet."""
        sender_id = [0xFF, 0xD9, 0x04, 0x81]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT)

        expected = [0xD2, 0x80, 0x01, 0xFF, 0xD9, 0x04, 0x81, 0x00]
        assert packet == expected

    def test_off_mode_packet(self):
        """Test building an OFF mode packet."""
        sender_id = [0xAA, 0xBB, 0xCC, 0xDD]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_OFF)

        assert packet[0] == RORG_VLD
        assert packet[1] == 0x80  # CMD 0x08, channel 0
        assert packet[2] == 0x00  # Mode OFF
        assert packet[3:7] == sender_id

    def test_eco_mode_packet(self):
        """Test building an ECO mode packet."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_ECO)

        assert packet[2] == 0x02  # Mode ECO

    def test_frost_protection_mode_packet(self):
        """Test building a frost protection mode packet."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_FROST_PROTECTION)

        assert packet[2] == 0x03  # Mode frost protection

    def test_comfort_minus_1_mode_packet(self):
        """Test building a comfort -1 mode packet."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT_MINUS_1)

        assert packet[2] == 0x04  # Mode comfort -1

    def test_comfort_minus_2_mode_packet(self):
        """Test building a comfort -2 mode packet."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT_MINUS_2)

        assert packet[2] == 0x05  # Mode comfort -2

    def test_packet_length(self):
        """Test packet has correct length."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT)

        assert len(packet) == 8  # RORG + CMD/ch + mode + 4 sender + status

    def test_different_channel(self):
        """Test building packet with different channel."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT, channel=1)

        assert packet[1] == 0x81  # CMD 0x08, channel 1

    def test_cmd_byte_encoding(self):
        """Test CMD byte is correctly encoded."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT)

        cmd_byte = packet[1]
        cmd = (cmd_byte >> 4) & 0x0F
        channel = cmd_byte & 0x0F

        assert cmd == CMD_SET_PILOT_WIRE_MODE
        assert channel == 0


class TestParsePilotWireResponse:
    """Test parse_pilot_wire_response function."""

    def test_parse_comfort_response(self):
        """Test parsing a comfort mode response."""
        data = [0xD2, 0xA0, 0x01, 0xFF, 0xD9, 0x04, 0x81, 0x00]
        result = parse_pilot_wire_response(data)

        assert result["rorg"] == RORG_VLD
        assert result["cmd"] == CMD_PILOT_WIRE_MODE_RESPONSE
        assert result["channel"] == 0
        assert result["mode"] == PILOT_WIRE_MODE_COMFORT
        assert result["sender_id"] == [0xFF, 0xD9, 0x04, 0x81]

    def test_parse_off_response(self):
        """Test parsing an OFF mode response."""
        data = [0xD2, 0xA0, 0x00, 0xAA, 0xBB, 0xCC, 0xDD, 0x00]
        result = parse_pilot_wire_response(data)

        assert result["mode"] == PILOT_WIRE_MODE_OFF

    def test_parse_eco_response(self):
        """Test parsing an ECO mode response."""
        data = [0xD2, 0xA0, 0x02, 0x01, 0x02, 0x03, 0x04, 0x00]
        result = parse_pilot_wire_response(data)

        assert result["mode"] == PILOT_WIRE_MODE_ECO

    def test_parse_frost_protection_response(self):
        """Test parsing a frost protection mode response."""
        data = [0xD2, 0xA0, 0x03, 0x01, 0x02, 0x03, 0x04, 0x00]
        result = parse_pilot_wire_response(data)

        assert result["mode"] == PILOT_WIRE_MODE_FROST_PROTECTION

    def test_parse_response_with_channel(self):
        """Test parsing response with non-zero channel."""
        data = [0xD2, 0xA1, 0x01, 0x01, 0x02, 0x03, 0x04, 0x00]  # Channel 1
        result = parse_pilot_wire_response(data)

        assert result["channel"] == 1

    def test_parse_short_packet(self):
        """Test parsing short packet raises error."""
        data = [0xD2, 0xA0]
        try:
            parse_pilot_wire_response(data)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_mode_masking(self):
        """Test that only lower nibble is used for mode."""
        # Upper nibble should be ignored
        data = [0xD2, 0xA0, 0xF1, 0x01, 0x02, 0x03, 0x04, 0x00]
        result = parse_pilot_wire_response(data)

        assert result["mode"] == PILOT_WIRE_MODE_COMFORT  # 0xF1 & 0x0F = 0x01


class TestBuildUteTeachInPacket:
    """Test build_ute_teach_in_packet function."""

    def test_basic_teach_in_packet(self):
        """Test building a basic UTE teach-in packet."""
        sender_id = [0xFF, 0xD9, 0x04, 0x81]
        packet = build_ute_teach_in_packet(sender_id)

        expected = [0xD4, 0x20, 0xD2, 0x01, 0x0C, 0x00, 0x46, 0xFF, 0xD9, 0x04, 0x81, 0x00]
        assert packet == expected

    def test_teach_in_packet_length(self):
        """Test teach-in packet has correct length."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_ute_teach_in_packet(sender_id)

        assert len(packet) == 12

    def test_teach_in_rorg(self):
        """Test teach-in packet has UTE RORG."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_ute_teach_in_packet(sender_id)

        assert packet[0] == RORG_UTE

    def test_teach_in_bidirectional_flag(self):
        """Test teach-in packet has bidirectional flag."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_ute_teach_in_packet(sender_id)

        assert packet[1] == 0x20  # Bidirectional teach-in request

    def test_teach_in_eep(self):
        """Test teach-in packet has correct EEP."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_ute_teach_in_packet(sender_id)

        assert packet[2] == EEP_RORG  # D2
        assert packet[3] == EEP_FUNC  # 01
        assert packet[4] == EEP_TYPE  # 0C

    def test_teach_in_manufacturer_id_nodon(self):
        """Test teach-in packet has NodOn manufacturer ID by default."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_ute_teach_in_packet(sender_id)

        manufacturer_id = (packet[5] << 8) | packet[6]
        assert manufacturer_id == 0x0046  # NodOn

    def test_teach_in_custom_manufacturer_id(self):
        """Test teach-in packet with custom manufacturer ID."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        packet = build_ute_teach_in_packet(sender_id, manufacturer_id=0x07FF)

        manufacturer_id = (packet[5] << 8) | packet[6]
        assert manufacturer_id == 0x07FF  # Generic/universal

    def test_teach_in_sender_id(self):
        """Test teach-in packet contains sender ID."""
        sender_id = [0xAA, 0xBB, 0xCC, 0xDD]
        packet = build_ute_teach_in_packet(sender_id)

        assert packet[7:11] == sender_id


class TestPacketRoundTrip:
    """Test building and parsing packets together."""

    def test_all_modes_round_trip(self):
        """Test that all modes can be built and parsed correctly."""
        sender_id = [0x12, 0x34, 0x56, 0x78]

        modes = [
            PILOT_WIRE_MODE_OFF,
            PILOT_WIRE_MODE_COMFORT,
            PILOT_WIRE_MODE_ECO,
            PILOT_WIRE_MODE_FROST_PROTECTION,
            PILOT_WIRE_MODE_COMFORT_MINUS_1,
            PILOT_WIRE_MODE_COMFORT_MINUS_2,
        ]

        for mode in modes:
            # Build packet
            packet = build_set_pilot_wire_mode_packet(sender_id, mode)

            # Simulate response (change CMD from 0x08 to 0x0A)
            response = packet.copy()
            response[1] = (CMD_PILOT_WIRE_MODE_RESPONSE << 4) | (packet[1] & 0x0F)

            # Parse response
            result = parse_pilot_wire_response(response)

            assert result["mode"] == mode
            assert result["sender_id"] == sender_id


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_sender_id(self):
        """Test with minimum sender ID values."""
        sender_id = [0x00, 0x00, 0x00, 0x00]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT)

        assert packet[3:7] == sender_id

    def test_maximum_sender_id(self):
        """Test with maximum sender ID values."""
        sender_id = [0xFF, 0xFF, 0xFF, 0xFF]
        packet = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT)

        assert packet[3:7] == sender_id

    def test_channel_boundary(self):
        """Test channel boundary values."""
        sender_id = [0x01, 0x02, 0x03, 0x04]

        # Channel 0
        packet0 = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT, channel=0)
        assert (packet0[1] & 0x0F) == 0

        # Channel 15 (max 4-bit value)
        packet15 = build_set_pilot_wire_mode_packet(sender_id, PILOT_WIRE_MODE_COMFORT, channel=15)
        assert (packet15[1] & 0x0F) == 15

    def test_mode_masking_on_build(self):
        """Test that only lower nibble is used when building."""
        sender_id = [0x01, 0x02, 0x03, 0x04]
        # Pass value > 15 (should be masked)
        packet = build_set_pilot_wire_mode_packet(sender_id, 0xF1)

        assert packet[2] == 0x01  # 0xF1 & 0x0F = 0x01

