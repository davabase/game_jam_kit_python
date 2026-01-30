from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from Box2D import b2PolygonShape, b2Vec2
import pyray as rl

from engine.framework import GameObject
from engine.math_extensions import v2, vec_sub
from engine.prefabs.components import BodyComponent, PlatformerMovementComponent, PlatformerMovementParams, SpriteComponent
from engine.prefabs.services import PhysicsService


class StaticBox(GameObject):
    """Simple static box collider with optional debug drawing."""
    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        """  init  .
        
        Args:
            x: Parameter.
            y: Parameter.
            width: Parameter.
            height: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.body = None
        self.is_visible = True

    @classmethod
    def from_vectors(cls, position: rl.Vector2, size: rl.Vector2):
        """From vectors.
        
        Args:
            position: Parameter.
            size: Parameter.
        
        Returns:
            Result of the operation.
        """
        return cls(position.x, position.y, size.x, size.y)

    def init(self) -> None:
        """Initialize the object.
        
        Returns:
            None
        """
        physics = self.scene.get_service(PhysicsService)
        world = physics.world
        if not world:
            return
        self.body = world.CreateStaticBody(position=(self.x * physics.pixels_to_meters, self.y * physics.pixels_to_meters))
        shape = b2PolygonShape(box=(self.width / 2.0 * physics.pixels_to_meters,
                                    self.height / 2.0 * physics.pixels_to_meters))
        self.body.CreateFixture(shape=shape)
        self.add_component(BodyComponent(self.body))

    def draw(self) -> None:
        """Draw the object.
        
        Returns:
            None
        """
        if self.is_visible:
            rl.draw_rectangle(int(self.x - self.width / 2.0), int(self.y - self.height / 2.0), int(self.width), int(self.height), rl.Color(0, 121, 241, 255))


class DynamicBox(GameObject):
    """Simple dynamic rigid body box."""
    def __init__(self, x: float, y: float, width: float, height: float, rotation: float = 0.0) -> None:
        """  init  .
        
        Args:
            x: Parameter.
            y: Parameter.
            width: Parameter.
            height: Parameter.
            rotation: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rot_deg = rotation
        self.physics: Optional[PhysicsService] = None
        self.body = None

    @classmethod
    def from_vectors(cls, position: rl.Vector2, size: rl.Vector2, rotation: float = 0.0):
        """From vectors.
        
        Args:
            position: Parameter.
            size: Parameter.
            rotation: Parameter.
        
        Returns:
            Result of the operation.
        """
        return cls(position.x, position.y, size.x, size.y, rotation)

    def init(self) -> None:
        """Initialize the object.
        
        Returns:
            None
        """
        self.physics = self.scene.get_service(PhysicsService)
        world = self.physics.world
        if not world:
            return
        self.body = world.CreateDynamicBody(position=(self.x * self.physics.pixels_to_meters,
                                                      self.y * self.physics.pixels_to_meters),
                                            angle=math.radians(self.rot_deg))
        shape = b2PolygonShape(box=(self.width / 2.0 * self.physics.pixels_to_meters,
                                    self.height / 2.0 * self.physics.pixels_to_meters))
        self.body.CreateFixture(shape=shape, density=1.0, friction=0.3)
        body_component = self.add_component(BodyComponent(self.body))
        self.add_component(SpriteComponent("assets/character_green_idle.png", body_component))

    def draw(self) -> None:
        """Draw the object.
        
        Returns:
            None
        """
        if not self.physics or not self.body:
            return
        pos = self.body.position
        angle = math.degrees(self.body.angle)
        rl.draw_rectangle_pro(rl.Rectangle(self.physics.convert_length_to_pixels(pos.x),
                                   self.physics.convert_length_to_pixels(pos.y),
                                   self.width, self.height),
                         v2(self.width / 2.0, self.height / 2.0),
                         angle,
                         rl.Color(230, 41, 55, 255))


