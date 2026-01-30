from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from Box2D import (b2AABB, b2Body, b2CircleShape, b2PolygonShape, b2QueryCallback,
                   b2RayCastCallback, b2Transform, b2Vec2, b2TestOverlap)


@dataclass
class RayHit:
    """Raycast hit data.

    Attributes:
        hit: True if the ray hit something.
        body: The body hit, if any.
        fraction: Fraction along the ray where the hit occurred.
        distance: Distance along the ray in world units.
        point: World-space hit point.
        normal: World-space hit normal.
    """
    hit: bool = False
    body: Optional[b2Body] = None
    fraction: float = 1.0
    distance: float = 0.0
    point: b2Vec2 = b2Vec2(0.0, 0.0)
    normal: b2Vec2 = b2Vec2(0.0, 0.0)


class _RayCastClosest(b2RayCastCallback):
    def __init__(self, ignore_body: Optional[b2Body], translation: b2Vec2, result: RayHit) -> None:
        super().__init__()
        self.ignore_body = ignore_body
        self.translation = translation
        self.result = result

    def ReportFixture(self, fixture, point, normal, fraction):  # noqa: N802
        if self.ignore_body is not None and fixture.body == self.ignore_body:
            return 1.0
        if fraction < self.result.fraction:
            self.result.hit = True
            self.result.fraction = fraction
            self.result.distance = self.translation.length * fraction
            self.result.point = point
            self.result.normal = normal
            self.result.body = fixture.body
        return fraction


def raycast_closest(world, ignore_body: Optional[b2Body], origin: b2Vec2, translation: b2Vec2) -> RayHit:
    """Cast a ray and return the closest hit.

    Args:
        world: Box2D world to query.
        ignore_body: Optional body to ignore.
        origin: Ray start in world units.
        translation: Ray delta in world units.

    Returns:
        RayHit data for the closest hit (or empty hit if none).
    """
    result = RayHit()
    callback = _RayCastClosest(ignore_body, translation, result)
    world.RayCast(callback, origin, origin + translation)
    return result


def raycast_all(world, ignore_body: Optional[b2Body], origin: b2Vec2, translation: b2Vec2) -> List[RayHit]:
    """Cast a ray and return all hits.

    Args:
        world: Box2D world to query.
        ignore_body: Optional body to ignore.
        origin: Ray start in world units.
        translation: Ray delta in world units.

    Returns:
        List of RayHit results.
    """
    hits: List[RayHit] = []

    class _RayCastAll(b2RayCastCallback):
        def __init__(self, ignore: Optional[b2Body], translation_vec: b2Vec2) -> None:
            super().__init__()
            self.ignore = ignore
            self.translation_vec = translation_vec

        def ReportFixture(self, fixture, point, normal, fraction):  # noqa: N802
            if self.ignore is not None and fixture.body == self.ignore:
                return 1.0
            hit = RayHit(True, fixture.body, fraction, self.translation_vec.length * fraction, point, normal)
            hits.append(hit)
            return fraction

    world.RayCast(_RayCastAll(ignore_body, translation), origin, origin + translation)
    return hits


def _aabb_for_circle(center: b2Vec2, radius: float) -> b2AABB:
    lower = b2Vec2(center.x - radius, center.y - radius)
    upper = b2Vec2(center.x + radius, center.y + radius)
    return b2AABB(lowerBound=lower, upperBound=upper)


def _aabb_for_box(center: b2Vec2, half_w: float, half_h: float, angle: float) -> b2AABB:
    # Conservative AABB for rotated box
    import math

    cos_a = abs(math.cos(angle))
    sin_a = abs(math.sin(angle))
    extent_x = half_w * cos_a + half_h * sin_a
    extent_y = half_w * sin_a + half_h * cos_a
    lower = b2Vec2(center.x - extent_x, center.y - extent_y)
    upper = b2Vec2(center.x + extent_x, center.y + extent_y)
    return b2AABB(lowerBound=lower, upperBound=upper)


def shape_hit(world, ignore_body: Optional[b2Body], shape, transform: b2Transform) -> List[b2Body]:
    """Query overlaps for a shape and return hit bodies.

    Args:
        world: Box2D world to query.
        ignore_body: Optional body to ignore.
        shape: Box2D shape to test.
        transform: Transform for the shape.

    Returns:
        List of bodies overlapping the shape.
    """
    aabb = shape.getAABB(transform, 0)
    hits: List[b2Body] = []

    class _QueryCallback(b2QueryCallback):
        def __init__(self, ignore: Optional[b2Body]) -> None:
            super().__init__()
            self.ignore = ignore

        def ReportFixture(self, fixture):  # noqa: N802
            body = fixture.body
            if self.ignore is not None and body == self.ignore:
                return True
            if b2TestOverlap(shape, 0, fixture.shape, 0, transform, fixture.body.transform):
                if body not in hits:
                    hits.append(body)
            return True

    world.QueryAABB(_QueryCallback(ignore_body), aabb)
    return hits


def circle_hit(world, ignore_body: Optional[b2Body], center: b2Vec2, radius: float) -> List[b2Body]:
    """Check for circle overlaps in the world.

    Args:
        world: Box2D world to query.
        ignore_body: Optional body to ignore.
        center: Circle center in world units.
        radius: Circle radius in world units.

    Returns:
        List of bodies overlapping the circle.
    """
    shape = b2CircleShape(radius=radius, pos=b2Vec2(0.0, 0.0))
    transform = b2Transform()
    transform.position = center
    transform.angle = 0.0
    return shape_hit(world, ignore_body, shape, transform)


def rectangle_hit(world, ignore_body: Optional[b2Body], center: b2Vec2, size: b2Vec2, rotation: float = 0.0) -> List[b2Body]:
    """Check for rectangle overlaps in the world.

    Args:
        world: Box2D world to query.
        ignore_body: Optional body to ignore.
        center: Rectangle center in world units.
        size: Rectangle size in world units.
        rotation: Rotation in radians.

    Returns:
        List of bodies overlapping the rectangle.
    """
    half_w = size.x / 2.0
    half_h = size.y / 2.0
    shape = b2PolygonShape(box=(half_w, half_h))
    transform = b2Transform()
    transform.position = center
    transform.angle = rotation
    return shape_hit(world, ignore_body, shape, transform)
