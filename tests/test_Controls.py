import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, call
from src.RP2040 import Controls


@pytest.fixture
def base_config():
    return {"RP_connection":{"sim": True,
                                 "super_sim": True,
                                 "baud_rate": 115200,
                                 "device_ID": "/dev/ttyACM0",
                                 "fake_device_ID": "/pty/ttyVirtual0",
                                 "time_out": 1,
                                 "read_time": 0.5,
                                 "hb_send_msg": "ping",
                                 "hb_receive_msg": "pong",
                                 "retries": 3,
                                 "connection_cycles": 2,
                                 "power_cycles": 2,
                                 }}

@pytest.fixture
def super_sim_config(base_config):
    base_config["RP_connection"]["sim"] = False
    return base_config

@pytest.fixture
def sim_config(base_config):
    base_config["RP_connection"]["super_sim"] = False
    return base_config

@pytest.fixture
def real_config(base_config):
    base_config["RP_connection"]["sim"] = False
    base_config["RP_connection"]["super_sim"] = False
    return base_config

@pytest.fixture
def super_sim_Controls(super_sim_config):
    return Controls(super_sim_config)
@pytest.fixture
def sim_Controls(sim_config):
    return Controls(sim_config)

@pytest.fixture
def real_Controls(real_config):
    return Controls(real_config)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# RP2040Communication Tests

def test_super_sim_initialize_connection(super_sim_Controls):
    fake_serial_instance = MagicMock()
    with patch("src.RP2040.FakeSerial", return_value=fake_serial_instance) as mock_FakeSerial:
        super_sim_Controls._initialize_connection()

    mock_FakeSerial.assert_called_once_with(super_sim_Controls.config)
    assert super_sim_Controls.ser is fake_serial_instance


@pytest.mark.parametrize(
    "controls_fixture, expected_device_attr",
    [
        ("sim_Controls", "fake_device_ID"),
        ("real_Controls", "device_ID")
    ]
)

def test_initialize_connection(controls_fixture, expected_device_attr, request):
    controls = request.getfixturevalue(controls_fixture)
    fake_serial_instance = MagicMock()

    expected_device = getattr(controls, expected_device_attr)

    with patch("src.RP2040.serial.Serial", return_value=fake_serial_instance) as mock_serial: 
        controls._initialize_connection()
    
    mock_serial.assert_called_once_with(expected_device, 
                                        controls.baud_rate,
                                        controls.time_out
                                        )
    
    assert controls.ser is fake_serial_instance

def test_initialize_connection_failure(sim_Controls):

    with patch("src.RP2040.serial.Serial", side_effect=Exception("failure_test")):
        with patch("src.RP2040.logger") as mock_logger:

            sim_Controls._initialize_connection()

    mock_logger.error.assert_called_once()
    assert not hasattr(sim_Controls, "ser") or sim_Controls.ser is None


# Using sim controls as the natural default here, could use real or
# super_sim but behavior does not branch
def test_disconnect(sim_Controls):
    sim_Controls.ser = MagicMock() 
    sim_Controls._disconnect()
    sim_Controls.ser.close.assert_called_once_with()

def test_disconnect_exception(sim_Controls):

    sim_Controls.ser = MagicMock()
    sim_Controls.ser.close.side_effect = Exception("boom")

    with patch("src.RP2040.logger") as mock_logger:
        sim_Controls._disconnect()

    mock_logger.error.assert_called_once()


@pytest.mark.parametrize(
    "serial_response, expected_result, expect_error_log",
    [
        (b"pong", True, False),
        (b"", False, True),
    ]
)

# Using sim controls as the natural default here, could use real or
# super_sim but behavior does not branch
def test_read_and_write(
    sim_Controls, 
    serial_response, 
    expected_result,
    expect_error_log
):
    start_time = datetime(2024, 1, 1, 0, 0, 0)

    sim_Controls.ser = MagicMock()
    sim_Controls.ser.readline.return_value = serial_response

    times = [
        start_time,
        start_time + timedelta(seconds=0.001),
        start_time + timedelta(seconds=10000)
    ]

    with patch("src.RP2040.datetime") as mock_datetime, \
         patch("src.RP2040.logger") as mock_logger:

        mock_datetime.now.side_effect = times

        result = sim_Controls._read_and_write("ping", "pong")

    assert result is expected_result

    sim_Controls.ser.write.assert_called_once_with(b"ping")

    if expect_error_log:
        mock_logger.error.assert_called_once()
    else:
        mock_logger.error.assert_not_called()


def test_read_and_write_early_failure(sim_Controls):
    sim_Controls.ser = MagicMock()
    sim_Controls.ser.write.side_effect = Exception("fail here")
    with patch("src.RP2040.logger") as mock_logger:
        result = sim_Controls._read_and_write("ping", "pong")

    mock_logger.error.assert_called_once()
    assert result is False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# RP2040AdvancedErrorHandling Tests