class CameraObject(GameObject):
    """2D camera that follows a target with deadzone and clamp."""
    def __init__(self,
                 size: rl.Vector2,
                 level_size: rl.Vector2 = v2(0.0, 0.0),
                 follow_speed: rl.Vector2 = v2(1000.0, 1000.0),
                 offset_left: float = 70.0,
                 offset_right: float = 70.0,
                 offset_top: float = 40.0,
                 offset_bottom: float = 40.0) -> None:
        super().__init__()

        self.camera = rl.Camera2D()
        self.target = v2(0.0, 0.0)
        self.size = size
        self.level_size = level_size
        self.follow_speed = follow_speed
        self.offset_left = offset_left
        self.offset_right = offset_right
        self.offset_top = offset_top
        self.offset_bottom = offset_bottom

    def init(self) -> None:
        """Initialize the object.
        
        Returns:
            None
        """
        self.camera.zoom = 1.0
        self.camera.offset = v2(self.size.x / 2.0, self.size.y / 2.0)
        self.camera.rotation = 0.0
        self.camera.target = self.target

    def update(self, delta_time: float) -> None:
        """Update the object.
        
        Args:
            delta_time: Parameter.
        
        Returns:
            None
        """
        desired = self.camera.target
        inv_zoom = 1.0 / self.camera.zoom if self.camera.zoom != 0.0 else 1.0
        dz_left_w = self.offset_left * inv_zoom
        dz_right_w = self.offset_right * inv_zoom
        dz_top_w = self.offset_top * inv_zoom
        dz_bottom_w = self.offset_bottom * inv_zoom

        dx = self.target.x - self.camera.target.x
        dy = self.target.y - self.camera.target.y

        if dx < -dz_left_w:
            desired.x = self.target.x + dz_left_w
        elif dx > dz_right_w:
            desired.x = self.target.x - dz_right_w

        if dy < -dz_top_w:
            desired.y = self.target.y + dz_top_w
        elif dy > dz_bottom_w:
            desired.y = self.target.y - dz_bottom_w

        if self.follow_speed.x < 0:
            self.camera.target.x = desired.x
        else:
            self.camera.target.x = self.move_towards(self.camera.target.x, desired.x, self.follow_speed.x * delta_time)

        if self.follow_speed.y < 0:
            self.camera.target.y = desired.y
        else:
            self.camera.target.y = self.move_towards(self.camera.target.y, desired.y, self.follow_speed.y * delta_time)

        half_view = v2(self.size.x / 2.0 * inv_zoom, self.size.y / 2.0 * inv_zoom)
        if self.level_size.x > self.size.x:
            self.camera.target.x = max(half_view.x, min(self.level_size.x - half_view.x, self.camera.target.x))
        if self.level_size.y > self.size.y:
            self.camera.target.y = max(half_view.y, min(self.level_size.y - half_view.y, self.camera.target.y))

    @staticmethod
    def move_towards(current: float, target: float, max_delta: float) -> float:
        """Move towards.
        
        Args:
            current: Parameter.
            target: Parameter.
            max_delta: Parameter.
        
        Returns:
            Result of the operation.
        """
        delta = target - current
        if delta > max_delta:
            return current + max_delta
        if delta < -max_delta:
            return current - max_delta
        return target

    def set_target(self, target: rl.Vector2) -> None:
        """Set target.
        
        Args:
            target: Parameter.
        
        Returns:
            None
        """
        self.target = target

    def set_zoom(self, zoom: float) -> None:
        """Set zoom.
        
        Args:
            zoom: Parameter.
        
        Returns:
            None
        """
        self.camera.zoom = zoom

    def set_rotation(self, angle: float) -> None:
        """Set rotation.
        
        Args:
            angle: Parameter.
        
        Returns:
            None
        """
        self.camera.rotation = angle

    def draw_begin(self) -> None:
        """Draw begin.
        
        Returns:
            None
        """
        rl.begin_mode_2d(self.camera)

    def draw_end(self) -> None:
        """Draw end.
        
        Returns:
            None
        """
        rl.end_mode_2d()

    def draw_debug(self, color: rl.Color = rl.Color(0, 255, 0, 120)) -> None:
        """TODO"""
        inv_zoom = 1.0 / self.camera.zoom if self.camera.zoom != 0.0 else 1.0
        dz_left_w = self.offset_left * inv_zoom
        dz_right_w = self.offset_right * inv_zoom
        dz_top_w = self.offset_top * inv_zoom
        dz_bottom_w = self.offset_bottom * inv_zoom
        rect = rl.Rectangle(self.camera.target.x - dz_left_w,
                         self.camera.target.y - dz_top_w,
                         dz_left_w + dz_right_w,
                         dz_top_w + dz_bottom_w)
        rl.draw_rectangle_lines_ex(rect, 2.0 * inv_zoom, color)

    def screen_to_world(self, point: rl.Vector2) -> rl.Vector2:
        """Convert screen coordinates to world coordinates.
        
        Args:
            point: Parameter.
        
        Returns:
            Result of the operation.
        """
        return rl.get_screen_to_world_2d(point, self.camera)


