from __future__ import annotations

from typing import Any, Dict, Optional, Type
import pyray as rl

from engine.framework import Manager


class MultiManager(Manager):
    """Manager container for multiple managers of the same base type."""
    def __init__(self) -> None:
        super().__init__()
        self.managers: Dict[str, Manager] = {}

    def init(self) -> None:
        """Initialize all contained managers.

        Returns:
            None
        """
        for manager in self.managers.values():
            manager.init_manager()
        super().init()

    def add_manager(self, name: str, manager_or_cls: Any, *args: Any, **kwargs: Any) -> Manager:
        """Add a manager instance or construct one from a class.

        Args:
            name: Name to register the manager under.
            manager_or_cls: Manager instance or Manager class.
            *args: Positional args forwarded to the constructor.
            **kwargs: Keyword args forwarded to the constructor.

        Returns:
            The manager instance added.
        """
        if isinstance(manager_or_cls, Manager):
            manager = manager_or_cls
        else:
            manager = manager_or_cls(*args, **kwargs)
        self.managers[name] = manager
        return manager

    def get_manager(self, name: str) -> Optional[Manager]:
        """Get a manager by name.

        Args:
            name: Manager name.

        Returns:
            The manager instance, or None if missing.
        """
        return self.managers.get(name)


class FontManager(Manager):
    """Manager for handling fonts so they are not loaded multiple times."""
    def __init__(self) -> None:
        super().__init__()
        self.fonts: Dict[str, Any] = {"default": rl.get_font_default()}

    def load_font(self, name: str, filename: str, size: int = 32) -> Any:
        """Load a font from a file (cached by name).

        Args:
            name: Name to register the font under.
            filename: Path to the font file.
            size: Font size used for the texture atlas.

        Returns:
            The loaded font instance.
        """
        if name in self.fonts:
            return self.fonts[name]

        font = rl.load_font_ex(filename, size, None, 0)
        self.fonts[name] = font
        return font

    def get_font(self, name: str) -> Any:
        """Get a font by name.

        Args:
            name: Font name.

        Returns:
            The font instance.
        """
        return self.fonts[name]

    def set_texture_filter(self, name: str, texture_filter: int) -> None:
        """Set the texture filter for a font.

        Args:
            name: Font name.
            texture_filter: Raylib texture filter enum value.

        Returns:
            None
        """
        if name in self.fonts:
            rl.set_texture_filter(self.fonts[name].texture, texture_filter)


class WindowManager(Manager):
    """Manager for handling the application window and audio device."""
    def __init__(self, width: int = 1280, height: int = 720, title: str = "My Game", fps: int = 60) -> None:
        super().__init__()
        self.width = width
        self.height = height
        self.title = title
        self.target_fps = fps

    def init(self) -> None:
        """Initialize the window and audio device.

        Returns:
            None
        """
        rl.set_config_flags(rl.FLAG_WINDOW_RESIZABLE)
        rl.init_window(self.width, self.height, self.title)
        rl.init_audio_device()
        rl.set_target_fps(self.target_fps)
        mappings = rl.load_file_text("assets/gamecontrollerdb.txt")
        if mappings:
            try:
                rl.set_gamepad_mappings(mappings)
            except Exception:
                print("Failed to set gamepad mappings")
        super().init()

    def set_title(self, title: str) -> None:
        """Set the window title.

        Args:
            title: New title string.

        Returns:
            None
        """
        self.title = title
        rl.set_window_title(title)

    def get_width(self) -> float:
        """Get the window width.

        Returns:
            Window width in pixels.
        """
        return float(self.width)

    def get_height(self) -> float:
        """Get the window height.

        Returns:
            Window height in pixels.
        """
        return float(self.height)

    def get_size(self):
        """Get the window size as a Vector2.

        Returns:
            Vector2 containing width and height.
        """
        return rl.Vector2(float(self.width), float(self.height))

    def get_aspect_ratio(self) -> float:
        """Get the window aspect ratio.

        Returns:
            Width divided by height.
        """
        return float(self.width) / float(self.height)
