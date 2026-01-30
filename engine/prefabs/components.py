from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from Box2D import (b2Body, b2CircleShape, b2FixtureDef, b2PolygonShape,
                   b2Vec2)
import pyray as rl

from engine.framework import Component
from engine.math_extensions import vec_add, vec_div, vec_len, vec_mul, vec_normalize, vec_sub, v2
from engine.raycasts import raycast_closest
from engine.prefabs.managers import FontManager
from engine.prefabs.services import PhysicsService, SoundService, TextureService


class MultiComponent(Component):
    """Container component that allows multiple components of the same type."""
    def __init__(self) -> None:
        """  init  .
        
        Returns:
            None
        """
        super().__init__()
        self.components: Dict[str, Component] = {}

    def init(self) -> None:
        """Initialize all contained components.

        Returns:
            None
        """
        for component in self.components.values():
            component.init()

    def update(self, delta_time: float) -> None:
        """Update all contained components.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        for component in self.components.values():
            component.update(delta_time)

    def draw(self) -> None:
        """Draw all contained components.

        Returns:
            None
        """
        for component in self.components.values():
            component.draw()

    def add_component(self, name: str, component_or_cls: Any, *args: Any, **kwargs: Any) -> Component:
        """Add a component under a name.

        Args:
            name: Component name key.
            component_or_cls: Component instance or class.
            *args: Positional args forwarded to constructor.
            **kwargs: Keyword args forwarded to constructor.

        Returns:
            The component instance added.
        """
        if isinstance(component_or_cls, Component):
            component = component_or_cls
        else:
            component = component_or_cls(*args, **kwargs)
        component.owner = self.owner
        self.components[name] = component
        return component

    def get_component(self, name: str) -> Optional[Component]:
        """Get a component by name.

        Args:
            name: Component name key.

        Returns:
            The component if present, otherwise None.
        """
        return self.components.get(name)


class TextComponent(Component):
    """Component for rendering text. Depends on FontManager."""
    def __init__(self, text: str, font_name: str = "default", font_size: int = 20, color: rl.Color = rl.WHITE) -> None:
        """  init  .
        
        Args:
            text: Parameter.
            font_name: Parameter.
            font_size: Parameter.
            color: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.font_manager: Optional[FontManager] = None
        self.text = text
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.position = v2(0.0, 0.0)
        self.rotation = 0.0

    def init(self) -> None:
        """Resolve FontManager from the owning scene.

        Returns:
            None
        """
        if self.owner and self.owner.scene and self.owner.scene.game:
            self.font_manager = self.owner.scene.game.get_manager(FontManager)

    def draw(self) -> None:
        """Draw the text if a font is available.

        Returns:
            None
        """
        if not self.font_manager:
            return
        rl.draw_text_ex(self.font_manager.get_font(self.font_name),
                   self.text,
                   self.position,
                   float(self.font_size),
                   1.0,
                   self.color)

    def set_text(self, text: str) -> None:
        """Set the displayed text.

        Args:
            text: New text string.

        Returns:
            None
        """
        self.text = text

    def set_color(self, color: rl.Color) -> None:
        """Set the text color.

        Args:
            color: Raylib color.

        Returns:
            None
        """
        self.color = color

    def set_font_size(self, font_size: int) -> None:
        """Set the font size.

        Args:
            font_size: New font size.

        Returns:
            None
        """
        self.font_size = font_size

    def set_font(self, font_name: str) -> None:
        """Set the font by name.

        Args:
            font_name: Registered font name.

        Returns:
            None
        """
        self.font_name = font_name

    def set_position(self, position: rl.Vector2) -> None:
        """Set the text position.

        Args:
            position: Vector2 in pixels.

        Returns:
            None
        """
        self.position = position

    def set_rotation(self, rotation: float) -> None:
        """Set the text rotation.

        Args:
            rotation: Rotation in degrees.

        Returns:
            None
        """
        self.rotation = rotation


