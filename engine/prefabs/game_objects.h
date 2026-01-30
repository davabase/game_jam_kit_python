#pragma once

#include "engine/framework.h"
#include "engine/prefabs/components.h"
#include "engine/prefabs/services.h"

/**
 * A simple static box.
 */
class StaticBox : public GameObject
{
public:
    b2BodyId body = b2_nullBodyId;
    float x, y, width, height;
    bool is_visible = true;

    /**
     * Constructor for StaticBox.
     *
     * @param x The center x position in pixels.
     * @param y The center y position in pixels.
     * @param width The width of the box in pixels.
     * @param height The height of the box in pixels.
     */
    StaticBox(float x, float y, float width, float height) : x(x), y(y), width(width), height(height) {}

    /**
     * Constructor for StaticBox that takes Vector2s.
     *
     * @param position The center of the box in pixels.
     * @param size The size of the box in pixels.
     */
    StaticBox(Vector2 position, Vector2 size) : x(position.x), y(position.y), width(size.x), height(size.y) {}

    /**
     * Initialize the StaticBox.
     */
    void init() override
    {
        auto physics = scene->get_service<PhysicsService>();
        const float pixels_to_meters = physics->pixels_to_meters;
        auto world = physics->world;

        b2BodyDef body_def = b2DefaultBodyDef();
        body_def.type = b2_staticBody;
        body_def.position = b2Vec2{x * pixels_to_meters, y * pixels_to_meters};
        body = b2CreateBody(world, &body_def);

        b2Polygon body_polygon = b2MakeBox(width / 2.0f * pixels_to_meters, height / 2.0f * pixels_to_meters);
        b2ShapeDef box_shape_def = b2DefaultShapeDef();
        b2CreatePolygonShape(body, &box_shape_def, &body_polygon);

        add_component<BodyComponent>(body);
    }

    /**
     * Draw the StaticBox as a blue rectangle.
     */
    void draw() override
    {
        if (is_visible)
        {
            DrawRectangle((int)(x - width / 2.0f), (int)(y - height / 2.0f), (int)width, (int)height, BLUE);
        }
    }
};

/**
 * A simple dynamic rigid body box.
 */
class DynamicBox : public GameObject
{
public:
    b2BodyId body = b2_nullBodyId;
    float x, y, width, height, rot_deg;
    PhysicsService* physics;

    /**
     * Constructor for DynamicBox.
     *
     * @param x The center x position in pixels.
     * @param y The center y position in pixels.
     * @param width The width of the box in pixels.
     * @param height The height of the box in pixels.
     * @param rotation The angle of the box in degrees.
     */
    DynamicBox(float x, float y, float width, float height, float rotation = 0) :
        x(x),
        y(y),
        width(width),
        height(height),
        rot_deg(rotation)
    {
    }

    /**
     * Constructor for DynamicBox that takes Vector2s.
     *
     * @param position The center of the box in pixels.
     * @param size The size of the box in pixels.
     * @param rotation The angle of the box in degrees.
     */
    DynamicBox(Vector2 position, Vector2 size, float rotation = 0) :
        x(position.x),
        y(position.y),
        width(size.x),
        height(size.y),
        rot_deg(rotation)
    {
    }

    /**
     * Initialize the DynamicBody.
     */
    void init() override
    {
        physics = scene->get_service<PhysicsService>();
        const float pixels_to_meters = physics->pixels_to_meters;
        auto world = physics->world;

        b2BodyDef body_def = b2DefaultBodyDef();
        body_def.type = b2_dynamicBody;
        body_def.position = b2Vec2{x * pixels_to_meters, y * pixels_to_meters};
        body_def.rotation = b2MakeRot(rot_deg * DEG2RAD);
        body = b2CreateBody(world, &body_def);

        b2Polygon body_polygon = b2MakeBox(width / 2.0f * pixels_to_meters, height / 2.0f * pixels_to_meters);
        b2ShapeDef box_shape_def = b2DefaultShapeDef();
        b2SurfaceMaterial body_material = b2DefaultSurfaceMaterial();
        body_material.friction = 0.3f;
        box_shape_def.density = 1.0f;
        box_shape_def.material = body_material;
        b2CreatePolygonShape(body, &box_shape_def, &body_polygon);

        auto body_component = add_component<BodyComponent>(body);
        add_component<SpriteComponent>("assets/character_green_idle.png", body_component);
    }

