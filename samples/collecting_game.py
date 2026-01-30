"""Demonstration of split screen cameras and sensor-based item collection."""

from __future__ import annotations

import math
from typing import List

from Box2D import b2CircleShape, b2PolygonShape
import pyray as rl

from engine.framework import GameObject, Scene
from engine.math_extensions import vec_div, vec_mul, vec_normalize, vec_sub, v2
from engine.prefabs.components import (AnimationController, BodyComponent, MultiComponent,
                                       PlatformerMovementComponent, PlatformerMovementParams,
                                       SoundComponent)
from engine.prefabs.game_objects import CharacterParams, SplitCamera
from engine.prefabs.managers import FontManager, WindowManager
from engine.prefabs.services import LevelService, PhysicsService, SoundService, TextureService


class CollectingCharacter(GameObject):
    """Basic collecting character.

    Shows how to build a physics body, route input into a movement
component, and drive animations/sounds from gameplay events."""
    def __init__(self, params: CharacterParams, player_number: int = 1) -> None:
        """Create a player-controlled collector.

        Args:
            params: Character sizing and physics parameters.
            player_number: 1-based index used to map input/skins.

        Returns:
            None
        """
        super().__init__()
        self.p = params
        self.player_number = player_number
        self.gamepad = player_number - 1
        self.width = params.width
        self.height = params.height
        self.physics: PhysicsService = None  # type: ignore[assignment]
        self.level: LevelService = None  # type: ignore[assignment]
        self.body: BodyComponent = None  # type: ignore[assignment]
        self.movement: PlatformerMovementComponent = None  # type: ignore[assignment]
        self.animation: AnimationController = None  # type: ignore[assignment]
        self.sounds: MultiComponent = None  # type: ignore[assignment]
        self.jump_sound: SoundComponent = None  # type: ignore[assignment]
        self.die_sound: SoundComponent = None  # type: ignore[assignment]
        self.score = 0

    def init(self) -> None:
        """Initialize physics, movement, sounds, and animations.

        Services are resolved here (not during update) so missing services are
        discovered early and per-frame overhead is avoided.

        Returns:
            None
        """
        self.physics = self.scene.get_service(PhysicsService)

        def build_body(component: BodyComponent):
            """Build body.

            Args:
                component: Parameter.

            Returns:
                Result of the operation.
            """
            world = self.physics.world
            body = world.CreateDynamicBody(position=(self.physics.convert_to_meters(self.p.position).x,
                                                     self.physics.convert_to_meters(self.p.position).y),
                                           fixedRotation=True,
                                           bullet=True)
            body.userData = self
            shape = b2PolygonShape(box=(self.physics.convert_length_to_meters(self.p.width / 2.0),
                                        self.physics.convert_length_to_meters(self.p.height / 2.0)))
            body.CreateFixture(shape=shape, density=self.p.density, friction=self.p.friction,
                               restitution=self.p.restitution)
            component.body = body

        self.body = self.add_component(BodyComponent(build=build_body))

        movement_params = PlatformerMovementParams()
        movement_params.width = self.p.width
        movement_params.height = self.p.height
        self.movement = self.add_component(PlatformerMovementComponent(movement_params))

        self.level = self.scene.get_service(LevelService)

        self.sounds = self.add_component(MultiComponent())
        self.jump_sound = self.sounds.add_component("jump", SoundComponent, "assets/sounds/jump.wav")
        self.die_sound = self.sounds.add_component("die", SoundComponent, "assets/sounds/die.wav")

        self.animation = self.add_component(AnimationController(self.body))
        if self.player_number == 1:
            self.animation.add_animation_from_files("run",
                                                   ["assets/pixel_platformer/characters/green_1.png",
                                                    "assets/pixel_platformer/characters/green_2.png"],
                                                   10.0)
        elif self.player_number == 2:
            self.animation.add_animation_from_files("run",
                                                   ["assets/pixel_platformer/characters/blue_1.png",
                                                    "assets/pixel_platformer/characters/blue_2.png"],
                                                   10.0)
        elif self.player_number == 3:
            self.animation.add_animation_from_files("run",
                                                   ["assets/pixel_platformer/characters/pink_1.png",
                                                    "assets/pixel_platformer/characters/pink_2.png"],
                                                   10.0)
        elif self.player_number == 4:
            self.animation.add_animation_from_files("run",
                                                   ["assets/pixel_platformer/characters/yellow_1.png",
                                                    "assets/pixel_platformer/characters/yellow_2.png"],
                                                   10.0)

    def update(self, delta_time: float) -> None:
        """Handle input and drive movement/animation.

        Args:
            delta_time: Seconds since last frame.

        Returns:
            None
        """
        deadzone = 0.1
        jump_pressed = rl.is_key_pressed(rl.KEY_W) or rl.is_gamepad_button_pressed(self.gamepad, rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN)
        jump_held = rl.is_key_down(rl.KEY_W) or rl.is_gamepad_button_down(self.gamepad, rl.GAMEPAD_BUTTON_RIGHT_FACE_DOWN)

        move_x = rl.get_gamepad_axis_movement(self.gamepad, rl.GAMEPAD_AXIS_LEFT_X)
        if abs(move_x) < deadzone:
            move_x = 0.0
        if rl.is_key_down(rl.KEY_D) or rl.is_gamepad_button_down(self.gamepad, rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT):
            move_x = 1.0
        elif rl.is_key_down(rl.KEY_A) or rl.is_gamepad_button_down(self.gamepad, rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT):
            move_x = -1.0

        self.movement.set_input(move_x, jump_pressed, jump_held)
        if self.movement.grounded and jump_pressed:
            self.jump_sound.play()

        if abs(self.movement.move_x) > 0.1:
            self.animation.play("run")
            self.animation.flip_x = self.movement.move_x > 0.0
        else:
            self.animation.pause()

    def die(self) -> None:
        """Respawn the character at the start position.

        Returns:
            None
        """
        self.body.set_position(self.p.position)
        self.body.set_velocity(v2(0.0, 0.0))
        self.die_sound.play()