class SoundComponent(Component):
    """Component for playing sounds. Depends on SoundService."""
    def __init__(self, filename: str, volume: float = 1.0, pitch: float = 1.0, pan: float = 0.5) -> None:
        """  init  .
        
        Args:
            filename: Parameter.
            volume: Parameter.
            pitch: Parameter.
            pan: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.filename = filename
        self.sound = None
        self.volume = volume
        self.pitch = pitch
        self.pan = pan

    def init(self) -> None:
        """Load the sound from SoundService.

        Returns:
            None
        """
        if self.owner and self.owner.scene:
            sound_service = self.owner.scene.get_service(SoundService)
            self.sound = sound_service.get_sound(self.filename)

    def play(self) -> None:
        """Play the sound.

        Returns:
            None
        """
        if self.sound:
            rl.play_sound(self.sound)

    def stop(self) -> None:
        """Stop the sound.

        Returns:
            None
        """
        if self.sound:
            rl.stop_sound(self.sound)

    def set_volume(self, volume: float) -> None:
        """Set playback volume.

        Args:
            volume: Volume scalar.

        Returns:
            None
        """
        self.volume = volume
        if self.sound:
            rl.set_sound_volume(self.sound, volume)

    def set_pitch(self, pitch: float) -> None:
        """Set playback pitch.

        Args:
            pitch: Pitch scalar.

        Returns:
            None
        """
        self.pitch = pitch
        if self.sound:
            rl.set_sound_pitch(self.sound, pitch)

    def set_pan(self, pan: float) -> None:
        """Set playback pan.

        Args:
            pan: Pan value from 0.0 (left) to 1.0 (right).

        Returns:
            None
        """
        self.pan = pan
        if self.sound:
            rl.set_sound_pan(self.sound, pan)

    def is_playing(self) -> bool:
        """Check if the sound is currently playing.

        Returns:
            True if playing, otherwise False.
        """
        return bool(self.sound and rl.is_sound_playing(self.sound))


class BodyComponent(Component):
    """Component that owns a Box2D body. Depends on PhysicsService."""
    def __init__(self, body: Optional[b2Body] = None, build: Optional[Any] = None) -> None:
        """  init  .
        
        Args:
            body: Parameter.
            build: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.body = body
        self.build = build
        self.physics: Optional[PhysicsService] = None

    def init(self) -> None:
        """Resolve PhysicsService and build the body if provided.

        Returns:
            None
        """
        if not self.owner or not self.owner.scene:
            return
        self.physics = self.owner.scene.get_service(PhysicsService)
        if self.build:
            self.build(self)

    def enable(self) -> None:
        """Enable the body in the physics simulation.

        Returns:
            None
        """
        if self.body:
            self.body.awake = True
            self.body.active = True

    def disable(self) -> None:
        """Disable the body in the physics simulation.

        Returns:
            None
        """
        if self.body:
            self.body.active = False

    def get_position_meters(self) -> b2Vec2:
        """Get position in meters.

        Returns:
            b2Vec2 position in meters.
        """
        return self.body.position if self.body else b2Vec2(0.0, 0.0)

    def get_position_pixels(self) -> rl.Vector2:
        """Get position in pixels.

        Returns:
            Vector2 position in pixels.
        """
        if not self.physics or not self.body:
            return v2(0.0, 0.0)
        pos = self.physics.convert_to_pixels(self.body.position)
        return v2(pos.x, pos.y)

    def set_position(self, pos) -> None:
        """Set position (meters if b2Vec2, else pixels).

        Args:
            pos: b2Vec2 in meters or Vector2 in pixels.

        Returns:
            None
        """
        if not self.body:
            return
        if isinstance(pos, b2Vec2):
            self.body.position = pos
        else:
            if not self.physics:
                return
            self.body.position = self.physics.convert_to_meters(pos)

    def set_rotation(self, degrees: float) -> None:
        """Set rotation in degrees.

        Args:
            degrees: Rotation in degrees.

        Returns:
            None
        """
        if self.body:
            self.body.angle = math.radians(degrees)

    def get_velocity_meters(self) -> b2Vec2:
        """Get linear velocity in meters/sec.

        Returns:
            b2Vec2 velocity in meters/sec.
        """
        return self.body.linearVelocity if self.body else b2Vec2(0.0, 0.0)

    def get_velocity_pixels(self) -> rl.Vector2:
        """Get linear velocity in pixels/sec.

        Returns:
            Vector2 velocity in pixels/sec.
        """
        if not self.physics or not self.body:
            return v2(0.0, 0.0)
        vel = self.physics.convert_to_pixels(self.body.linearVelocity)
        return v2(vel.x, vel.y)

    def set_velocity(self, vel) -> None:
        """Set linear velocity (meters if b2Vec2, else pixels).

        Args:
            vel: b2Vec2 in meters/sec or Vector2 in pixels/sec.

        Returns:
            None
        """
        if not self.body:
            return
        if isinstance(vel, b2Vec2):
            self.body.linearVelocity = vel
        else:
            if not self.physics:
                return
            self.body.linearVelocity = self.physics.convert_to_meters(vel)

    def get_rotation(self) -> float:
        """Get rotation in degrees.

        Returns:
            Rotation in degrees.
        """
        return math.degrees(self.body.angle) if self.body else 0.0

    def get_contacts(self) -> List[b2Body]:
        """Get bodies currently touching this body.

        Returns:
            List of bodies in contact.
        """
        if not self.body:
            return []
        contacts: List[b2Body] = []
        for edge in self.body.contacts:
            contact = edge.contact
            if contact.touching:
                other = edge.other
                if other not in contacts:
                    contacts.append(other)
        return contacts

    def get_sensor_overlaps(self) -> List[b2Body]:
        """Get bodies overlapping sensor fixtures on this body.

        Returns:
            List of bodies overlapping sensor fixtures.
        """
        if not self.body:
            return []
        contacts: List[b2Body] = []
        for edge in self.body.contacts:
            contact = edge.contact
            if not contact.touching:
                continue
            fixture_a = contact.fixtureA
            fixture_b = contact.fixtureB
            if fixture_a.body == self.body and fixture_a.sensor:
                if fixture_b.body not in contacts:
                    contacts.append(fixture_b.body)
            elif fixture_b.body == self.body and fixture_b.sensor:
                if fixture_a.body not in contacts:
                    contacts.append(fixture_a.body)
        return contacts


