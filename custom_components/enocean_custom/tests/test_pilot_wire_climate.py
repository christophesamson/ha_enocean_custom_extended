# -*- encoding: utf-8 -*-
"""Tests for EnOceanPilotWireClimate entity.

These tests require Home Assistant dependencies to be installed.
They are designed to run in a Home Assistant development environment.

Run with:
    pytest custom_components/enocean_custom/tests/test_pilot_wire_climate.py -v

For standalone packet tests that don't require HA, see:
    custom_components/enocean_custom/enocean_library/protocol/tests/test_pilot_wire_packets.py
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# These imports require Home Assistant to be installed
from homeassistant.components.climate import (
    ATTR_PRESET_MODE,
    HVACAction,
    HVACMode,
    ClimateEntityFeature,
    PRESET_COMFORT,
)
from homeassistant.const import (
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    UnitOfTemperature,
)

from custom_components.enocean_custom.climate import (
    EnOceanPilotWireClimate,
    PRESET_COMFORT_MINUS_1,
    PRESET_COMFORT_MINUS_2,
    PRESET_FROST_PROTECTION,
    PRESET_ECO,
    PILOT_WIRE_MODE_OFF,
    PILOT_WIRE_MODE_COMFORT,
    PILOT_WIRE_MODE_ECO,
    PILOT_WIRE_MODE_FROST_PROTECTION,
    PILOT_WIRE_MODE_COMFORT_MINUS_1,
    PILOT_WIRE_MODE_COMFORT_MINUS_2,
    generate_unique_id,
)


class TestEnOceanPilotWireClimateInit:
    """Test EnOceanPilotWireClimate initialization."""

    def test_init_default_values(self):
        """Test that default values are set correctly on initialization."""
        dev_id = [0xFF, 0xD9, 0x04, 0x81]
        dev_name = "test_pilot_wire"

        entity = EnOceanPilotWireClimate(dev_id, dev_name)

        assert entity.dev_id == dev_id
        assert entity.dev_name == dev_name
        assert entity._sender_id == dev_id
        assert entity._attr_temperature_unit == UnitOfTemperature.CELSIUS
        assert entity._attr_hvac_mode is None
        assert entity._attr_preset_mode == PRESET_COMFORT
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_COMFORT
        assert entity._attr_unique_id == generate_unique_id(dev_id, 0)

    def test_init_supported_features(self):
        """Test that supported features are set correctly."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")

        expected_features = (
            ClimateEntityFeature.PRESET_MODE
            | ClimateEntityFeature.TURN_OFF
            | ClimateEntityFeature.TURN_ON
        )
        assert entity._attr_supported_features == expected_features

    def test_init_hvac_modes(self):
        """Test that HVAC modes are set correctly."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")

        assert HVACMode.HEAT in entity._attr_hvac_modes
        assert HVACMode.OFF in entity._attr_hvac_modes
        assert len(entity._attr_hvac_modes) == 2

    def test_init_preset_modes(self):
        """Test that preset modes are set correctly."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")

        expected_presets = [
            PRESET_COMFORT,
            PRESET_ECO,
            PRESET_FROST_PROTECTION,
            PRESET_COMFORT_MINUS_1,
            PRESET_COMFORT_MINUS_2,
        ]
        assert entity._attr_preset_modes == expected_presets

    def test_name_property(self):
        """Test the name property returns dev_name."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "my_heater")
        assert entity.name == "my_heater"


class TestEnOceanPilotWireClimateHvacAction:
    """Test hvac_action property."""

    def test_hvac_action_off_when_hvac_mode_off(self):
        """Test hvac_action returns OFF when HVAC mode is OFF."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.OFF

        assert entity.hvac_action == HVACAction.OFF

    def test_hvac_action_off_when_pilot_wire_mode_off(self):
        """Test hvac_action returns OFF when pilot wire mode is OFF."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity._pilot_wire_mode = PILOT_WIRE_MODE_OFF

        assert entity.hvac_action == HVACAction.OFF

    def test_hvac_action_idle_when_frost_protection(self):
        """Test hvac_action returns IDLE when in frost protection mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity._pilot_wire_mode = PILOT_WIRE_MODE_FROST_PROTECTION

        assert entity.hvac_action == HVACAction.IDLE

    def test_hvac_action_heating_when_comfort(self):
        """Test hvac_action returns HEATING when in comfort mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity._pilot_wire_mode = PILOT_WIRE_MODE_COMFORT

        assert entity.hvac_action == HVACAction.HEATING

    def test_hvac_action_heating_when_eco(self):
        """Test hvac_action returns HEATING when in eco mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity._pilot_wire_mode = PILOT_WIRE_MODE_ECO

        assert entity.hvac_action == HVACAction.HEATING


