import pyray as rl

from engine.math_extensions import v2
from engine.framework import Scene
from engine.prefabs.includes import FontManager


class TitleScreen(Scene):
    def __init__(self):
        super().__init__()
        self.font = None
        self.title = "Game Jam Kit"

    def init(self):
        font_manager = self.game.get_manager(FontManager)
        self.font = font_manager.get_font("Roboto")

    def update(self, delta_time):
        # Trigger scene change on Enter key or gamepad start button.
        if rl.is_key_pressed(rl.KEY_ENTER) or rl.is_gamepad_button_pressed(0, rl.GAMEPAD_BUTTON_MIDDLE_RIGHT):
            self.game.go_to_scene_next()

    def draw(self):
        width = rl.get_screen_width()
        height = rl.get_screen_height()
        title_text_size = rl.measure_text_ex(self.font, self.title, 64, 0)

        subtitle = "Press Start or Enter to Switch Scenes"
        subtitle_text_size = rl.measure_text_ex(self.font, subtitle, 32, 0)

        rl.clear_background(rl.SKYBLUE)
        rl.draw_text_ex(
            self.font,
            self.title,
            v2((width - title_text_size.x) / 2, (height - title_text_size.y - 100) / 2),
            64,
            1,
            rl.WHITE,
        )
        rl.draw_text_ex(
            self.font,
            subtitle,
            v2((width - subtitle_text_size.x) / 2, (height - subtitle_text_size.y + 100) / 2),
            32,
            1,
            rl.WHITE,
        )