class EnemyType:
    Bat = 0
    DrillHead = 1
    BlockHead = 2


class Enemy(GameObject):
    """Enemy that patrols between two points using a kinematic body."""
    def __init__(self, enemy_type: int, start: rl.Vector2, end: rl.Vector2) -> None:
        """Configure the patrol endpoints and enemy type.

        Args:
            enemy_type: EnemyType constant selecting animation and behavior.
            start: Starting world position in pixels.
            end: Ending world position in pixels.

        Returns:
            None
        """
        super().__init__()
        self.start = start
        self.end = end
        self.type = enemy_type
        self.physics: PhysicsService = None  # type: ignore[assignment]
        self.body: BodyComponent = None  # type: ignore[assignment]
        self.animation: AnimationController = None  # type: ignore[assignment]
        self.radius = 12.0

    def init_object(self) -> None:
        """Create a sensor body, setup animation, and start movement.

        Returns:
            None
        """
        self.physics = self.scene.get_service(PhysicsService)

        def build_body(component: BodyComponent):
            """Build body.

            Args:
                component: Parameter.

            Returns:
                Result of the operation.
            """
            world = self.physics.world
            body = world.CreateKinematicBody(position=(self.physics.convert_to_meters(self.start).x,
                                                       self.physics.convert_to_meters(self.start).y))
            body.userData = self
            shape = b2CircleShape(radius=self.physics.convert_length_to_meters(self.radius))
            body.CreateFixture(shape=shape, density=1.0, isSensor=True)
            component.body = body

        self.body = self.add_component(BodyComponent(build=build_body))

        self.animation = self.add_component(AnimationController(self.body))
        if self.type == EnemyType.Bat:
            self.animation.add_animation_from_files("move",
                                                   ["assets/pixel_platformer/enemies/bat_1.png",
                                                    "assets/pixel_platformer/enemies/bat_2.png",
                                                    "assets/pixel_platformer/enemies/bat_3.png"],
                                                   5.0)
        elif self.type == EnemyType.DrillHead:
            self.animation.add_animation_from_files("move",
                                                   ["assets/pixel_platformer/enemies/drill_head_1.png",
                                                    "assets/pixel_platformer/enemies/drill_head_2.png"],
                                                   5.0)
        elif self.type == EnemyType.BlockHead:
            self.animation.add_animation_from_files("move",
                                                   ["assets/pixel_platformer/enemies/block_head_1.png",
                                                    "assets/pixel_platformer/enemies/block_head_2.png"],
                                                   5.0)
        self.animation.play("move")

        super().init_object()

        to_end = vec_normalize(vec_sub(self.end, self.body.get_position_pixels()))
        self.body.set_velocity(vec_mul(to_end, 50.0))

    def update(self, delta_time: float) -> None:
        """Move between endpoints and detect sensor hits on players.

        Args:
            delta_time: Seconds since last frame.

        Returns:
            None
        """
        pos = self.body.get_position_pixels()
        if math.dist((self.end.x, self.end.y), (pos.x, pos.y)) <= self.radius * 2.0:
            to_start = vec_normalize(vec_sub(self.start, pos))
            self.body.set_velocity(vec_mul(to_start, 50.0))
        elif math.dist((self.start.x, self.start.y), (pos.x, pos.y)) <= self.radius * 2.0:
            to_end = vec_normalize(vec_sub(self.end, pos))
            self.body.set_velocity(vec_mul(to_end, 50.0))

        for contact_body in self.body.get_sensor_overlaps():
            user_data = contact_body.userData
            if user_data and user_data.has_tag("character"):
                user_data.die()

        velocity = self.body.get_velocity_pixels()
        self.animation.flip_x = velocity.x > 0.0


