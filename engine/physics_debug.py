from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from Box2D import b2Color, b2Draw
import pyray as rl


@dataclass
class DebugDrawCtx:
    meters_to_pixels: float = 30.0
    line_thickness: float = 1.0


def _to_raylib_color(color: b2Color, alpha: float = 1.0) -> rl.Color:
    r = int(max(0, min(255, color.r * 255)))
    g = int(max(0, min(255, color.g * 255)))
    b = int(max(0, min(255, color.b * 255)))
    a = int(max(0, min(255, alpha * 255)))
    return rl.Color(r, g, b, a)


class PhysicsDebugRenderer(b2Draw):
    def __init__(self, meters_to_pixels: float = 30.0, line_thickness: float = 1.0) -> None:
        super().__init__()
        self.ctx = DebugDrawCtx(meters_to_pixels=meters_to_pixels, line_thickness=line_thickness)

    def DrawPolygon(self, vertices, color):
        count = len(vertices)
        if count < 2:
            return
        c = _to_raylib_color(color)
        for i in range(count):
            p0 = vertices[i]
            p1 = vertices[(i + 1) % count]
            a = rl.Vector2(p0[0] * self.ctx.meters_to_pixels, p0[1] * self.ctx.meters_to_pixels)
            b = rl.Vector2(p1[0] * self.ctx.meters_to_pixels, p1[1] * self.ctx.meters_to_pixels)
            rl.draw_line_ex(a, b, self.ctx.line_thickness, c)

    def DrawSolidPolygon(self, vertices, color):
        count = len(vertices)
        if count < 2:
            return
        fill = _to_raylib_color(color, 0.8)
        line = _to_raylib_color(color, 1.0)
        pts = [rl.Vector2(v[0] * self.ctx.meters_to_pixels, v[1] * self.ctx.meters_to_pixels) for v in vertices]
        center = rl.Vector2(0.0, 0.0)
        for p in pts:
            center.x += p.x
            center.y += p.y
        center.x /= count
        center.y /= count
        for i in range(count - 1):
            rl.draw_triangle(pts[i], center, pts[i + 1], fill)
        rl.draw_triangle(pts[count - 1], center, pts[0], fill)
        for i in range(count):
            rl.draw_line_ex(pts[i], pts[(i + 1) % count], self.ctx.line_thickness, line)

    def DrawCircle(self, center, radius, color):
        c = _to_raylib_color(color)
        rl.draw_circle_lines(int(center[0] * self.ctx.meters_to_pixels),
                        int(center[1] * self.ctx.meters_to_pixels),
                        radius * self.ctx.meters_to_pixels,
                        c)

    def DrawSolidCircle(self, center, radius, axis, color):
        fill = _to_raylib_color(color, 0.8)
        line = _to_raylib_color(color, 1.0)
        c = rl.Vector2(center[0] * self.ctx.meters_to_pixels, center[1] * self.ctx.meters_to_pixels)
        rl.draw_circle_v(c, radius * self.ctx.meters_to_pixels, fill)
        axis_end = rl.Vector2((center[0] + axis[0] * radius) * self.ctx.meters_to_pixels,
                           (center[1] + axis[1] * radius) * self.ctx.meters_to_pixels)
        rl.draw_line_ex(c, axis_end, self.ctx.line_thickness, line)

    def DrawSegment(self, p1, p2, color):
        c = _to_raylib_color(color)
        a = rl.Vector2(p1[0] * self.ctx.meters_to_pixels, p1[1] * self.ctx.meters_to_pixels)
        b = rl.Vector2(p2[0] * self.ctx.meters_to_pixels, p2[1] * self.ctx.meters_to_pixels)
        rl.draw_line_ex(a, b, self.ctx.line_thickness, c)

    def DrawTransform(self, xf):
        p = xf.position
        x_axis = xf.R.x_axis
        y_axis = xf.R.y_axis
        origin = rl.Vector2(p[0] * self.ctx.meters_to_pixels, p[1] * self.ctx.meters_to_pixels)
        x_end = rl.Vector2((p[0] + x_axis[0]) * self.ctx.meters_to_pixels, (p[1] + x_axis[1]) * self.ctx.meters_to_pixels)
        y_end = rl.Vector2((p[0] + y_axis[0]) * self.ctx.meters_to_pixels, (p[1] + y_axis[1]) * self.ctx.meters_to_pixels)
        rl.draw_line_ex(origin, x_end, self.ctx.line_thickness, rl.RED)
        rl.draw_line_ex(origin, y_end, self.ctx.line_thickness, rl.GREEN)

    def DrawPoint(self, p, size, color):
        c = _to_raylib_color(color)
        rl.draw_circle_v(rl.Vector2(p[0] * self.ctx.meters_to_pixels, p[1] * self.ctx.meters_to_pixels), size, c)
