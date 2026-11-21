
from unittest.mock import MagicMock

from Input.keyboard import Keyboard


def test_keyboard_keydown():
    keyboard = Keyboard()

    try:
        keyboard.on_press(MagicMock(char="w"))

        keys = keyboard.read()

        assert "w" in keys

    finally:
        keyboard.close()


def test_keyboard_keyup():
    keyboard = Keyboard()

    try:
        keyboard.on_press(MagicMock(char="w"))
        keyboard.on_release(MagicMock(char="w"))

        keys = keyboard.read()

        assert "w" not in keys

    finally:
        keyboard.close()