    /**
     * Draw the DynamicBody as a red rectangle.
     */
    void draw() override
    {
        float meters_to_pixels = physics->meters_to_pixels;
        b2Vec2 pos = b2Body_GetPosition(body);
        b2Rot rot = b2Body_GetRotation(body);
        float angle = b2Rot_GetAngle(rot) * RAD2DEG;

        DrawRectanglePro({physics->convert_to_pixels(pos.x), physics->convert_to_pixels(pos.y), width, height},
                         {width / 2.0f, height / 2.0f},
                         angle,
                         RED);
    }
};

/**
 * A 2D camera that controls the view of the scene.
 */
class CameraObject : public GameObject
{
public:
    Camera2D camera;

    // The target position to follow, in pixels.
    Vector2 target = {0, 0};

    // The size of the screen.
    Vector2 size = {0, 0};

    // The size of the level in pixels. The camera will clamp to this size.
    Vector2 level_size = {0, 0};

    // Tracking speed in pixels per second.
    Vector2 follow_speed = {1000, 1000};

    // Deadzone bounds in pixels relative to the center.
    float offset_left = 150.0f;
    float offset_right = 150.0f;
    float offset_top = 100.0f;
    float offset_bottom = 100.0f;

    /**
     * Constructor for CameraObject.
     *
     * @param size The size of the camera view.
     * @param level_size The size of the level.
     * @param follow_speed The speed at which the camera follows the target.
     * @param offset_left The left deadzone offset in pixels.
     * @param offset_right The right deadzone offset in pixels.
     * @param offset_top The top deadzone offset in pixels.
     * @param offset_bottom The bottom deadzone offset in pixels.
     */
    CameraObject(Vector2 size,
                 Vector2 level_size = {0, 0},
                 Vector2 follow_speed = {1000, 1000},
                 float offset_left = 70,
                 float offset_right = 70,
                 float offset_top = 40,
                 float offset_bottom = 40) :
        size(size),
        level_size(level_size),
        follow_speed(follow_speed),
        offset_left(offset_left),
        offset_right(offset_right),
        offset_top(offset_top),
        offset_bottom(offset_bottom)
    {
    }

    /**
     * Initialize the camera.
     */
    void init() override
    {
        camera.zoom = 1.0f;
        camera.offset = {size.x / 2.0f, size.y / 2.0f};
        camera.rotation = 0.0f;

        camera.target = target;
    }

    /**
     * Update the camera position based on the target and deadzone.
     *
     * @param delta_time The delta time since the last frame.
     */
    void update(float delta_time) override
    {
        // Desired camera.target after applying deadzone.
        Vector2 desired = camera.target;

        // Convert deadzone from SCREEN pixels to WORLD pixels (depends on zoom).
        // Because camera.target is in world units.
        float inv_zoom = (camera.zoom != 0.0f) ? (1.0f / camera.zoom) : 1.0f;

        float dz_left_w = offset_left * inv_zoom;
        float dz_right_w = offset_right * inv_zoom;
        float dz_top_w = offset_top * inv_zoom;
        float dz_bottom_w = offset_bottom * inv_zoom;

        // Compute target displacement from current camera center (world-space).
        float dx = target.x - camera.target.x;
        float dy = target.y - camera.target.y;

        // If target is outside deadzone, shift desired camera center just enough to bring it back.
        if (dx < -dz_left_w)
        {
            desired.x = target.x + dz_left_w;
        }
        else if (dx > dz_right_w)
        {
            desired.x = target.x - dz_right_w;
        }

        if (dy < -dz_top_w)
        {
            desired.y = target.y + dz_top_w;
        }
        else if (dy > dz_bottom_w)
        {
            desired.y = target.y - dz_bottom_w;
        }

        // Apply tracking speed per axis.
        if (follow_speed.x < 0)
        {
            camera.target.x = desired.x;
        }
        else
        {
            camera.target.x = move_towards(camera.target.x, desired.x, follow_speed.x * delta_time);
        }

        if (follow_speed.y < 0)
        {
            camera.target.y = desired.y;
        }
        else
        {
            camera.target.y = move_towards(camera.target.y, desired.y, follow_speed.y * delta_time);
        }

        Vector2 half_view = {size.x / 2.0f * inv_zoom, size.y / 2.0f * inv_zoom};
        if (level_size.x > size.x)
        {
            camera.target.x = std::max(half_view.x, std::min(level_size.x - half_view.x, camera.target.x));
        }
        if (level_size.y > size.y)
        {
            camera.target.y = std::max(half_view.y, std::min(level_size.y - half_view.y, camera.target.y));
        }
    }