class Coin(GameObject):
    """Collectible coin using a sensor body."""
    def __init__(self, position: rl.Vector2) -> None:
        """Store the coin spawn position.

        Args:
            position: World position in pixels.

        Returns:
            None
        """
        super().__init__()
        self.position = position
        self.physics: PhysicsService = None  # type: ignore[assignment]
        self.body: BodyComponent = None  # type: ignore[assignment]
        self.animation: AnimationController = None  # type: ignore[assignment]
        self.collect_sound: SoundComponent = None  # type: ignore[assignment]

    def init(self) -> None:
        """Create the sensor body, animation, and pickup sound.

        Returns:
            None
        """
        self.physics = self.scene.get_service(PhysicsService)

        def build_body(component: BodyComponent):
            """Build body.

            Args:
                component: Parameter.

            Returns:
                Result of the operation.
            """
            world = self.physics.world
            body = world.CreateStaticBody(position=(self.physics.convert_to_meters(self.position).x,
                                                    self.physics.convert_to_meters(self.position).y))
            body.userData = self
            shape = b2CircleShape(radius=self.physics.convert_length_to_meters(8.0))
            body.CreateFixture(shape=shape, density=1.0, isSensor=True)
            component.body = body

        self.body = self.add_component(BodyComponent(build=build_body))
        self.animation = self.add_component(AnimationController(self.body))
        self.animation.add_animation_from_files("spin",
                                               ["assets/pixel_platformer/items/coin_1.png",
                                                "assets/pixel_platformer/items/coin_2.png"],
                                               5.0)
        self.animation.play("spin")
        self.collect_sound = self.add_component(SoundComponent("assets/sounds/coin.wav"))

    def update(self, delta_time: float) -> None:
        """Check sensor overlaps and award score on pickup.

        Args:
            delta_time: Seconds since last frame.

        Returns:
            None
        """
        for contact_body in self.body.get_sensor_overlaps():
            user_data = contact_body.userData
            if user_data and user_data.has_tag("character"):
                self.collect_sound.play()
                self.is_active = False
                self.body.disable()
                user_data.score += 1
                break


