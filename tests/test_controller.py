
from unittest.mock import MagicMock, patch

from Input.controller import Controller


def test_read_controller_inputs():
    with patch("Input.controller.pygame") as mock_pygame:

        mock_joystick = MagicMock()

        mock_pygame.joystick.get_count.return_value = 1
        mock_pygame.joystick.Joystick.return_value = mock_joystick

        mock_joystick.get_numaxes.return_value = 2
        mock_joystick.get_axis.side_effect = [0.5, -0.5]

        mock_joystick.get_numbuttons.return_value = 2
        mock_joystick.get_button.side_effect = [1, 0]

        mock_joystick.get_numhats.return_value = 1
        mock_joystick.get_hat.return_value = (0, 1)

        controller = Controller(dead_zone=0.1)
        data = controller.read()

        assert data["axes"] == [0.5, -0.5]
        assert data["buttons"] == [1, 0]
        assert data["hats"] == [(0, 1)]


def test_controller_disconnects():
    with patch("Input.controller.pygame") as mock_pygame:

        mock_joystick = MagicMock()

        mock_pygame.joystick.get_count.return_value = 1
        mock_pygame.joystick.Joystick.return_value = mock_joystick

        controller = Controller(dead_zone=0.1)

        mock_pygame.joystick.get_count.return_value = 0

        controller.check_connection()

        assert controller.joystick is None
        mock_joystick.quit.assert_called_once()


def test_controller_reconnects():
    with patch("Input.controller.pygame") as mock_pygame:

        mock_joystick = MagicMock()

        mock_pygame.joystick.get_count.return_value = 0

        controller = Controller(dead_zone=0.1)

        assert controller.joystick is None

        mock_pygame.joystick.get_count.return_value = 1
        mock_pygame.joystick.Joystick.return_value = mock_joystick

        controller.check_connection()

        assert controller.joystick is mock_joystick
        mock_joystick.init.assert_called_once()


def test_dead_zone():
    with patch("Input.controller.pygame") as mock_pygame:

        mock_joystick = MagicMock()

        mock_pygame.joystick.get_count.return_value = 1
        mock_pygame.joystick.Joystick.return_value = mock_joystick

        mock_joystick.get_numaxes.return_value = 3
        mock_joystick.get_axis.side_effect = [0.05, -0.08, 0.5]

        mock_joystick.get_numbuttons.return_value = 0
        mock_joystick.get_numhats.return_value = 0

        controller = Controller(dead_zone=0.1)
        data = controller.read()

        assert data["axes"] == [0.0, 0.0, 0.5]


def test_get_actions():
    with patch("Input.controller.pygame") as mock_pygame:

        mock_joystick = MagicMock()

        mock_pygame.joystick.get_count.return_value = 1
        mock_pygame.joystick.Joystick.return_value = mock_joystick

        controller = Controller(dead_zone=0.1)

        profile = {
            "controller": {
                "forward_axis": 1,
                "left_axis": 0,
                "arm_button": 1
            }
        }

        data = {
            "axes": [0.5, -0.8],
            "buttons": [0, 1],
            "hats": []
        }

        actions = controller.get_actions(profile, data)

        assert actions == {
            "forward": 0.8,
            "left": -0.5,
            "arm": True
        }