    /**
     * Calculate a value moved towards a target by a maximum delta.
     *
     * @param current The current value.
     * @param target The target value.
     * @param max_delta The maximum change that can be applied.
     * @return The new value after moving towards the target.
     */
    float move_towards(float current, float target, float max_delta)
    {
        float d = target - current;
        if (d > max_delta)
            return current + max_delta;
        if (d < -max_delta)
            return current - max_delta;
        return target;
    }

    /**
     * Set the target position for the camera to follow.
     *
     * @param target The target position in pixels.
     */
    void set_target(Vector2 target)
    {
        this->target = target;
    }

    /**
     * Set the zoom level of the camera.
     *
     * @param zoom The zoom level.
     */
    void set_zoom(float zoom)
    {
        camera.zoom = zoom;
    }

    /**
     * Set the rotation angle of the camera.
     *
     * @param angle The rotation angle in degrees.
     */
    void set_rotation(float angle)
    {
        camera.rotation = angle;
    }

    /**
     * Begin drawing with the camera.
     * The rest of the Scene should be drawn between draw_begin() and draw_end().
     */
    void draw_begin()
    {
        BeginMode2D(camera);
    }

    /**
     * End drawing with the camera.
     */
    void draw_end()
    {
        EndMode2D();
    }

    /**
     * Draw the camera's deadzone for debugging.
     *
     * @param c The color to draw the deadzone rectangle.
     */
    void draw_debug(Color c = {0, 255, 0, 120}) const
    {
        float inv_zoom = (camera.zoom != 0.0f) ? (1.0f / camera.zoom) : 1.0f;
        float dz_left_w = offset_left * inv_zoom;
        float dz_right_w = offset_right * inv_zoom;
        float dz_top_w = offset_top * inv_zoom;
        float dz_bottom_w = offset_bottom * inv_zoom;

        Rectangle r;
        r.x = camera.target.x - dz_left_w;
        r.y = camera.target.y - dz_top_w;
        r.width = dz_left_w + dz_right_w;
        r.height = dz_top_w + dz_bottom_w;

        DrawRectangleLinesEx(r, 2.0f * inv_zoom, c);
    }

    /**
     * Convert screen coordinates to world coordinates.
     *
     * @param point The screen coordinates.
     * @return The corresponding world coordinates.
     */
    Vector2 screen_to_world(Vector2 point)
    {
        return GetScreenToWorld2D(point, camera);
    }
};

/**
 * A split-screen camera that renders to a texture.
 */
class SplitCamera : public CameraObject
{
public:
    RenderTexture2D renderer;

    /**
     * Constructor for SplitCamera.
     *
     * @param size The size of the camera view.
     * @param level_size The size of the level.
     * @param follow_speed The speed at which the camera follows the target.
     * @param offset_left The left deadzone offset in pixels.
     * @param offset_right The right deadzone offset in pixels.
     * @param offset_top The top deadzone offset in pixels.
     * @param offset_bottom The bottom deadzone offset in pixels.
     */
    SplitCamera(Vector2 size,
                Vector2 level_size = {0, 0},
                Vector2 follow_speed = {1000, 1000},
                float offset_left = 70,
                float offset_right = 70,
                float offset_top = 40,
                float offset_bottom = 40) :
        CameraObject(size, level_size, follow_speed, offset_left, offset_right, offset_top, offset_bottom)
    {
    }

    ~SplitCamera()
    {
        UnloadRenderTexture(renderer);
    }

    /**
     * Initialize the SplitCamera.
     */
    void init() override
    {
        renderer = LoadRenderTexture((int)size.x, (int)size.y);
        CameraObject::init();
    }

    /**
     * Begin drawing to the camera's texture.
     * The rest of the Scene should be drawn between draw_begin() and draw_end().
     */
    void draw_begin()
    {
        BeginTextureMode(renderer);
        ClearBackground(WHITE);
        BeginMode2D(camera);
    }

    /**
     * End drawing to the camera's texture.
     */
    void draw_end()
    {
        EndMode2D();
        EndTextureMode();
    }

    /**
     * Draw the camera's texture at the specified position.
     *
     * @param x The x position to draw the texture.
     * @param y The y position to draw the texture.
     */
    void draw_texture(float x, float y)
    {
        DrawTextureRec(renderer.texture,
                       {0, 0, static_cast<float>(renderer.texture.width), static_cast<float>(-renderer.texture.height)},
                       {x, y},
                       WHITE);
    }

    void draw_texture_pro(float x, float y, float width, float height)
    {
        DrawTexturePro(renderer.texture,
                       {0, 0, static_cast<float>(renderer.texture.width), static_cast<float>(-renderer.texture.height)},
                       {x, y, width, height},
                       {0, 0},
                       0.0f,
                       WHITE);
    }