class TestEnOceanPilotWireClimateSetHvacMode:
    """Test async_set_hvac_mode method."""

    @pytest.mark.asyncio
    async def test_set_hvac_mode_heat(self):
        """Test setting HVAC mode to HEAT."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.OFF
        entity._pilot_wire_mode = PILOT_WIRE_MODE_COMFORT
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_hvac_mode(HVACMode.HEAT)

        assert entity._attr_hvac_mode == HVACMode.HEAT
        entity._send_pilot_wire_mode.assert_called_once_with(PILOT_WIRE_MODE_COMFORT)
        entity.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_hvac_mode_off(self):
        """Test setting HVAC mode to OFF."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_hvac_mode(HVACMode.OFF)

        assert entity._attr_hvac_mode == HVACMode.OFF
        entity._send_pilot_wire_mode.assert_called_once_with(PILOT_WIRE_MODE_OFF)
        entity.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_hvac_mode_invalid(self):
        """Test setting an invalid HVAC mode does nothing."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.OFF
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_hvac_mode(HVACMode.COOL)

        assert entity._attr_hvac_mode == HVACMode.OFF
        entity._send_pilot_wire_mode.assert_not_called()
        entity.async_write_ha_state.assert_not_called()


class TestEnOceanPilotWireClimateSetPresetMode:
    """Test async_set_preset_mode method."""

    @pytest.mark.asyncio
    async def test_set_preset_mode_comfort(self):
        """Test setting preset mode to comfort."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_preset_mode(PRESET_COMFORT)

        assert entity._attr_preset_mode == PRESET_COMFORT
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_COMFORT
        entity._send_pilot_wire_mode.assert_called_once_with(PILOT_WIRE_MODE_COMFORT)
        entity.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_preset_mode_eco(self):
        """Test setting preset mode to eco."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_preset_mode(PRESET_ECO)

        assert entity._attr_preset_mode == PRESET_ECO
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_ECO
        entity._send_pilot_wire_mode.assert_called_once_with(PILOT_WIRE_MODE_ECO)

    @pytest.mark.asyncio
    async def test_set_preset_mode_frost_protection(self):
        """Test setting preset mode to frost protection."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_preset_mode(PRESET_FROST_PROTECTION)

        assert entity._attr_preset_mode == PRESET_FROST_PROTECTION
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_FROST_PROTECTION

    @pytest.mark.asyncio
    async def test_set_preset_mode_comfort_minus_1(self):
        """Test setting preset mode to comfort -1."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_preset_mode(PRESET_COMFORT_MINUS_1)

        assert entity._attr_preset_mode == PRESET_COMFORT_MINUS_1
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_COMFORT_MINUS_1

    @pytest.mark.asyncio
    async def test_set_preset_mode_comfort_minus_2(self):
        """Test setting preset mode to comfort -2."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_preset_mode(PRESET_COMFORT_MINUS_2)

        assert entity._attr_preset_mode == PRESET_COMFORT_MINUS_2
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_COMFORT_MINUS_2

    @pytest.mark.asyncio
    async def test_set_preset_mode_no_send_when_hvac_off(self):
        """Test that preset mode change doesn't send command when HVAC is off."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.OFF
        entity.async_write_ha_state = MagicMock()
        entity._send_pilot_wire_mode = MagicMock()

        await entity.async_set_preset_mode(PRESET_ECO)

        assert entity._attr_preset_mode == PRESET_ECO
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_ECO
        entity._send_pilot_wire_mode.assert_not_called()
        entity.async_write_ha_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_preset_mode_invalid_raises_error(self):
        """Test that setting an invalid preset mode raises ValueError."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity.async_write_ha_state = MagicMock()

        with pytest.raises(ValueError, match="unsupported preset_mode"):
            await entity.async_set_preset_mode("invalid_preset")