class SpriteComponent(Component):
    """Component for rendering a sprite. Depends on TextureService."""
    def __init__(self, filename: str, body: Optional[BodyComponent] = None) -> None:
        """  init  .
        
        Args:
            filename: Parameter.
            body: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.filename = filename
        self.body = body
        self.sprite: Optional[rl.Texture2D] = None
        self.position = v2(0.0, 0.0)
        self.rotation = 0.0
        self.scale = 1.0
        self.tint = rl.WHITE
        self.is_active = True

    def init(self) -> None:
        """Load the sprite texture via TextureService.

        Returns:
            None
        """
        if self.owner and self.owner.scene:
            texture_service = self.owner.scene.get_service(TextureService)
            self.sprite = texture_service.get_texture(self.filename)

    def draw(self) -> None:
        """Draw the sprite if active.

        Returns:
            None
        """
        if not self.is_active or not self.sprite:
            return
        if self.body:
            self.position = self.body.get_position_pixels()
            self.rotation = self.body.get_rotation()
        source = rl.Rectangle(0.0, 0.0, float(self.sprite.width), float(self.sprite.height))
        dest = rl.Rectangle(self.position.x, self.position.y,
                         float(self.sprite.width) * self.scale,
                         float(self.sprite.height) * self.scale)
        origin = v2(float(self.sprite.width) / 2.0 * self.scale,
                    float(self.sprite.height) / 2.0 * self.scale)
        rl.draw_texture_pro(self.sprite, source, dest, origin, self.rotation, self.tint)

    def set_position(self, position: rl.Vector2) -> None:
        """Set the sprite position in pixels.

        Args:
            position: Vector2 position.

        Returns:
            None
        """
        self.position = position

    def set_rotation(self, rotation: float) -> None:
        """Set the sprite rotation in degrees.

        Args:
            rotation: Rotation in degrees.

        Returns:
            None
        """
        self.rotation = rotation

    def set_scale(self, scale: float) -> None:
        """Set the sprite scale.

        Args:
            scale: Scale multiplier.

        Returns:
            None
        """
        self.scale = scale

    def set_tint(self, tint: rl.Color) -> None:
        """Set the sprite tint color.

        Args:
            tint: Raylib color.

        Returns:
            None
        """
        self.tint = tint

    def set_active(self, active: bool) -> None:
        """Enable or disable sprite rendering.

        Args:
            active: True to render, False to hide.

        Returns:
            None
        """
        self.is_active = active


class Animation:
    """Frame-based animation helper."""
    def __init__(self, frames: List[rl.Texture2D], fps: float = 15.0, loop: bool = True) -> None:
        """  init  .
        
        Args:
            frames: Parameter.
            fps: Parameter.
            loop: Parameter.
        
        Returns:
            None
        """
        self.frames = frames
        self.fps = fps
        self.frame_timer = 1.0 / fps if fps > 0 else 0.0
        self.loop = loop
        self.current_frame = 0
        self.playing = True
        self.is_active = True

    @classmethod
    def from_files(cls, texture_service: TextureService, filenames: List[str], fps: float = 15.0, loop: bool = True):
        """From files.
        
        Args:
            texture_service: Parameter.
            filenames: Parameter.
            fps: Parameter.
            loop: Parameter.
        
        Returns:
            Result of the operation.
        """
        frames = [texture_service.get_texture(name) for name in filenames]
        return cls(frames, fps, loop)

    def update(self, delta_time: float) -> None:
        """Advance the animation by delta time.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        if not self.frames or not self.playing or not self.is_active or self.fps <= 0:
            return
        self.frame_timer -= delta_time
        if self.frame_timer <= 0.0:
            self.frame_timer = 1.0 / self.fps
            self.current_frame += 1
        if self.current_frame > len(self.frames) - 1:
            self.current_frame = 0 if self.loop else len(self.frames) - 1

    def draw(self, position: rl.Vector2, rotation: float = 0.0, tint: rl.Color = rl.WHITE) -> None:
        """Draw the animation at a position.

        Args:
            position: Position in pixels.
            rotation: Rotation in degrees.
            tint: Color tint.

        Returns:
            None
        """
        if not self.is_active or not self.frames:
            return
        sprite = self.frames[self.current_frame]
        rl.draw_texture_pro(sprite,
                       rl.Rectangle(0.0, 0.0, float(sprite.width), float(sprite.height)),
                       rl.Rectangle(position.x, position.y, float(sprite.width), float(sprite.height)),
                       v2(float(sprite.width) / 2.0, float(sprite.height) / 2.0),
                       rotation,
                       tint)

    def draw_with_origin(self, position: rl.Vector2, origin: rl.Vector2, rotation: float = 0.0,
                         scale: float = 1.0, flip_x: bool = False, flip_y: bool = False,
                         tint: rl.Color = rl.WHITE) -> None:
        """Draw the animation with origin, scale, and flip options.

        Args:
            position: Position in pixels.
            origin: Origin for rotation/scaling.
            rotation: Rotation in degrees.
            scale: Scale multiplier.
            flip_x: True to flip horizontally.
            flip_y: True to flip vertically.
            tint: Color tint.

        Returns:
            None
        """
        if not self.is_active or not self.frames:
            return
        sprite = self.frames[self.current_frame]
        src = rl.Rectangle(0.0, 0.0,
                        float(sprite.width) * (-1.0 if flip_x else 1.0),
                        float(sprite.height) * (-1.0 if flip_y else 1.0))
        dest = rl.Rectangle(position.x, position.y,
                         float(sprite.width) * scale,
                         float(sprite.height) * scale)
        rl.draw_texture_pro(sprite, src, dest, vec_mul(origin, scale), rotation, tint)

    def play(self) -> None:
        """Start or resume playback.

        Returns:
            None
        """
        self.playing = True

    def pause(self) -> None:
        """Pause playback.

        Returns:
            None
        """
        self.playing = False

    def stop(self) -> None:
        """Stop playback and reset to the first frame.

        Returns:
            None
        """
        self.playing = False
        self.frame_timer = 1.0 / self.fps if self.fps > 0 else 0.0
        self.current_frame = 0