    /**
     * Convert screen coordinates to world coordinates relative to a draw position.
     *
     * @param draw_position The position where the texture is drawn.
     * @param point The screen coordinates.
     * @return The corresponding world coordinates.
     */
    Vector2 screen_to_world(Vector2 draw_position, Vector2 point)
    {
        auto local_point = point - draw_position;
        return GetScreenToWorld2D(local_point, camera);
    }
};

/**
 * Parameters for the PlatformerCharacter game object.
 */
struct CharacterParams
{
    // Geometry in pixels
    float width = 24.0f;
    float height = 40.0f;

    // Initial position in pixels
    Vector2 position;

    // Surface behavior
    float friction = 0.0f;
    float restitution = 0.0f;
    float density = 1.0f;
};

/**
 * A simple platformer character with movement and animation.
 */
class PlatformerCharacter : public GameObject
{
public:
    CharacterParams p;
    PhysicsService* physics;
    BodyComponent* body;
    PlatformerMovementComponent* movement;

    bool grounded = false;
    bool on_wall_left = false;
    bool on_wall_right = false;
    float coyote_timer = 0.0f;
    float jump_buffer_timer = 0.0f;
    int gamepad = 0;

    /**
     * Constructor for PlatformerCharacter.
     *
     * @param p The parameters for the character.
     */
    PlatformerCharacter(CharacterParams p, int gamepad = 0) : p(p), gamepad(gamepad) {}

    /**
     * Initialize the PlatformerCharacter.
     */
    void init() override
    {
        physics = scene->get_service<PhysicsService>();

        body = add_component<BodyComponent>(
            [=](BodyComponent& b)
            {
                b2BodyDef body_def = b2DefaultBodyDef();
                body_def.type = b2_dynamicBody;
                body_def.fixedRotation = true;
                // body_def.isBullet = true;
                body_def.linearDamping = 0.0f;
                body_def.angularDamping = 0.0f;
                body_def.position = physics->convert_to_meters(p.position);
                body_def.userData = this;
                b.id = b2CreateBody(physics->world, &body_def);

                b2SurfaceMaterial body_material = b2DefaultSurfaceMaterial();
                body_material.friction = p.friction;
                body_material.restitution = p.restitution;

                b2ShapeDef box_shape_def = b2DefaultShapeDef();
                box_shape_def.density = p.density;
                box_shape_def.material = body_material;

                // Needed to presolve one-way behavior.
                box_shape_def.enablePreSolveEvents = true;

                b2Polygon body_polygon = b2MakeRoundedBox(physics->convert_to_meters(p.width / 2.0f),
                                                          physics->convert_to_meters(p.height / 2.0f),
                                                          physics->convert_to_meters(0.25));
                b2CreatePolygonShape(b.id, &box_shape_def, &body_polygon);
            });

        PlatformerMovementParams mp;
        mp.width = p.width;
        mp.height = p.height;
        movement = add_component<PlatformerMovementComponent>(mp);
    }

    /**
     * Update the PlatformerCharacter.
     */
    void update(float delta_time) override
    {
        float deadzone = 0.1f;

        const bool jump_pressed =
            IsKeyPressed(KEY_W) || IsGamepadButtonPressed(gamepad, GAMEPAD_BUTTON_RIGHT_FACE_DOWN);
        const bool jump_held = IsKeyDown(KEY_W) || IsGamepadButtonDown(gamepad, GAMEPAD_BUTTON_RIGHT_FACE_DOWN);

        float move_x = 0.0f;
        move_x = GetGamepadAxisMovement(gamepad, GAMEPAD_AXIS_LEFT_X);
        if (fabsf(move_x) < deadzone)
        {
            move_x = 0.0f;
        }
        if (IsKeyDown(KEY_D) || IsGamepadButtonDown(gamepad, GAMEPAD_BUTTON_LEFT_FACE_RIGHT))
        {
            move_x = 1.0f;
        }
        else if (IsKeyDown(KEY_A) || IsGamepadButtonDown(gamepad, GAMEPAD_BUTTON_LEFT_FACE_LEFT))
        {
            move_x = -1.0f;
        }

        movement->set_input(move_x, jump_pressed, jump_held);
    }

    /**
     * Draw the PlatformerCharacter as a rectangle.
     */
    void draw() override
    {
        Color color = movement->grounded ? GREEN : BLUE;
        auto pos = body->get_position_pixels();
        DrawRectanglePro({pos.x, pos.y, p.width, p.height}, {p.width / 2.0f, p.height / 2.0f}, 0.0f, color);
    }
};
