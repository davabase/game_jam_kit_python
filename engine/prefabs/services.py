from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from Box2D import (b2Body, b2CircleShape, b2EdgeShape, b2FixtureDef,
                   b2PolygonShape, b2Vec2, b2World)
import pyray as rl

from engine.framework import Service
from engine.math_extensions import v2
from engine.physics_debug import PhysicsDebugRenderer
from engine.raycasts import circle_hit, raycast_closest, rectangle_hit
from engine.LdtkJson import LdtkJSON, Level, LayerInstance, GridPoint


class MultiService(Service):
    """Service container for multiple services of the same base type.

    Attributes:
        services: Mapping of service name to instance.
    """
    def __init__(self) -> None:
        super().__init__()
        self.services: Dict[str, Service] = {}

    def init_service(self) -> None:
        """Initialize all contained services.

        Returns:
            None
        """
        for service in self.services.values():
            service.init()
        super().init_service()

    def update(self, delta_time: float) -> None:
        """Update all contained services.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        for service in self.services.values():
            service.update(delta_time)
        super().update(delta_time)

    def draw(self) -> None:
        """Draw all contained services.

        Returns:
            None
        """
        for service in self.services.values():
            service.draw()

    def add_service(self, name: str, service_or_cls: Any, *args: Any, **kwargs: Any) -> Service:
        """Add a service instance or construct one from a class.

        Args:
            name: Name to register the service under.
            service_or_cls: A Service instance or Service class.
            *args: Positional args forwarded to the constructor.
            **kwargs: Keyword args forwarded to the constructor.

        Returns:
            The service instance added.
        """
        if isinstance(service_or_cls, Service):
            service = service_or_cls
        else:
            service = service_or_cls(*args, **kwargs)
        self.services[name] = service
        return service

    def get_service(self, name: str) -> Optional[Service]:
        """Get a service by name.

        Args:
            name: Registered name of the service.

        Returns:
            The service instance, or None if missing.
        """
        return self.services.get(name)


class TextureService(Service):
    """Cache textures so they are loaded once.

    Attributes:
        textures: Mapping of filename to loaded Texture2D.
    """
    def __init__(self) -> None:
        super().__init__()
        self.textures: Dict[str, rl.Texture2D] = {}

    def get_texture(self, filename: str) -> rl.Texture2D:
        """Get or load a texture by filename.

        Args:
            filename: Path to the texture file.

        Returns:
            The loaded Texture2D.
        """

        if filename not in self.textures:
            self.textures[filename] = rl.load_texture(filename)
        return self.textures[filename]


class SoundService(Service):
    """Cache sounds and create aliases for overlapping playback.

    Attributes:
        sounds: Mapping of filename to a list of Sound aliases.
    """
    def __init__(self) -> None:
        super().__init__()
        self.sounds: Dict[str, List[Any]] = {}

    def get_sound(self, filename: str):
        """Get or load a sound; returns an alias if already loaded.

        Args:
            filename: Path to the sound file.

        Returns:
            A Sound instance (original or alias).
        """

        if filename not in self.sounds:
            self.sounds[filename] = [rl.load_sound(filename)]
        else:
            self.sounds[filename].append(rl.load_sound_alias(self.sounds[filename][0]))
        return self.sounds[filename][-1]


class PhysicsService(Service):
    """Service that owns the Box2D world and physics configuration."""
    def __init__(self,
                 gravity: b2Vec2 = b2Vec2(0.0, 10.0),
                 time_step: float = 1.0 / 60.0,
                 sub_steps: int = 6,
                 meters_to_pixels: float = 30.0) -> None:
        super().__init__()
        self.gravity = gravity
        self.time_step = time_step
        self.sub_steps = sub_steps
        self.meters_to_pixels = meters_to_pixels
        self.pixels_to_meters = 1.0 / meters_to_pixels
        self.world: Optional[b2World] = None
        self.debug_draw = PhysicsDebugRenderer(meters_to_pixels=meters_to_pixels)

    def init(self) -> None:
        """Create the Box2D world.

        Returns:
            None
        """
        self.world = b2World(gravity=self.gravity, doSleep=True)
        self.world.contactListener = None
        self.world.renderer = self.debug_draw

    def update(self, delta_time: float) -> None:
        """Step the physics world.

        Args:
            delta_time: Seconds since the last frame (unused by fixed-step).

        Returns:
            None
        """
        if not self.world:
            return
        self.world.Step(self.time_step, self.sub_steps, self.sub_steps)

    def draw_debug(self) -> None:
        """Draw debug shapes for the physics world.

        Returns:
            None
        """
        if self.world:
            self.world.DrawDebugData()

    def convert_to_pixels(self, meters: b2Vec2) -> b2Vec2:
        """Convert meters to pixels.

        Args:
            meters: Vector in meters.

        Returns:
            Vector in pixels.
        """
        return b2Vec2(meters.x * self.meters_to_pixels, meters.y * self.meters_to_pixels)

    def convert_to_meters(self, pixels) -> b2Vec2:
        """Convert pixels to meters.

        Args:
            pixels: Vector in pixels.

        Returns:
            Vector in meters.
        """
        return b2Vec2(pixels.x * self.pixels_to_meters, pixels.y * self.pixels_to_meters)

    def convert_length_to_pixels(self, meters: float) -> float:
        """Convert a length in meters to pixels.

        Args:
            meters: Length in meters.

        Returns:
            Length in pixels.
        """
        return meters * self.meters_to_pixels

    def convert_length_to_meters(self, pixels: float) -> float:
        """Convert a length in pixels to meters.

        Args:
            pixels: Length in pixels.

        Returns:
            Length in meters.
        """
        return pixels * self.pixels_to_meters

    def raycast(self, ignore: Optional[b2Body], start, end):
        """Raycast in pixel units.

        Args:
            ignore: Body to ignore during raycast.
            start: Start position in pixels.
            end: End position in pixels.

        Returns:
            RayHit if world exists, otherwise None.
        """
        if not self.world:
            return None
        origin = self.convert_to_meters(start)
        translation = self.convert_to_meters(v2(end.x - start.x, end.y - start.y))
        return raycast_closest(self.world, ignore, origin, translation)

    def circle_overlap(self, center, radius: float, ignore_body: Optional[b2Body] = None):
        """Overlap query for a circle in pixel units.

        Args:
            center: Center in pixels.
            radius: Radius in pixels.
            ignore_body: Optional body to ignore.

        Returns:
            List of bodies overlapping the circle.
        """
        if not self.world:
            return []
        center_m = self.convert_to_meters(center)
        radius_m = self.convert_length_to_meters(radius)
        return circle_hit(self.world, ignore_body, center_m, radius_m)

    def rectangle_overlap(self, rectangle, rotation: float = 0.0, ignore_body: Optional[b2Body] = None):
        """Overlap query for a rectangle in pixel units.

        Args:
            rectangle: Rectangle in pixels.
            rotation: Rotation in radians.
            ignore_body: Optional body to ignore.

        Returns:
            List of bodies overlapping the rectangle.
        """
        if not self.world:
            return []
        size = v2(rectangle.width, rectangle.height)
        center = v2(rectangle.x + size.x / 2.0, rectangle.y + size.y / 2.0)
        size_m = self.convert_to_meters(size)
        center_m = self.convert_to_meters(center)
        return rectangle_hit(self.world, ignore_body, center_m, size_m, rotation)


@dataclass(frozen=True)
class IntPoint:
    x: int
    y: int


class LdtkEntity:
    """Thin wrapper around an LDtk entity instance."""
    def __init__(self, entity) -> None:
        self.entity = entity

    def getPosition(self) -> IntPoint:
        """Get entity position in pixels.

        Returns:
            IntPoint for the entity position.
        """
        return IntPoint(self.entity.px[0], self.entity.px[1])

    def getSize(self) -> IntPoint:
        """Get entity size in pixels.

        Returns:
            IntPoint for the entity size.
        """
        return IntPoint(self.entity.width, self.entity.height)

    def getField(self, name: str) -> Optional[Any]:
        """Get a field value by name.

        Args:
            name: Field identifier.

        Returns:
            Field value, converted for point fields when possible.
        """
        for field in self.entity.field_instances:
            if field.identifier == name:
                value = field.value
                if isinstance(value, dict) and "cx" in value and "cy" in value:
                    return IntPoint(int(value["cx"]), int(value["cy"]))
                return value
        return None


@dataclass
class LayerRenderer:
    renderer: rl.RenderTexture
    layer_iid: str
    visible: bool = True


class LevelService(Service):
    """Service for loading and drawing LDtk levels and collisions.

    Attributes:
        project: Parsed LDtk project.
        level: Active Level instance.
        renderers: Render textures per layer.
        layer_bodies: Physics bodies used for collision.
        physics: PhysicsService reference.
    """
    def __init__(self,
                 project_file: str,
                 level_name: str,
                 collision_names: List[str],
                 scale: float = 1.0) -> None:
        super().__init__()
        self.project_file = project_file
        self.level_name = level_name
        self.collision_names = collision_names
        self.scale = scale
        self.project: Optional[LdtkJSON] = None
        self.level: Optional[Level] = None
        self.renderers: List[LayerRenderer] = []
        self.layer_bodies: List[b2Body] = []
        self.physics: Optional[PhysicsService] = None
        self.layer_defs_by_uid: Dict[int, Any] = {}

    def init(self) -> None:
        """Load the LDtk project, build renderers and collision bodies.

        Returns:
            None
        """
        if not rl.file_exists(self.project_file):
            print(f"LDtk file not found: {self.project_file}")
            raise RuntimeError("LDtk file not found")

        with open(self.project_file, "r", encoding="utf-8") as handle:
            project_data = json.load(handle)
        self.project = LdtkJSON.from_dict(project_data)

        level = None
        for candidate in self.project.levels:
            if candidate.identifier == self.level_name:
                level = candidate
                break
        if level is None:
            print(f"LDtk level not found: {self.level_name}")
            raise RuntimeError("LDtk level not found")

        if level.layer_instances is None and level.external_rel_path:
            external_path = self._resolve_external_level_path(level.external_rel_path)
            with open(external_path, "r", encoding="utf-8") as handle:
                external_data = json.load(handle)
            level = Level.from_dict(external_data)

        self.level = level
        self.layer_defs_by_uid = {layer.uid: layer for layer in self.project.defs.layers}

        self.physics = self.scene.get_service(PhysicsService) if self.scene else None
        if not self.physics:
            print("PhysicsService required for LevelService")
            raise RuntimeError("PhysicsService required")

        texture_service = self.scene.get_service(TextureService)
        for layer in self.level.layer_instances or []:
            if layer.tileset_rel_path:
                tileset_path = self._resolve_tileset_path(layer.tileset_rel_path)
                texture = texture_service.get_texture(tileset_path)
                renderer = rl.load_render_texture(self.level.px_wid, self.level.px_hei)
                self._render_layer_tiles(layer, texture, renderer)
                self.renderers.append(LayerRenderer(renderer=renderer, layer_iid=layer.iid, visible=layer.visible))

            if layer.type == "IntGrid" and self.collision_names:
                self._build_collision_for_layer(layer)

    def _resolve_tileset_path(self, rel_path: str) -> str:
        """Resolve a tileset path relative to the project file.

        Args:
            rel_path: Relative tileset path from the LDtk project.

        Returns:
            Absolute or normalized tileset path.
        """
        import os

        directory = os.path.dirname(self.project_file)
        return os.path.join(directory, rel_path).replace("\\", "/")

    def _resolve_external_level_path(self, rel_path: str) -> str:
        """Resolve an external level path relative to the project file.

        Args:
            rel_path: Relative level path from the LDtk project.

        Returns:
            Absolute or normalized level path.
        """
        import os

        directory = os.path.dirname(self.project_file)
        return os.path.join(directory, rel_path).replace("\\", "/")

    def _render_layer_tiles(self, layer: LayerInstance, texture: rl.Texture2D, renderer: rl.RenderTexture) -> None:
        """Render the tiles for a layer to a render texture.

        Args:
            layer: Layer instance to render.
            texture: Tileset texture.
            renderer: Render texture target.

        Returns:
            None
        """
        rl.begin_texture_mode(renderer)
        rl.clear_background(rl.Color(0, 0, 0, 0))

        tile_size = layer.grid_size
        tiles = list(layer.grid_tiles) + list(layer.auto_layer_tiles)
        for tile in tiles:
            src_x, src_y = tile.src[0], tile.src[1]
            flip_x = (tile.f & 1) != 0
            flip_y = (tile.f & 2) != 0
            src = rl.Rectangle(float(src_x), float(src_y),
                            float(tile_size) * (-1.0 if flip_x else 1.0),
                            float(tile_size) * (-1.0 if flip_y else 1.0))
            dest = v2(float(tile.px[0] + layer.px_total_offset_x), float(tile.px[1] + layer.px_total_offset_y))
            rl.draw_texture_rec(texture, src, dest, rl.WHITE)

        rl.end_texture_mode()

    def _intgrid_value_name(self, layer: LayerInstance, value: int) -> Optional[str]:
        """Map an IntGrid value to its identifier string.

        Args:
            layer: Layer instance with IntGrid definitions.
            value: Raw IntGrid value.

        Returns:
            Identifier string or None if empty/unknown.
        """
        if value == 0:
            return None
        layer_def = self.layer_defs_by_uid.get(layer.layer_def_uid)
        if not layer_def:
            return None
        for def_value in layer_def.int_grid_values:
            if def_value.value == value:
                return def_value.identifier
        return None

    def _build_collision_for_layer(self, layer: LayerInstance) -> None:
        """Create boundary colliders for a collision layer.

        Args:
            layer: Layer instance to build colliders for.

        Returns:
            None
        """
        if not self.physics or not self.physics.world:
            return
        world = self.physics.world
        body = world.CreateStaticBody(position=(0, 0))
        grid_w = layer.c_wid
        grid_h = layer.c_hei
        cell_size = float(layer.grid_size) * self.scale
        # Build boundary edges into chain shapes to avoid internal collisions.
        def is_solid(cx: int, cy: int) -> bool:
            if cx < 0 or cy < 0 or cx >= grid_w or cy >= grid_h:
                return False
            idx = cy * grid_w + cx
            value = layer.int_grid_csv[idx] if idx < len(layer.int_grid_csv) else 0
            name = self._intgrid_value_name(layer, value)
            return bool(name and name in self.collision_names)

        def make_edge(a, b):
            return (a, b) if a <= b else (b, a)

        edges = set()
        for y in range(grid_h):
            for x in range(grid_w):
                if not is_solid(x, y):
                    continue
                if not is_solid(x, y - 1):
                    edges.add(make_edge((x, y), (x + 1, y)))
                if not is_solid(x, y + 1):
                    edges.add(make_edge((x, y + 1), (x + 1, y + 1)))
                if not is_solid(x - 1, y):
                    edges.add(make_edge((x, y), (x, y + 1)))
                if not is_solid(x + 1, y):
                    edges.add(make_edge((x + 1, y), (x + 1, y + 1)))

        adj: Dict[tuple, List[tuple]] = {}
        for a, b in edges:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)

        def erase_edge(a, b):
            edges.discard(make_edge(a, b))

        loops: List[List[tuple]] = []
        while edges:
            start_a, start_b = next(iter(edges))
            start = start_a
            cur = start_b
            prev = start
            poly = [start, cur]
            erase_edge(start, cur)

            while cur != start:
                next_pt = None
                for cand in adj.get(cur, []):
                    if cand == prev:
                        continue
                    if make_edge(cur, cand) in edges:
                        next_pt = cand
                        break
                if next_pt is None:
                    break
                prev, cur = cur, next_pt
                poly.append(cur)
                erase_edge(prev, cur)
                if len(poly) > 100000:
                    break

            if poly and poly[0] == poly[-1]:
                poly.pop()
            if len(poly) >= 3:
                loops.append(poly)

        for loop in loops:
            verts = []
            for cx, cy in loop:
                x_px = cx * cell_size
                y_px = cy * cell_size
                verts.append(self.physics.convert_to_meters(v2(x_px, y_px)))
            count = len(verts)
            if count < 2:
                continue
            for i in range(count):
                v1 = verts[i]
                v2p = verts[(i + 1) % count]
                edge = b2EdgeShape(vertices=[(float(v1.x), float(v1.y)), (float(v2p.x), float(v2p.y))])
                body.CreateFixture(shape=edge, friction=0.1, restitution=0.1)
        self.layer_bodies.append(body)

    def draw(self) -> None:
        """Draw all visible layer renderers in reverse order.

        Returns:
            None
        """
        for renderer in reversed(self.renderers):
            if not renderer.visible:
                continue
            texture = renderer.renderer.texture
            src = rl.Rectangle(0.0, 0.0, float(texture.width), -float(texture.height))
            dest = rl.Rectangle(0.0, 0.0, float(texture.width) * self.scale, float(texture.height) * self.scale)
            rl.draw_texture_pro(texture, src, dest, v2(0.0, 0.0), 0.0, rl.WHITE)

    def draw_layer(self, layer_id_or_name: str) -> None:
        """Draw a specific layer by IID or identifier.

        Args:
            layer_id_or_name: Layer IID or identifier.

        Returns:
            None
        """
        if not self.level:
            return
        layer = None
        for layer_inst in self.level.layer_instances or []:
            if layer_inst.iid == layer_id_or_name or layer_inst.identifier == layer_id_or_name:
                layer = layer_inst
                break
        if not layer:
            return
        for renderer in self.renderers:
            if renderer.layer_iid == layer.iid:
                texture = renderer.renderer.texture
                src = rl.Rectangle(0.0, 0.0, float(texture.width), -float(texture.height))
                dest = rl.Rectangle(0.0, 0.0, float(texture.width) * self.scale, float(texture.height) * self.scale)
                rl.draw_texture_pro(texture, src, dest, v2(0.0, 0.0), 0.0, rl.WHITE)
                return

    def set_layer_visibility(self, layer_id_or_name: str, visible: bool) -> None:
        """Set a layer's visibility by IID or identifier.

        Args:
            layer_id_or_name: Layer IID or identifier.
            visible: True to show the layer, False to hide it.

        Returns:
            None
        """
        if not self.level:
            return
        for layer_inst in self.level.layer_instances or []:
            if layer_inst.iid == layer_id_or_name or layer_inst.identifier == layer_id_or_name:
                for renderer in self.renderers:
                    if renderer.layer_iid == layer_inst.iid:
                        renderer.visible = visible
                        return

    def get_layer_by_name(self, name: str) -> Optional[LayerInstance]:
        """Get a layer instance by name.

        Args:
            name: Layer identifier.

        Returns:
            The LayerInstance or None.
        """
        if not self.level:
            return None
        for layer in self.level.layer_instances or []:
            if layer.identifier == name:
                return layer
        return None

    def get_entities(self) -> List[LdtkEntity]:
        """Get all entities across all layers.

        Returns:
            List of LdtkEntity wrappers.
        """
        if not self.level:
            print("LDtk project not loaded.")
            return []
        entities: List[LdtkEntity] = []
        for layer in self.level.layer_instances or []:
            if layer.type != "Entities":
                continue
            for entity in layer.entity_instances:
                entities.append(LdtkEntity(entity))
        return entities

    def get_entities_by_name(self, name: str) -> List[LdtkEntity]:
        """Get all entities by name across all layers.

        Args:
            name: Entity identifier.

        Returns:
            List of matching entities.
        """
        return [entity for entity in self.get_entities() if entity.entity.identifier == name]

    def get_entities_by_tag(self, tag: str) -> List[LdtkEntity]:
        """Get all entities by tag across all layers.

        Args:
            tag: Tag string.

        Returns:
            List of matching entities.
        """
        return [entity for entity in self.get_entities() if tag in entity.entity.tags]

    def get_entity_by_name(self, name: str) -> Optional[LdtkEntity]:
        """Get the first entity by name.

        Args:
            name: Entity identifier.

        Returns:
            The first matching entity, or None.
        """
        entities = self.get_entities_by_name(name)
        return entities[0] if entities else None

    def get_entity_by_tag(self, tag: str) -> Optional[LdtkEntity]:
        """Get the first entity by tag.

        Args:
            tag: Tag string.

        Returns:
            The first matching entity, or None.
        """
        entities = self.get_entities_by_tag(tag)
        return entities[0] if entities else None

    def convert_to_pixels(self, point: IntPoint) -> Any:
        """Convert grid point to pixels.

        Args:
            point: Grid point.

        Returns:
            Vector2 in pixels.
        """
        return v2(point.x * self.scale, point.y * self.scale)

    def convert_cells_to_pixels(self, cell_point: IntPoint, layer: LayerInstance):
        """Convert cell coordinates to pixels.

        Args:
            cell_point: Cell coordinates.
            layer: Layer instance for cell size.

        Returns:
            Vector2 in pixels.
        """
        cell_size = float(layer.grid_size)
        return v2(cell_point.x * cell_size * self.scale, cell_point.y * cell_size * self.scale)

    def convert_to_meters(self, point: IntPoint):
        """Convert grid point to meters.

        Args:
            point: Grid point.

        Returns:
            b2Vec2 in meters.
        """
        if not self.physics:
            return b2Vec2(0.0, 0.0)
        return self.physics.convert_to_meters(self.convert_to_pixels(point))

    def convert_to_grid(self, pixels) -> IntPoint:
        """Convert pixels to grid coordinates.

        Args:
            pixels: Vector2 in pixels.

        Returns:
            IntPoint grid coordinate.
        """
        return IntPoint(int(pixels.x / self.scale), int(pixels.y / self.scale))

    def convert_to_grid_meters(self, meters) -> IntPoint:
        """Convert meters to grid coordinates.

        Args:
            meters: b2Vec2 in meters.

        Returns:
            IntPoint grid coordinate.
        """
        if not self.physics:
            return IntPoint(0, 0)
        pixels = self.physics.convert_to_pixels(meters)
        return IntPoint(int(pixels.x / self.scale), int(pixels.y / self.scale))

    def get_size(self):
        """Get level size in pixels.

        Returns:
            Vector2 containing level width and height in pixels.
        """
        if not self.level:
            return v2(0.0, 0.0)
        return v2(float(self.level.px_wid) * self.scale, float(self.level.px_hei) * self.scale)