class AnimationController(Component):
    """Component for controlling animations. Depends on TextureService."""
    def __init__(self, body: Optional[BodyComponent] = None) -> None:
        """  init  .
        
        Args:
            body: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.animations: Dict[str, Animation] = {}
        self.current_animation: Optional[Animation] = None
        self.position = v2(0.0, 0.0)
        self.rotation = 0.0
        self.origin = v2(0.0, 0.0)
        self.scale = 1.0
        self.flip_x = False
        self.flip_y = False
        self.body = body

    def update(self, delta_time: float) -> None:
        """Update the current animation.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        if self.current_animation:
            self.current_animation.update(delta_time)

    def draw(self) -> None:
        """Draw the current animation.

        Returns:
            None
        """
        if self.body:
            self.position = self.body.get_position_pixels()
            self.rotation = self.body.get_rotation()
        if self.current_animation:
            self.current_animation.draw_with_origin(self.position, self.origin, self.rotation, self.scale,
                                                    self.flip_x, self.flip_y)

    def add_animation(self, name: str, animation: Animation) -> None:
        """Add an Animation to the controller.

        Args:
            name: Animation name.
            animation: Animation instance.

        Returns:
            None
        """
        self.animations[name] = animation
        if not self.current_animation:
            self.current_animation = animation
            sprite = animation.frames[animation.current_frame]
            self.origin = v2(float(sprite.width) / 2.0, float(sprite.height) / 2.0)

    def add_animation_from_files(self, name: str, filenames: List[str], fps: float = 15.0, loop: bool = True) -> Animation:
        """Create an Animation from files and add it.

        Args:
            name: Animation name.
            filenames: List of frame image paths.
            fps: Frames per second.
            loop: True to loop.

        Returns:
            The created Animation.
        """
        texture_service = self.owner.scene.get_service(TextureService) if self.owner and self.owner.scene else None
        if not texture_service:
            raise RuntimeError("TextureService not available")
        animation = Animation.from_files(texture_service, filenames, fps, loop)
        self.add_animation(name, animation)
        return animation

    def get_animation(self, name: str) -> Optional[Animation]:
        """Get an animation by name.

        Args:
            name: Animation name.

        Returns:
            The Animation or None.
        """
        return self.animations.get(name)

    def play(self, name: Optional[str] = None) -> None:
        """Play the current animation or switch by name then play.

        Args:
            name: Optional animation name to switch to.

        Returns:
            None
        """
        if name:
            animation = self.animations.get(name)
            if animation:
                self.current_animation = animation
        if self.current_animation:
            self.current_animation.play()

    def pause(self) -> None:
        """Pause the current animation.

        Returns:
            None
        """
        if self.current_animation:
            self.current_animation.pause()

    def set_play(self, play: bool) -> None:
        """Set play/pause state for the current animation.

        Args:
            play: True to play, False to pause.

        Returns:
            None
        """
        if self.current_animation:
            self.current_animation.play() if play else self.current_animation.pause()

    def stop(self) -> None:
        """Stop the current animation.

        Returns:
            None
        """
        if self.current_animation:
            self.current_animation.stop()

    def set_position(self, position: rl.Vector2) -> None:
        """Set animation draw position.

        Args:
            position: Vector2 in pixels.

        Returns:
            None
        """
        self.position = position

    def set_rotation(self, rotation: float) -> None:
        """Set animation rotation in degrees.

        Args:
            rotation: Rotation in degrees.

        Returns:
            None
        """
        self.rotation = rotation

    def set_origin(self, origin: rl.Vector2) -> None:
        """Set animation origin point.

        Args:
            origin: Vector2 origin.

        Returns:
            None
        """
        self.origin = origin

    def set_scale(self, scale: float) -> None:
        """Set animation scale.

        Args:
            scale: Scale multiplier.

        Returns:
            None
        """
        self.scale = scale

    def set_flip_x(self, flip: bool) -> None:
        """Set horizontal flip.

        Args:
            flip: True to flip horizontally.

        Returns:
            None
        """
        self.flip_x = flip

    def set_flip_y(self, flip: bool) -> None:
        """Set vertical flip.

        Args:
            flip: True to flip vertically.

        Returns:
            None
        """
        self.flip_y = flip


