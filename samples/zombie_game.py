"""Demonstration of a top-down shooter with light masking."""

from __future__ import annotations

import math
from typing import List

from Box2D import b2CircleShape, b2Vec2
import pyray as rl

from engine.framework import GameObject, Scene
from engine.math_extensions import vec_add, vec_mul, vec_sub, v2
from engine.prefabs.components import (BodyComponent, MultiComponent, SoundComponent,
                                       SpriteComponent, TopDownMovementComponent,
                                       TopDownMovementParams)
from engine.prefabs.managers import FontManager
from engine.prefabs.services import LevelService, PhysicsService, SoundService, TextureService

RLGL_SRC_ALPHA = 0x0302
RLGL_MIN = 0x8007


class Bullet(GameObject):
    """Projectile fired by a player character."""
    def __init__(self) -> None:
        """Prepare bullet component references and cached services.

        Returns:
            None
        """
        super().__init__()
        self.physics: PhysicsService = None  # type: ignore[assignment]
        self.body: BodyComponent = None  # type: ignore[assignment]
        self.sprite: SpriteComponent = None  # type: ignore[assignment]
        self.hit_sound: SoundComponent = None  # type: ignore[assignment]
        self.speed = 800.0

    def init(self) -> None:
        """Create the bullet body, sprite, and hit sound.

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
            body = world.CreateDynamicBody(position=(self.physics.convert_to_meters(v2(-1000.0, -1000.0)).x,
                                                     self.physics.convert_to_meters(v2(-1000.0, -1000.0)).y),
                                           bullet=True)
            body.userData = self
            shape = b2CircleShape(radius=self.physics.convert_length_to_meters(8.0))
            body.CreateFixture(shape=shape, density=0.25, friction=0.0, restitution=0.0)
            component.body = body

        self.body = self.add_component(BodyComponent(build=build_body))
        self.sprite = self.add_component(SpriteComponent("assets/zombie_shooter/bullet.png", self.body))
        self.hit_sound = self.add_component(SoundComponent("assets/sounds/hit.wav"))

    def update(self, delta_time: float) -> None:
        """Handle collisions and deactivate on impact.

        Args:
            delta_time: Seconds since last frame.

        Returns:
            None
        """
        for contact_body in self.body.get_contacts():
            self.is_active = False
            self.body.set_position(v2(-1000.0, -1000.0))
            self.body.set_velocity(v2(0.0, 0.0))
            other = contact_body.userData
            if other and other.has_tag("zombie"):
                self.hit_sound.play()
                other.is_active = False
                zombie_body = other.get_component(BodyComponent)
                if zombie_body:
                    zombie_body.set_position(v2(-1000.0, -1000.0))
                    zombie_body.set_velocity(v2(0.0, 0.0))
                    zombie_body.disable()
                zombie_sprite = other.get_component(SpriteComponent)
                if zombie_sprite:
                    zombie_sprite.set_position(v2(-1000.0, -1000.0))
                break


class TopDownCharacter(GameObject):
    """Top-down character controlled by player input."""
    def __init__(self, position: rl.Vector2, bullets: List["Bullet"], player_num: int) -> None:
        """Store spawn data, shared bullet pool, and player index.

        Args:
            position: Spawn position in pixels.
            bullets: Shared list of Bullet objects to reuse.
            player_num: Index used for controls and UI.

        Returns:
            None
        """
        super().__init__()
        self.position = position
        self.bullets = bullets
        self.player_num = player_num
        self.health = 10
        self.contact_timer = 1.0
        self.contact_cooldown = 0.3
        self.body: BodyComponent = None  # type: ignore[assignment]
        self.physics: PhysicsService = None  # type: ignore[assignment]
        self.sprite: SpriteComponent = None  # type: ignore[assignment]
        self.movement: TopDownMovementComponent = None  # type: ignore[assignment]
        self.sounds: MultiComponent = None  # type: ignore[assignment]
        self.shoot_sound: SoundComponent = None  # type: ignore[assignment]

    def init(self) -> None:
        """Create body, movement, sounds, and sprite.

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
            body = world.CreateDynamicBody(position=(self.physics.convert_to_meters(self.position).x,
                                                     self.physics.convert_to_meters(self.position).y),
                                           fixedRotation=True)
            body.userData = self
            shape = b2CircleShape(radius=self.physics.convert_length_to_meters(16.0))
            body.CreateFixture(shape=shape, density=1.0)
            component.body = body

        self.body = self.add_component(BodyComponent(build=build_body))

        params = TopDownMovementParams()
        params.accel = 5000.0
        params.friction = 5000.0
        params.max_speed = 350.0
        self.movement = self.add_component(TopDownMovementComponent(params))

        self.sounds = self.add_component(MultiComponent())
        self.shoot_sound = self.sounds.add_component("shoot", SoundComponent, "assets/sounds/shoot.wav")

        self.sprite = self.add_component(SpriteComponent(f"assets/zombie_shooter/player_{self.player_num + 1}.png"))

    def update(self, delta_time: float) -> None:
        """Handle movement, shooting, and damage over time.

        Args:
            delta_time: Seconds since last frame.

        Returns:
            None
        """
        move = v2(0.0, 0.0)
        move = v2(rl.get_gamepad_axis_movement(self.player_num, rl.GAMEPAD_AXIS_LEFT_X),
                  rl.get_gamepad_axis_movement(self.player_num, rl.GAMEPAD_AXIS_LEFT_Y))

        if rl.is_key_down(rl.KEY_W) or rl.is_gamepad_button_down(self.player_num, rl.GAMEPAD_BUTTON_LEFT_FACE_UP):
            move.y -= 1.0
        if rl.is_key_down(rl.KEY_S) or rl.is_gamepad_button_down(self.player_num, rl.GAMEPAD_BUTTON_LEFT_FACE_DOWN):
            move.y += 1.0
        if rl.is_key_down(rl.KEY_A) or rl.is_gamepad_button_down(self.player_num, rl.GAMEPAD_BUTTON_LEFT_FACE_LEFT):
            move.x -= 1.0
        if rl.is_key_down(rl.KEY_D) or rl.is_gamepad_button_down(self.player_num, rl.GAMEPAD_BUTTON_LEFT_FACE_RIGHT):
            move.x += 1.0

        self.movement.set_input(move.x, move.y)
        self.sprite.set_position(self.body.get_position_pixels())
        self.sprite.set_rotation(self.movement.facing_dir)

        if rl.is_key_pressed(rl.KEY_SPACE) or rl.is_gamepad_button_pressed(self.player_num, rl.GAMEPAD_BUTTON_RIGHT_FACE_RIGHT):
            for bullet in self.bullets:
                if not bullet.is_active:
                    self.shoot_sound.play()
                    char_pos = self.body.get_position_pixels()
                    shoot_dir = v2(math.cos(math.radians(self.movement.facing_dir)),
                                   math.sin(math.radians(self.movement.facing_dir)))
                    bullet_start = v2(char_pos.x + shoot_dir.x * 48.0, char_pos.y + shoot_dir.y * 48.0)
                    bullet.body.set_position(bullet_start)
                    bullet.body.set_rotation(self.movement.facing_dir + 90.0)
                    bullet.body.set_velocity(v2(shoot_dir.x * bullet.speed, shoot_dir.y * bullet.speed))
                    bullet.is_active = True
                    break

        for contact_body in self.body.get_contacts():
            other = contact_body.userData
            if other and other.has_tag("zombie"):
                if self.contact_timer > 0.0:
                    self.contact_timer -= delta_time
                if self.contact_timer <= 0.0:
                    self.health -= 1
                    self.contact_timer = self.contact_cooldown
                    if self.health <= 0:
                        self.is_active = False
                        self.body.set_position(v2(-1000.0, -1000.0))
                        self.body.set_velocity(v2(0.0, 0.0))