@pytest.mark.parametrize(
        "confirmed, expected_result",
        [
            (True, True),
            (False, False),
        ]
)
def test_retries(sim_Controls, confirmed, expected_result):
    with patch.object(sim_Controls, 
                      "_read_and_write", 
                      return_value=confirmed) as mock_rw:
        result = sim_Controls._retries("ping", "pong")
    if confirmed: 
        mock_rw.assert_called_once_with("ping", "pong")
    else: 
        mock_rw.assert_any_call("ping", "pong")
        assert mock_rw.call_count == sim_Controls.retries
    assert result is expected_result


@pytest.mark.parametrize(
        "confirmed, expected_result",
        [
            (True, True),
            (False, False),
        ]
)
def test_reconnect(sim_Controls, confirmed, expected_result):
    with patch.object(sim_Controls, "_disconnect") as mock_disconnect, \
         patch.object(sim_Controls, "_initialize_connection") as mock_connect, \
         patch.object( sim_Controls, "_read_and_write", return_value=confirmed) as mock_rw:
        
        result = sim_Controls._reconnect()
    
        if confirmed: 
            mock_disconnect.assert_called_once()
            mock_connect.assert_called_once()
            mock_rw.assert_called_once()
            assert result is expected_result
        else: 
            assert mock_disconnect.call_count == sim_Controls.connection_cycles
            assert mock_connect.call_count == sim_Controls.connection_cycles
            assert mock_rw.call_count == sim_Controls.connection_cycles
            assert result is expected_result


@pytest.mark.parametrize(
    "pca, confirmed, expected_result",
    [
        (False, None, False),
        (True, True, True),
        (True, False, False),
        (True, False, False),
    ]
)

def test_power_cycle(sim_Controls, pca, confirmed, expected_result,):
    with patch.object(sim_Controls, "_read_and_write", return_value=confirmed) as mock_rw:
        
        result = sim_Controls._power_cycle(pca)

        if pca is False: 
            assert result is expected_result

        if pca: 
            if confirmed:
                mock_rw.assert_called_once()
                assert result is expected_result
            if confirmed is False: 
                assert mock_rw.call_count == sim_Controls.power_cycles

def test_power_cycle_exception(sim_Controls):
    with patch.object(sim_Controls, "_read_and_write", side_effect=Exception("boom")) as mock_rw, \
         patch("src.RP2040.logger") as mock_logger:
        
        pca = True 
        result = sim_Controls._power_cycle(pca)

        assert mock_logger.error.call_count == sim_Controls.power_cycles
        assert result is False


@pytest.mark.parametrize(
    "cl_1, cl_2, cl_3, confirmed",
    [
        (True, False, False, True),
        (False, True, False, True),
        (False, False, True, True),
        (False, False, False, False),
    ]
)

def test_advanced_connection(sim_Controls, cl_1, cl_2, cl_3, confirmed): 
    with patch.object(sim_Controls, "_retries", return_value=cl_1) as mock_retires, \
         patch.object(sim_Controls, "_reconnect", return_value=cl_2) as mock_reconnect, \
         patch.object(sim_Controls, "_power_cycle", return_value=cl_3) as mock_power_cycle:
        
        rl_dict = sim_Controls.advanced_connection("ping", "pong", True)

        assert rl_dict["retries"] == cl_1
        assert rl_dict["software_cycle"] == cl_2
        assert rl_dict["power_cycle"] == cl_3

        if cl_1: 
            mock_retires.assert_called_once()
            mock_reconnect.assert_not_called()
            mock_power_cycle.assert_not_called()
        elif cl_2: 
            mock_retires.assert_called_once()
            mock_reconnect.assert_called_once()
            mock_power_cycle.assert_not_called()
        elif cl_3: 
            mock_retires.assert_called_once()
            mock_reconnect.assert_called_once()
            mock_power_cycle.assert_called_once()
        else: 
            mock_retires.assert_called_once()
            mock_reconnect.assert_called_once()
            mock_power_cycle.assert_called_once()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Controls Tests

def test_connect(sim_Controls):
    with patch.object(sim_Controls, "_initialize_connection") as mock_connect:
        sim_Controls.connect()

@pytest.mark.parametrize(
        "send_msg, receive_msg, confirmed",
        [
            (None, None, True),
            ("ping", "pong", True),
        ]
)
def test_full_communication_handling_success(sim_Controls,
                                     send_msg, 
                                     receive_msg, 
                                     confirmed):
    
    with patch.object(sim_Controls, "_read_and_write", return_value=confirmed) as mock_rw:
        
        result = sim_Controls.full_communication_handling(True, send_msg, receive_msg)

        if send_msg is None:
            mock_rw.assert_called_once_with(sim_Controls.hb_send_msg, sim_Controls.hb_receive_msg)
        else:
            mock_rw.assert_called_once_with(send_msg, receive_msg)
        assert result