class PlatformerMovementParams:
    """Parameter bag for platformer movement."""
    def __init__(self) -> None:
        """  init  .
        
        Returns:
            None
        """
        self.width = 24.0
        self.height = 40.0
        self.max_speed = 220.0
        self.accel = 2000.0
        self.decel = 2500.0
        self.gravity = 1400.0
        self.jump_speed = 520.0
        self.fall_speed = 1200.0
        self.jump_cutoff_multiplier = 0.45
        self.coyote_time = 0.08
        self.jump_buffer = 0.10


class PlatformerMovementComponent(Component):
    """Component for 2D platformer movement."""
    def __init__(self, params: PlatformerMovementParams) -> None:
        """  init  .
        
        Args:
            params: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.p = params
        self.physics: Optional[PhysicsService] = None
        self.body: Optional[BodyComponent] = None
        self.grounded = False
        self.on_wall_left = False
        self.on_wall_right = False
        self.coyote_timer = 0.0
        self.jump_buffer_timer = 0.0
        self.move_x = 0.0
        self.jump_pressed = False
        self.jump_held = False

    def init(self) -> None:
        """Resolve PhysicsService and BodyComponent.

        Returns:
            None
        """
        if not self.owner or not self.owner.scene:
            return
        self.physics = self.owner.scene.get_service(PhysicsService)
        self.body = self.owner.get_component(BodyComponent)

    def update(self, delta_time: float) -> None:
        """Update movement and apply velocity to the body.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        if not self.physics or not self.body or not self.body.body:
            return
        self.coyote_timer = max(0.0, self.coyote_timer - delta_time)
        self.jump_buffer_timer = max(0.0, self.jump_buffer_timer - delta_time)
        if self.jump_pressed:
            self.jump_buffer_timer = self.p.jump_buffer

        self.grounded = False
        self.on_wall_left = False
        self.on_wall_right = False

        ray_length = self.physics.convert_length_to_meters(4.0)
        half_width = self.physics.convert_length_to_meters(self.p.width) / 2.0
        half_height = self.physics.convert_length_to_meters(self.p.height) / 2.0

        pos = self.body.get_position_meters()
        ground_left_start = b2Vec2(pos.x - half_width, pos.y + half_height)
        ground_right_start = b2Vec2(pos.x + half_width, pos.y + half_height)
        ground_translation = b2Vec2(0.0, ray_length)

        left_ground_hit = raycast_closest(self.physics.world, self.body.body, ground_left_start, ground_translation)
        right_ground_hit = raycast_closest(self.physics.world, self.body.body, ground_right_start, ground_translation)
        self.grounded = left_ground_hit.hit or right_ground_hit.hit

        mid = b2Vec2(pos.x, pos.y)
        wall_left_start = b2Vec2(pos.x - half_width, mid.y)
        wall_left_translation = b2Vec2(-ray_length, 0.0)
        wall_right_start = b2Vec2(pos.x + half_width, mid.y)
        wall_right_translation = b2Vec2(ray_length, 0.0)

        left_wall_hit = raycast_closest(self.physics.world, self.body.body, wall_left_start, wall_left_translation)
        right_wall_hit = raycast_closest(self.physics.world, self.body.body, wall_right_start, wall_right_translation)
        self.on_wall_left = left_wall_hit.hit
        self.on_wall_right = right_wall_hit.hit

        if self.grounded:
            self.coyote_timer = self.p.coyote_time

        target_vx = self.move_x * self.p.max_speed
        v = self.body.get_velocity_pixels()

        if abs(target_vx) > 0.001:
            v.x = self.move_towards(v.x, target_vx, self.p.accel * delta_time)
        else:
            v.x = self.move_towards(v.x, 0.0, self.p.decel * delta_time)

        v.y += self.p.gravity * delta_time
        v.y = max(-self.p.fall_speed, min(self.p.fall_speed, v.y))

        can_jump = self.grounded or self.coyote_timer > 0.0
        if self.jump_buffer_timer > 0.0 and can_jump:
            v.y = -self.p.jump_speed
            self.jump_buffer_timer = 0.0
            self.coyote_timer = 0.0
            self.grounded = False

        if not self.jump_held and v.y < 0.0:
            v.y *= self.p.jump_cutoff_multiplier

        self.body.set_velocity(v)

    @staticmethod
    def move_towards(current: float, target: float, max_delta: float) -> float:
        """Move a value toward a target by at most max_delta.

        Args:
            current: Current value.
            target: Target value.
            max_delta: Maximum change allowed.

        Returns:
            The updated value.
        """
        delta = target - current
        if abs(delta) <= max_delta:
            return target
        return current + (max_delta if delta > 0 else -max_delta)

    def set_input(self, horizontal_speed: float, jump_pressed: bool, jump_held: bool) -> None:
        """Set movement input for this frame.

        Args:
            horizontal_speed: Horizontal input (-1 to 1).
            jump_pressed: True if jump pressed this frame.
            jump_held: True if jump is held.

        Returns:
            None
        """
        self.move_x = horizontal_speed
        self.jump_pressed = jump_pressed
        self.jump_held = jump_held