class TestEnOceanPilotWireClimateSendPilotWireMode:
    """Test _send_pilot_wire_mode method."""

    def test_send_pilot_wire_mode_packet_structure(self):
        """Test that the packet structure is correct for pilot wire mode."""
        dev_id = [0xFF, 0xD9, 0x04, 0x81]
        entity = EnOceanPilotWireClimate(dev_id, "test")
        entity.send_command = MagicMock()

        entity._send_pilot_wire_mode(PILOT_WIRE_MODE_COMFORT)

        # Expected packet: [0xD2, (0x08 << 4) | 0x00, mode, ...sender_id, 0x00]
        expected_command = [0xD2, 0x80, 0x01, 0xFF, 0xD9, 0x04, 0x81, 0x00]
        entity.send_command.assert_called_once_with(expected_command, [], 0x01)

    def test_send_pilot_wire_mode_off(self):
        """Test sending OFF mode."""
        dev_id = [0xFF, 0xD9, 0x04, 0x81]
        entity = EnOceanPilotWireClimate(dev_id, "test")
        entity.send_command = MagicMock()

        entity._send_pilot_wire_mode(PILOT_WIRE_MODE_OFF)

        expected_command = [0xD2, 0x80, 0x00, 0xFF, 0xD9, 0x04, 0x81, 0x00]
        entity.send_command.assert_called_once_with(expected_command, [], 0x01)

    def test_send_pilot_wire_mode_eco(self):
        """Test sending ECO mode."""
        dev_id = [0xFF, 0xD9, 0x04, 0x81]
        entity = EnOceanPilotWireClimate(dev_id, "test")
        entity.send_command = MagicMock()

        entity._send_pilot_wire_mode(PILOT_WIRE_MODE_ECO)

        expected_command = [0xD2, 0x80, 0x02, 0xFF, 0xD9, 0x04, 0x81, 0x00]
        entity.send_command.assert_called_once_with(expected_command, [], 0x01)

    def test_send_pilot_wire_mode_all_modes(self):
        """Test sending all pilot wire modes have correct values."""
        dev_id = [0xAA, 0xBB, 0xCC, 0xDD]
        entity = EnOceanPilotWireClimate(dev_id, "test")
        entity.send_command = MagicMock()

        modes = [
            (PILOT_WIRE_MODE_OFF, 0x00),
            (PILOT_WIRE_MODE_COMFORT, 0x01),
            (PILOT_WIRE_MODE_ECO, 0x02),
            (PILOT_WIRE_MODE_FROST_PROTECTION, 0x03),
            (PILOT_WIRE_MODE_COMFORT_MINUS_1, 0x04),
            (PILOT_WIRE_MODE_COMFORT_MINUS_2, 0x05),
        ]

        for mode_value, expected_byte in modes:
            entity.send_command.reset_mock()
            entity._send_pilot_wire_mode(mode_value)

            call_args = entity.send_command.call_args[0][0]
            assert call_args[0] == 0xD2  # RORG VLD
            assert call_args[1] == 0x80  # CMD 0x08 << 4 | channel 0
            assert call_args[2] == expected_byte  # Mode value