class Zombie(GameObject):
    """Enemy that chases the closest player."""
    def __init__(self, players: List[TopDownCharacter]) -> None:
        """Store the list of players to chase.

        Args:
            players: Player characters to target.

        Returns:
            None
        """
        super().__init__()
        self.players = players
        self.body: BodyComponent = None  # type: ignore[assignment]
        self.physics: PhysicsService = None  # type: ignore[assignment]
        self.sprite: SpriteComponent = None  # type: ignore[assignment]
        self.movement: TopDownMovementComponent = None  # type: ignore[assignment]

    def init(self) -> None:
        """Create body, movement, and sprite (starts inactive).

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
            body = world.CreateDynamicBody(position=(self.physics.convert_to_meters(v2(-1000.0, -1000.0)).x,
                                                     self.physics.convert_to_meters(v2(-1000.0, -1000.0)).y),
                                           fixedRotation=True)
            body.userData = self
            shape = b2CircleShape(radius=self.physics.convert_length_to_meters(16.0))
            body.CreateFixture(shape=shape, density=1.0)
            body.active = False
            component.body = body

        self.body = self.add_component(BodyComponent(build=build_body))

        params = TopDownMovementParams()
        params.accel = 5000.0
        params.friction = 5000.0
        params.max_speed = 100.0
        self.movement = self.add_component(TopDownMovementComponent(params))

        self.sprite = self.add_component(SpriteComponent("assets/zombie_shooter/zombie.png"))

    def update(self, delta_time: float) -> None:
        """Move toward the closest player and update sprite.

        Args:
            delta_time: Seconds since last frame.

        Returns:
            None
        """
        closest_pos = v2(0.0, 0.0)
        closest_dist_sq = float("inf")
        for player in self.players:
            player_pos = player.body.get_position_pixels()
            to_player = vec_sub(player_pos, self.body.get_position_pixels())
            dist_sq = to_player.x * to_player.x + to_player.y * to_player.y
            if dist_sq < closest_dist_sq:
                closest_dist_sq = dist_sq
                closest_pos = player_pos
        to_closest = vec_sub(closest_pos, self.body.get_position_pixels())
        length = math.sqrt(to_closest.x * to_closest.x + to_closest.y * to_closest.y)
        if length > 0.0:
            to_closest.x /= length
            to_closest.y /= length
        self.movement.set_input(to_closest.x, to_closest.y)
        self.sprite.set_position(self.body.get_position_pixels())
        self.sprite.set_rotation(self.movement.facing_dir)


class Spawner(GameObject):
    """Spawner that activates zombies from a pool."""
    def __init__(self, position: rl.Vector2, size: rl.Vector2, zombies: List[Zombie]) -> None:
        """Configure spawn region and zombie pool.

        Args:
            position: Center of the spawn rectangle in pixels.
            size: Size of the spawn rectangle in pixels.
            zombies: Pool of zombie objects to activate.

        Returns:
            None
        """
        super().__init__()
        self.spawn_timer = 0.0
        self.spawn_interval = 1.0
        self.position = vec_sub(position, vec_mul(size, 0.5))
        self.size = size
        self.zombie_pool = zombies

    def update(self, delta_time: float) -> None:
        """Spawn zombies at an interval within a rectangle.

        Args:
            delta_time: Seconds since last frame.

        Returns:
            None
        """
        self.spawn_timer -= delta_time
        if self.spawn_timer <= 0.0:
            self.spawn_timer = self.spawn_interval
            x = self.position.x + float(rl.get_random_value(0, int(self.size.x)))
            y = self.position.y + float(rl.get_random_value(0, int(self.size.y)))
            spawn_pos = v2(x, y)
            for zombie in self.zombie_pool:
                if not zombie.is_active:
                    zombie.body.set_position(spawn_pos)
                    zombie.is_active = True
                    zombie.body.enable()
                    return


class ZombieScene(Scene):
    """Scene for the zombie shooter game."""
    def __init__(self) -> None:
        """Initialize scene storage for services, actors, and render targets.

        Returns:
            None
        """
        super().__init__()
        self.font_manager: FontManager = None  # type: ignore[assignment]
        self.physics: PhysicsService = None  # type: ignore[assignment]
        self.level: LevelService = None  # type: ignore[assignment]
        self.renderer: rl.RenderTexture = None  # type: ignore[assignment]
        self.light_map: rl.RenderTexture = None  # type: ignore[assignment]
        self.light_texture: rl.Texture2D = None  # type: ignore[assignment]
        self.bullets: List[Bullet] = []
        self.characters: List[TopDownCharacter] = []
        self.zombies: List[Zombie] = []

    def init_services(self) -> None:
        """Register services required by the scene.

        Returns:
            None
        """
        self.add_service(TextureService)
        self.add_service(SoundService)
        self.physics = self.add_service(PhysicsService, b2Vec2(0.0, 0.0))
        collision_names = ["walls", "obstacles"]
        self.level = self.add_service(LevelService, "assets/levels/top_down.ldtk", "Level", collision_names)
        self.font_manager = self.game.get_manager(FontManager)

    def init(self) -> None:
        """Create pools, characters, spawner, and render textures.

        Returns:
            None
        """
        for _ in range(100):
            bullet = self.add_game_object(Bullet())
            bullet.is_active = False
            self.bullets.append(bullet)

        player_entities = self.level.get_entities_by_name("Start")
        for i, player_entity in enumerate(player_entities[:4]):
            position = self.level.convert_to_pixels(player_entity.getPosition())
            character = self.add_game_object(TopDownCharacter(position, self.bullets, i))
            character.add_tag("player")
            self.characters.append(character)

        for _ in range(100):
            zombie = self.add_game_object(Zombie(self.characters))
            zombie.is_active = False
            zombie.add_tag("zombie")
            self.zombies.append(zombie)

        spawn_entity = self.level.get_entities_by_name("Spawn")[0]
        spawn_position = self.level.convert_to_pixels(spawn_entity.getPosition())
        spawn_size = self.level.convert_to_pixels(spawn_entity.getSize())
        self.add_game_object(Spawner(spawn_position, spawn_size, self.zombies))

        self.level.set_layer_visibility("Foreground", False)

        self.renderer = rl.load_render_texture(int(self.level.get_size().x), int(self.level.get_size().y))
        self.light_map = rl.load_render_texture(int(self.level.get_size().x), int(self.level.get_size().y))
        self.light_texture = self.get_service(TextureService).get_texture("assets/zombie_shooter/light.png")

    def update(self, delta_time: float) -> None:
        # Trigger scene change on Enter key or gamepad start button.
        if rl.is_key_pressed(rl.KEY_ENTER) or rl.is_gamepad_button_pressed(0, rl.GAMEPAD_BUTTON_MIDDLE_RIGHT):
            self.game.go_to_scene_next()

    def draw_scene(self) -> None:
        """Build light mask and render the final frame.

        Returns:
            None
        """

        """Draw the scene.

        Returns:
            None
        """
        rl.begin_texture_mode(self.light_map)
        rl.clear_background(rl.BLACK)
        rl.rl_set_blend_factors(RLGL_SRC_ALPHA, RLGL_SRC_ALPHA, RLGL_MIN)
        rl.rl_set_blend_mode(rl.BLEND_CUSTOM)

        for i in range(min(4, len(self.characters))):
            pos = self.characters[i].body.get_position_pixels()
            rl.draw_texture(self.light_texture,
                        int(pos.x - self.light_texture.width / 2),
                        int(pos.y - self.light_texture.height / 2),
                        rl.WHITE)

        rl.rl_draw_render_batch_active()
        rl.rl_set_blend_mode(rl.BLEND_ALPHA)
        rl.end_texture_mode()

        rl.begin_texture_mode(self.renderer)
        rl.clear_background(rl.Color(255, 0, 255, 255))
        super().draw_scene()
        self.level.draw_layer("Foreground")
        rl.draw_texture_pro(self.light_map.texture,
                       rl.Rectangle(0.0, 0.0, float(self.light_map.texture.width), -float(self.light_map.texture.height)),
                       rl.Rectangle(0.0, 0.0, float(self.light_map.texture.width), float(self.light_map.texture.height)),
                       v2(0.0, 0.0),
                       0.0,
                       rl.color_alpha(rl.WHITE, 0.92))
        rl.draw_rectangle(10, 10, 210, 210, rl.color_alpha(rl.WHITE, 0.3))
        health_lines = [f"Health: {char.health}" for char in self.characters[:4]]
        rl.draw_text_ex(self.font_manager.get_font("Roboto"),
                   "\n".join(health_lines),
                   v2(20.0, 20.0),
                   45.0,
                   1.0,
                   rl.Color(230, 41, 55, 255))
        rl.end_texture_mode()

        rl.draw_texture_pro(self.renderer.texture,
                       rl.Rectangle(0.0, 0.0, float(self.renderer.texture.width), -float(self.renderer.texture.height)),
                       rl.Rectangle(0.0, 0.0, float(rl.get_screen_width()), float(rl.get_screen_height())),
                       v2(0.0, 0.0),
                       0.0,
                       rl.WHITE)