class TopDownMovementParams:
    """Parameter bag for top-down movement."""
    def __init__(self) -> None:
        """  init  .
        
        Returns:
            None
        """
        self.max_speed = 300.0
        self.accel = 1200.0
        self.friction = 1200.0
        self.deadzone = 0.1


class TopDownMovementComponent(Component):
    """Component for 2D top-down movement."""
    def __init__(self, params: TopDownMovementParams) -> None:
        """  init  .
        
        Args:
            params: Parameter.
        
        Returns:
            None
        """
        super().__init__()
        self.p = params
        self.physics: Optional[PhysicsService] = None
        self.body: Optional[BodyComponent] = None
        self.move_x = 0.0
        self.move_y = 0.0
        self.facing_dir = 0.0

    def init(self) -> None:
        """Resolve PhysicsService and BodyComponent.

        Returns:
            None
        """
        if not self.owner or not self.owner.scene:
            return
        self.physics = self.owner.scene.get_service(PhysicsService)
        self.body = self.owner.get_component(BodyComponent)

    def update(self, delta_time: float) -> None:
        """Update movement and apply velocity to the body.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        if not self.body or not self.body.body:
            return
        v = self.body.get_velocity_pixels()
        input_vec = v2(self.move_x, self.move_y)
        input_len_sq = input_vec.x * input_vec.x + input_vec.y * input_vec.y
        desired = v2(0.0, 0.0)

        if input_len_sq > self.p.deadzone * self.p.deadzone:
            desired = v2(input_vec.x * self.p.max_speed, input_vec.y * self.p.max_speed)
            self.facing_dir = math.degrees(math.atan2(input_vec.y, input_vec.x))
            v = self.move_towards_vec(v, desired, self.p.accel * delta_time)
        else:
            v = self.apply_friction(v, self.p.friction * delta_time)

        speed_sq = v.x * v.x + v.y * v.y
        max_speed_sq = self.p.max_speed * self.p.max_speed
        if speed_sq > max_speed_sq:
            speed = math.sqrt(speed_sq)
            scale = self.p.max_speed / speed
            v.x *= scale
            v.y *= scale

        self.body.set_velocity(v)

    @staticmethod
    def move_towards_vec(current: rl.Vector2, target: rl.Vector2, max_delta: float) -> rl.Vector2:
        """Move a vector toward a target by at most max_delta.

        Args:
            current: Current vector.
            target: Target vector.
            max_delta: Maximum change length.

        Returns:
            The updated vector.
        """
        delta = v2(target.x - current.x, target.y - current.y)
        length = math.sqrt(delta.x * delta.x + delta.y * delta.y)
        if length <= max_delta or length < 1e-5:
            return target
        scale = max_delta / length
        return v2(current.x + delta.x * scale, current.y + delta.y * scale)

    @staticmethod
    def apply_friction(v: rl.Vector2, friction_delta: float) -> rl.Vector2:
        """Apply friction to reduce vector magnitude.

        Args:
            v: Current velocity vector.
            friction_delta: Speed to subtract this frame.

        Returns:
            The updated velocity vector.
        """
        speed = math.sqrt(v.x * v.x + v.y * v.y)
        if speed < 1e-5:
            return v2(0.0, 0.0)
        new_speed = speed - friction_delta
        if new_speed <= 0.0:
            return v2(0.0, 0.0)
        scale = new_speed / speed
        return v2(v.x * scale, v.y * scale)

    def set_input(self, horizontal: float, vertical: float) -> None:
        """Set movement input for this frame.

        Args:
            horizontal: Horizontal input (-1 to 1).
            vertical: Vertical input (-1 to 1).

        Returns:
            None
        """
        self.move_x = horizontal
        self.move_y = vertical