class TestEnOceanPilotWireClimateValueChanged:
    """Test value_changed method for handling incoming packets."""

    def test_value_changed_ignores_non_vld_packets(self):
        """Test that non-VLD packets are ignored."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity.schedule_update_ha_state = MagicMock()

        # Create a mock packet with non-D2 RORG
        packet = MagicMock()
        packet.data = [0xA5, 0xA0, 0x01]  # 4BS packet, not VLD

        entity.value_changed(packet)

        entity.schedule_update_ha_state.assert_not_called()

    def test_value_changed_ignores_non_pilot_wire_response(self):
        """Test that non-pilot wire response commands are ignored."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity.schedule_update_ha_state = MagicMock()

        # Create a mock packet with CMD != 0x0A
        packet = MagicMock()
        packet.data = [0xD2, 0x40, 0x01]  # CMD = 0x04 (Actuator Status Response)

        entity.value_changed(packet)

        entity.schedule_update_ha_state.assert_not_called()

    def test_value_changed_pilot_wire_response_comfort(self):
        """Test handling pilot wire response with comfort mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.OFF
        entity.schedule_update_ha_state = MagicMock()

        # Create a mock packet with CMD = 0x0A, mode = comfort (1)
        packet = MagicMock()
        packet.data = [0xD2, 0xA0, PILOT_WIRE_MODE_COMFORT]  # CMD = 0x0A in upper nibble

        entity.value_changed(packet)

        assert entity._attr_hvac_mode == HVACMode.HEAT
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_COMFORT
        assert entity._attr_preset_mode == PRESET_COMFORT
        entity.schedule_update_ha_state.assert_called_once()

    def test_value_changed_pilot_wire_response_eco(self):
        """Test handling pilot wire response with eco mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity.schedule_update_ha_state = MagicMock()

        packet = MagicMock()
        packet.data = [0xD2, 0xA0, PILOT_WIRE_MODE_ECO]

        entity.value_changed(packet)

        assert entity._attr_hvac_mode == HVACMode.HEAT
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_ECO
        assert entity._attr_preset_mode == PRESET_ECO

    def test_value_changed_pilot_wire_response_off(self):
        """Test handling pilot wire response with off mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity._attr_hvac_mode = HVACMode.HEAT
        entity.schedule_update_ha_state = MagicMock()

        packet = MagicMock()
        packet.data = [0xD2, 0xA0, PILOT_WIRE_MODE_OFF]

        entity.value_changed(packet)

        assert entity._attr_hvac_mode == HVACMode.OFF
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_OFF

    def test_value_changed_pilot_wire_response_frost_protection(self):
        """Test handling pilot wire response with frost protection mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity.schedule_update_ha_state = MagicMock()

        packet = MagicMock()
        packet.data = [0xD2, 0xA0, PILOT_WIRE_MODE_FROST_PROTECTION]

        entity.value_changed(packet)

        assert entity._attr_hvac_mode == HVACMode.HEAT
        assert entity._pilot_wire_mode == PILOT_WIRE_MODE_FROST_PROTECTION
        assert entity._attr_preset_mode == PRESET_FROST_PROTECTION

    def test_value_changed_pilot_wire_response_comfort_minus_1(self):
        """Test handling pilot wire response with comfort -1 mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity.schedule_update_ha_state = MagicMock()

        packet = MagicMock()
        packet.data = [0xD2, 0xA0, PILOT_WIRE_MODE_COMFORT_MINUS_1]

        entity.value_changed(packet)

        assert entity._attr_preset_mode == PRESET_COMFORT_MINUS_1

    def test_value_changed_pilot_wire_response_comfort_minus_2(self):
        """Test handling pilot wire response with comfort -2 mode."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity.schedule_update_ha_state = MagicMock()

        packet = MagicMock()
        packet.data = [0xD2, 0xA0, PILOT_WIRE_MODE_COMFORT_MINUS_2]

        entity.value_changed(packet)

        assert entity._attr_preset_mode == PRESET_COMFORT_MINUS_2