class CollectingScene(Scene):
    """Scene demonstrating split-screen cameras and collectible items."""
    def __init__(self) -> None:
        """Set up scene containers and cached services.

        Returns:
            None
        """
        super().__init__()
        self.window_manager: WindowManager = None  # type: ignore[assignment]
        self.font_manager: FontManager = None  # type: ignore[assignment]
        self.characters: List[CollectingCharacter] = []
        self.level: LevelService = None  # type: ignore[assignment]
        self.physics: PhysicsService = None  # type: ignore[assignment]
        self.cameras: List[SplitCamera] = []
        self.screen_size = v2(0.0, 0.0)
        self.scale = 2.5

    def init_services(self) -> None:
        """Register services required by the scene.

        Returns:
            None
        """
        self.add_service(TextureService)
        self.add_service(SoundService)
        self.physics = self.add_service(PhysicsService)
        collision_names = ["walls", "clouds", "trees"]
        self.level = self.add_service(LevelService, "assets/levels/collecting.ldtk", "Level", collision_names)

    def init(self) -> None:
        """Create characters, enemies, coins, and cameras.

        Returns:
            None
        """
        self.window_manager = self.game.get_manager(WindowManager)
        self.font_manager = self.game.get_manager(FontManager)

        entities_layer = self.level.get_layer_by_name("Entities")
        player_entities = self.level.get_entities_by_name("Start")
        for i, player_entity in enumerate(player_entities[:4]):
            params = CharacterParams()
            params.position = self.level.convert_to_pixels(player_entity.getPosition())
            params.width = 16
            params.height = 24
            character = self.add_game_object(CollectingCharacter(params, i + 1))
            character.add_tag("character")
            self.characters.append(character)

        for bat_entity in self.level.get_entities_by_name("Bat"):
            start_pos = self.level.convert_to_pixels(bat_entity.getPosition())
            end_point = bat_entity.getField("end")
            end_pos = self.level.convert_cells_to_pixels(end_point, entities_layer)
            enemy = self.add_game_object(Enemy(EnemyType.Bat, start_pos, end_pos))
            enemy.add_tag("enemy")

        for drill_entity in self.level.get_entities_by_name("DrillHead"):
            start_pos = self.level.convert_to_pixels(drill_entity.getPosition())
            end_point = drill_entity.getField("end")
            end_pos = self.level.convert_cells_to_pixels(end_point, entities_layer)
            enemy = self.add_game_object(Enemy(EnemyType.DrillHead, start_pos, end_pos))
            enemy.add_tag("enemy")

        for block_entity in self.level.get_entities_by_name("BlockHead"):
            start_pos = self.level.convert_to_pixels(block_entity.getPosition())
            end_point = block_entity.getField("end")
            end_pos = self.level.convert_cells_to_pixels(end_point, entities_layer)
            enemy = self.add_game_object(Enemy(EnemyType.BlockHead, start_pos, end_pos))
            enemy.add_tag("enemy")

        for coin_entity in self.level.get_entities_by_name("Coin"):
            coin_pos = self.level.convert_to_pixels(coin_entity.getPosition())
            coin = self.add_game_object(Coin(coin_pos))
            coin.add_tag("coin")

        self.screen_size = v2(self.window_manager.get_width(), self.window_manager.get_height())
        for _ in self.characters:
            cam = self.add_game_object(SplitCamera(vec_div(self.screen_size, self.scale), self.level.get_size()))
            self.cameras.append(cam)

    def update(self, delta_time: float) -> None:
        """Update camera targets and handle window resizing.

        Args:
            delta_time: Seconds since last frame.

        Returns:
            None
        """
        for idx, camera in enumerate(self.cameras):
            camera.target = self.characters[idx].body.get_position_pixels()

        new_screen_size = v2(float(rl.get_screen_width()), float(rl.get_screen_height()))
        if new_screen_size.x != self.screen_size.x or new_screen_size.y != self.screen_size.y:
            self.screen_size = new_screen_size
            screen_scale = self.window_manager.get_width() / self.screen_size.x
            for camera in self.cameras:
                camera.size = vec_mul(vec_div(self.screen_size, self.scale), screen_scale)
                camera.camera.offset = v2(camera.size.x / 2.0, camera.size.y / 2.0)
                if camera.renderer:
                    rl.unload_render_texture(camera.renderer)
                camera.renderer = rl.load_render_texture(int(camera.size.x), int(camera.size.y))

        # Trigger scene change on Enter key or gamepad start button.
        if rl.is_key_pressed(rl.KEY_ENTER) or rl.is_gamepad_button_pressed(0, rl.GAMEPAD_BUTTON_MIDDLE_RIGHT):
            self.game.go_to_scene_next()

    def draw_scene(self) -> None:
        """Render the scene once per camera and composite the split view.

        Returns:
            None
        """
        for camera in self.cameras:
            camera.draw_begin()
            super().draw_scene()
            camera.draw_end()

        rl.clear_background(rl.MAGENTA)
        for i, camera in enumerate(self.cameras):
            if i == 0:
                camera.draw_texture_pro(0, 0, self.screen_size.x / 2.0, self.screen_size.y / 2.0)
                rl.draw_text_ex(self.font_manager.get_font("Tiny5"),
                           f"Score: {self.characters[0].score}",
                           v2(20.0, 20.0),
                           40.0,
                           2.0,
                           rl.BLACK)
            elif i == 1:
                camera.draw_texture_pro(self.screen_size.x / 2.0, 0, self.screen_size.x / 2.0, self.screen_size.y / 2.0)
                rl.draw_text_ex(self.font_manager.get_font("Tiny5"),
                           f"Score: {self.characters[1].score}",
                           v2(self.screen_size.x / 2.0 + 20.0, 20.0),
                           40.0,
                           2.0,
                           rl.BLACK)
            elif i == 2:
                camera.draw_texture_pro(0, self.screen_size.y / 2.0, self.screen_size.x / 2.0, self.screen_size.y / 2.0)
                rl.draw_text_ex(self.font_manager.get_font("Tiny5"),
                           f"Score: {self.characters[2].score}",
                           v2(20.0, self.screen_size.y / 2.0 + 20.0),
                           40.0,
                           2.0,
                           rl.BLACK)
            elif i == 3:
                camera.draw_texture_pro(self.screen_size.x / 2.0,
                                        self.screen_size.y / 2.0,
                                        self.screen_size.x / 2.0,
                                        self.screen_size.y / 2.0)
                rl.draw_text_ex(self.font_manager.get_font("Tiny5"),
                           f"Score: {self.characters[3].score}",
                           v2(self.screen_size.x / 2.0 + 20.0, self.screen_size.y / 2.0 + 20.0),
                           40.0,
                           2.0,
                           rl.BLACK)

        rl.draw_line_ex(v2(self.screen_size.x / 2.0, 0), v2(self.screen_size.x / 2.0, self.screen_size.y), 4.0, rl.Color(130, 130, 130, 255))
        rl.draw_line_ex(v2(0, self.screen_size.y / 2.0), v2(self.screen_size.x, self.screen_size.y / 2.0), 4.0, rl.Color(130, 130, 130, 255))