class SplitCamera(CameraObject):
    """Split-screen camera that renders to a texture."""
    def __init__(self, size: rl.Vector2, level_size: rl.Vector2 = v2(0.0, 0.0),
                 follow_speed: rl.Vector2 = v2(1000.0, 1000.0),
                 offset_left: float = 70.0, offset_right: float = 70.0,
                 offset_top: float = 40.0, offset_bottom: float = 40.0) -> None:
        super().__init__(size, level_size, follow_speed, offset_left, offset_right, offset_top, offset_bottom)
        self.renderer: Optional[rl.RenderTexture] = None

    def init(self) -> None:
        """Initialize the object.
        
        Returns:
            None
        """
        self.renderer = rl.load_render_texture(int(self.size.x), int(self.size.y))
        super().init()

    def draw_begin(self) -> None:
        """Draw begin.
        
        Returns:
            None
        """
        if not self.renderer:
            return
        rl.begin_texture_mode(self.renderer)
        rl.clear_background(rl.WHITE)
        rl.begin_mode_2d(self.camera)

    def draw_end(self) -> None:
        """Draw end.
        
        Returns:
            None
        """
        rl.end_mode_2d()
        rl.end_texture_mode()

    def draw_texture(self, x: float, y: float) -> None:
        """Draw texture.
        
        Args:
            x: Parameter.
            y: Parameter.
        
        Returns:
            None
        """
        if not self.renderer:
            return
        rl.draw_texture_pro(self.renderer.texture,
                       rl.Rectangle(0.0, 0.0, float(self.renderer.texture.width), -float(self.renderer.texture.height)),
                       rl.Rectangle(x, y, float(self.renderer.texture.width), float(self.renderer.texture.height)),
                       v2(0.0, 0.0),
                       0.0,
                       rl.WHITE)

    def draw_texture_pro(self, x: float, y: float, width: float, height: float) -> None:
        """Draw texture pro.
        
        Args:
            x: Parameter.
            y: Parameter.
            width: Parameter.
            height: Parameter.
        
        Returns:
            None
        """
        if not self.renderer:
            return
        rl.draw_texture_pro(self.renderer.texture,
                       rl.Rectangle(0.0, 0.0, float(self.renderer.texture.width), -float(self.renderer.texture.height)),
                       rl.Rectangle(x, y, width, height),
                       v2(0.0, 0.0),
                       0.0,
                       rl.WHITE)

    def screen_to_world_with_offset(self, draw_position: rl.Vector2, point: rl.Vector2) -> rl.Vector2:
        """Convert screen coordinates to world coordinates.
        
        Args:
            draw_position: Parameter.
            point: Parameter.
        
        Returns:
            Result of the operation.
        """
        local_point = vec_sub(point, draw_position)
        return rl.get_screen_to_world_2d(local_point, self.camera)


@dataclass
class CharacterParams:
    """Parameter bag for a platformer character."""
    width: float = 24.0
    height: float = 40.0
    position: rl.Vector2 = v2(0.0, 0.0)
    friction: float = 0.0
    restitution: float = 0.0
    density: float = 1.0


class PlatformerCharacter(GameObject):
    """Simple platformer character with movement."""
    def __init__(self, params: CharacterParams, gamepad: int = 0) -> None:
        """  init  .
        
        Args:
            params: Parameter.
            gamepad: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.p = params
        self.physics: Optional[PhysicsService] = None
        self.body: Optional[BodyComponent] = None
        self.movement: Optional[PlatformerMovementComponent] = None
        self.gamepad = gamepad

    def init(self) -> None:
        """Initialize the object.
        
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
                                           fixedRotation=True)
            body.userData = self
            shape = b2PolygonShape(box=(self.physics.convert_length_to_meters(self.p.width / 2.0),
                                        self.physics.convert_length_to_meters(self.p.height / 2.0)))
            body.CreateFixture(shape=shape, density=self.p.density, friction=self.p.friction, restitution=self.p.restitution)
            component.body = body

        self.body = self.add_component(BodyComponent(build=build_body))
        params = PlatformerMovementParams()
        params.width = self.p.width
        params.height = self.p.height
        self.movement = self.add_component(PlatformerMovementComponent(params))

    def update(self, delta_time: float) -> None:

        """Update the object.
        
        Args:
            delta_time: Parameter.
        
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

        if self.movement:
            self.movement.set_input(move_x, jump_pressed, jump_held)

    def draw(self) -> None:

        """Draw the object.
        
        Returns:
            None
        """
        if not self.body or not self.movement:
            return
        color = rl.GREEN if self.movement.grounded else rl.BLUE
        pos = self.body.get_position_pixels()
        rl.draw_rectangle_pro(rl.Rectangle(pos.x, pos.y, self.p.width, self.p.height),
                         v2(self.p.width / 2.0, self.p.height / 2.0),
                         0.0,
                         color)