@pytest.mark.parametrize(
    "send_msg, receive_msg, recovery_dict, new_confirmed",
    [
        ("ping", "pong", {"retries": True, "software_cycle": False, "power_cycle": False}, True),
        ("ping", "pong", {"retries": False, "software_cycle": True, "power_cycle": False}, True),
        ("ping", "pong", {"retries": False, "software_cycle": True, "power_cycle": False}, False),
        ("ping", "pong", {"retries": False, "software_cycle": False, "power_cycle": True}, True),
        ("ping", "pong", {"retries": False, "software_cycle": False, "power_cycle": True}, False),
    ]
)

def test_full_communication_handling_recovery(sim_Controls,
                                              send_msg, 
                                              receive_msg, 
                                              recovery_dict,
                                              new_confirmed):
    with patch.object(sim_Controls, "_read_and_write", 
                      side_effect=[False, new_confirmed]) as mock_rw, \
         patch.object(sim_Controls, "advanced_connection", 
                      return_value=recovery_dict) as mock_advanced_connection:
        
        result = sim_Controls.full_communication_handling(True, send_msg, receive_msg)

        expected_result = (recovery_dict["retries"] or new_confirmed)
        assert result is expected_result
        mock_advanced_connection.assert_called_once_with(send_msg, receive_msg, True)

        if recovery_dict["retries"]: 
            mock_rw.assert_called_once_with(send_msg, receive_msg)
        else:
            mock_rw.assert_has_calls([
                call(send_msg, receive_msg),
                call(send_msg, receive_msg),])
            assert mock_rw.call_count == 2
        
def test_full_communications_handling_failure(sim_Controls):
    with patch.object(sim_Controls, "_read_and_write", return_value=False) as mock_rw, \
        patch.object(sim_Controls,
                     "advanced_connection", 
                     return_value={"retries": False, 
                                   "software_cycle": False, 
                                   "power_cycle": False}) as mock_advanced_connection:
        
        result = sim_Controls.full_communication_handling(True, "ping", "pong")
        mock_rw.assert_called_once_with("ping", "pong")
        mock_advanced_connection.assert_called_once_with("ping", "pong", True)
        assert result is False

@pytest.mark.parametrize(
        "send_msg, receive_msg, confirm",
        [
            ("pingg", "pongg", True),
            ("ping", "pong", False),
            (None, None, True),
        ]
)
def test_heart_beat(sim_Controls, send_msg, receive_msg, confirm):
    with patch.object(sim_Controls, 
                      "full_communication_handling", 
                      return_value = confirm) as mock_full_comms_handling:
        result = sim_Controls.heart_beat(send_msg, receive_msg)

        if send_msg is None and receive_msg is None:
            mock_full_comms_handling.assert_called_once_with(sim_Controls.hb_send_msg, 
                                                             sim_Controls.hb_receive_msg)
        else:
            mock_full_comms_handling.assert_called_once_with(send_msg, receive_msg)

        assert result is confirm

            
def test_GPIO(sim_Controls):
    with patch.object(sim_Controls,
                       "full_communication_handling",
                       return_value = True) as mock_full_comms_handling:
        channel = 8
        side    = 8
        time    = 50
        result = sim_Controls.GPIO(True, channel, side, time)
        msg = "GPIO, " + str(channel) + ", " + str(side) + ", " + str(time)
        mock_full_comms_handling.assert_called_once_with(msg, msg)
        assert result is True

def test_PWM(sim_Controls):
    with patch.object(sim_Controls,
                       "full_communication_handling",
                       return_value = True) as mock_full_comms_handling:
        channel = 8
        clicks  = 10000
        time    = 50
        result = sim_Controls.PWM(True, channel, clicks, time)
        msg = "PWM, " + str(channel) + ", " + str(clicks) + ", " + str(time)
        mock_full_comms_handling.assert_called_once_with(msg, msg)
        assert result is True

def test_Lights(sim_Controls):
    with patch.object(sim_Controls,
                       "full_communication_handling",
                       return_value = True) as mock_full_comms_handling:
        channel = 4
        g       = 10
        r       = 20
        b       = 30
        w       = 40
        result = sim_Controls.Lights(True, channel, g, r, b, w)
        msg = "Lights, " + str(channel) + ", " + str(g) + ", " + str(r) + ", "  + str(b) + ", " + str(w)
        mock_full_comms_handling.assert_called_once_with(msg, msg)
        assert result is True