class TestEnOceanPilotWireClimateTeachIn:
    """Test teach-in methods."""

    def test_teach_in_pilot_wire_packet_structure(self):
        """Test that teach-in packet has correct UTE structure."""
        dev_id = [0xFF, 0xD9, 0x04, 0x81]
        entity = EnOceanPilotWireClimate(dev_id, "test")
        entity.send_command = MagicMock()

        entity.teach_in_pilot_wire()

        # Expected UTE teach-in packet
        expected_command = [
            0xD4,  # UTE RORG
            0x20,  # Teach-in request, bidirectional
            0xD2,  # EEP RORG
            0x01,  # EEP FUNC
            0x0C,  # EEP TYPE
            0x00,  # Manufacturer ID high byte
            0x46,  # Manufacturer ID low byte (NodOn)
            0xFF, 0xD9, 0x04, 0x81,  # Sender ID
            0x00,  # Status
        ]
        entity.send_command.assert_called_once_with(expected_command, [], 0x01)

    def test_teach_in_actor_calls_teach_in_pilot_wire(self):
        """Test that teach_in_actor is an alias for teach_in_pilot_wire."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")
        entity.teach_in_pilot_wire = MagicMock()

        entity.teach_in_actor()

        entity.teach_in_pilot_wire.assert_called_once()

    def test_teach_in_actor_switch_logs_warning(self):
        """Test that teach_in_actor_switch logs a warning."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")

        # Should not raise, just log warning
        entity.teach_in_actor_switch()


class TestEnOceanPilotWireClimateMappings:
    """Test preset to pilot wire mode mappings."""

    def test_preset_to_pilot_wire_mapping(self):
        """Test that preset to pilot wire mapping is correct."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")

        assert entity.PRESET_TO_PILOT_WIRE[PRESET_COMFORT] == PILOT_WIRE_MODE_COMFORT
        assert entity.PRESET_TO_PILOT_WIRE[PRESET_ECO] == PILOT_WIRE_MODE_ECO
        assert entity.PRESET_TO_PILOT_WIRE[PRESET_FROST_PROTECTION] == PILOT_WIRE_MODE_FROST_PROTECTION
        assert entity.PRESET_TO_PILOT_WIRE[PRESET_COMFORT_MINUS_1] == PILOT_WIRE_MODE_COMFORT_MINUS_1
        assert entity.PRESET_TO_PILOT_WIRE[PRESET_COMFORT_MINUS_2] == PILOT_WIRE_MODE_COMFORT_MINUS_2

    def test_pilot_wire_to_preset_mapping(self):
        """Test that pilot wire to preset mapping is correct (reverse mapping)."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")

        assert entity.PILOT_WIRE_TO_PRESET[PILOT_WIRE_MODE_COMFORT] == PRESET_COMFORT
        assert entity.PILOT_WIRE_TO_PRESET[PILOT_WIRE_MODE_ECO] == PRESET_ECO
        assert entity.PILOT_WIRE_TO_PRESET[PILOT_WIRE_MODE_FROST_PROTECTION] == PRESET_FROST_PROTECTION
        assert entity.PILOT_WIRE_TO_PRESET[PILOT_WIRE_MODE_COMFORT_MINUS_1] == PRESET_COMFORT_MINUS_1
        assert entity.PILOT_WIRE_TO_PRESET[PILOT_WIRE_MODE_COMFORT_MINUS_2] == PRESET_COMFORT_MINUS_2

    def test_mappings_are_bijective(self):
        """Test that mappings are bijective (one-to-one correspondence)."""
        entity = EnOceanPilotWireClimate([0xFF, 0xD9, 0x04, 0x81], "test")

        # Every preset should map to a unique pilot wire mode
        assert len(entity.PRESET_TO_PILOT_WIRE) == len(set(entity.PRESET_TO_PILOT_WIRE.values()))

        # Reverse mapping should have same number of entries
        assert len(entity.PRESET_TO_PILOT_WIRE) == len(entity.PILOT_WIRE_TO_PRESET)


class TestGenerateUniqueId:
    """Test generate_unique_id helper function."""

    def test_generate_unique_id(self):
        """Test unique ID generation."""
        dev_id = [0xFF, 0xD9, 0x04, 0x81]
        unique_id = generate_unique_id(dev_id, 0)

        # combine_hex should produce an integer from the dev_id bytes
        assert "-0" in unique_id

    def test_generate_unique_id_different_channels(self):
        """Test that different channels produce different unique IDs."""
        dev_id = [0xFF, 0xD9, 0x04, 0x81]

        id_channel_0 = generate_unique_id(dev_id, 0)
        id_channel_1 = generate_unique_id(dev_id, 1)

        assert id_channel_0 != id_channel_1
        assert "-0" in id_channel_0
        assert "-1" in id_channel_1

