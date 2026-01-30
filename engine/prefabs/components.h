#pragma once

#include "engine/framework.h"
#include "engine/prefabs/managers.h"
#include "engine/prefabs/services.h"
#include "engine/raycasts.h"

/**
 * For when you want a GameObject to have multiple of the same component.
 */
template <typename T>
class MultiComponent : public Component
{
public:
    std::unordered_map<std::string, std::unique_ptr<T>> components;

    MultiComponent() {}

    /**
     * Initialize all components.
     */
    void init() override
    {
        for (auto& component : components)
        {
            component.second->init();
        }
    }

    /**
     * Update all components.
     *
     * @param delta_time The time elapsed since the last frame.
     */
    void update(float delta_time) override
    {
        for (auto& component : components)
        {
            component.second->update(delta_time);
        }
    }

    /**
     * Draw all components.
     */
    void draw() override
    {
        for (auto& component : components)
        {
            component.second->draw();
        }
    }

    /**
     * Add a component to the MultiComponent.
     *
     * @param name The name to give the component.
     * @param component The component to add.
     */
    void add_component(std::string name, std::unique_ptr<T> component)
    {
        static_assert(std::is_base_of<Component, T>::value, "T must derive from Component");
        components[name] = std::move(component);
        components[name]->owner = owner;
    }

    /**
     * Create a component and add it to the MultiComponent.
     *
     * @param name The name to give the component.
     * @param args The arguments to forward to the component constructor.
     * @return A pointer to the added component.
     */
    template <typename... TArgs>
    T* add_component(std::string name, TArgs&&... args)
    {
        static_assert(std::is_base_of<Component, T>::value, "T must derive from Component");
        auto new_component = std::make_unique<T>(std::forward<TArgs>(args)...);
        T* component_ptr = new_component.get();
        add_component(name, std::move(new_component));
        return component_ptr;
    }

    /**
     * Get a component by name.
     *
     * @param name The name of the component.
     * @return A pointer to the component.
     */
    T* get_component(std::string name)
    {
        return components[name].get();
    }
};

/**
 * A component for rendering text.
 * Depends on FontManager.
 */
class TextComponent : public Component
{
public:
    FontManager* font_manager;
    std::string text;
    std::string font_name;
    int font_size = 20;
    Color color = WHITE;
    Vector2 position = {0, 0};
    float rotation = 0.0f;

    /**
     * Constructor for TextComponent.
     *
     * @param text The text to display.
     * @param font_name The name of the font to use.
     * @param font_size The size of the font.
     * @param color The color of the text.
     */
    TextComponent(std::string text, std::string font_name = "default", int font_size = 20, Color color = WHITE) :
        text(text),
        font_name(font_name),
        font_size(font_size),
        color(color)
    {
    }

    /**
     * Initialize the text component.
     */
    void init() override
    {
        font_manager = owner->scene->game->get_manager<FontManager>();
    }

    /**
     * Draw the text.
     */
    void draw() override
    {
        DrawTextEx(font_manager->get_font(font_name),
                   text.c_str(),
                   position,
                   static_cast<float>(font_size),
                   1.0f,
                   color);
    }

    /**
     * Set the text to display.
     *
     * @param text The text to display.
     */
    void set_text(const std::string& text)
    {
        this->text = text;
    }

    /**
     * Set the color of the text.
     *
     * @param color The color to set.
     */
    void set_color(Color color)
    {
        this->color = color;
    }

    /**
     * Set the font size.
     *
     * @param font_size The font size to set.
     */
    void set_font_size(int font_size)
    {
        this->font_size = font_size;
    }

    /**
     * Set the font by name.
     *
     * @param font_name The name of the font to set.
     */
    void set_font(const std::string& font_name)
    {
        this->font_name = font_name;
    }

    /**
     * Set the position of the text.
     *
     * @param position The position to set.
     */
    void set_position(Vector2 position)
    {
        this->position = position;
    }

    /**
     * Set the rotation of the text.
     *
     * @param rotation The rotation to set.
     */
    void set_rotation(float rotation)
    {
        this->rotation = rotation;
    }
};

/**
 * A component for playing sounds.
 * Depends on SoundService.
 */
class SoundComponent : public Component
{
public:
    std::string filename;
    Sound sound;
    float volume = 1.0f;
    float pitch = 1.0f;
    float pan = 0.5f;

    /**
     * Constructor for SoundComponent.
     *
     * @param filename The filename of the sound to load.
     * @param volume The initial volume of the sound.
     * @param pitch The initial pitch of the sound.
     */
    SoundComponent(std::string filename, float volume = 1.0f, float pitch = 1.0f, float pan = 0.5f) :
        filename(filename),
        volume(volume),
        pitch(pitch),
        pan(pan)
    {
    }

    /**
     * Initialize the sound component.
     */
    void init() override
    {
        auto sound_service = owner->scene->get_service<SoundService>();
        sound = sound_service->get_sound(filename);
    }

    /**
     * Play the sound.
     */
    void play()
    {
        PlaySound(sound);
    }

    /**
     * Stop the sound.
     */
    void stop()
    {
        StopSound(sound);
    }

    /**
     * Set the volume of the sound.
     *
     * @param volume The volume to set.
     */
    void set_volume(float volume)
    {
        this->volume = volume;
        SetSoundVolume(sound, volume);
    }

    /**
     * Set the pitch of the sound.
     *
     * @param pitch The pitch to set.
     */
    void set_pitch(float pitch)
    {
        this->pitch = pitch;
        SetSoundPitch(sound, pitch);
    }

    /**
     * Set the pan of the sound.
     *
     * @param pan The pan to set, between 0.0 (left) and 1.0 (right).
     */
    void set_pan(float pan)
    {
        this->pan = pan;
        SetSoundPan(sound, pan);
    }

    /**
     * Check if the sound is currently playing.
     *
     * @return True if the sound is playing, false otherwise.
     */
    bool is_playing()
    {
        return IsSoundPlaying(sound);
    }
};

/**
 * A component for a Box2D physics body.
 * Depends on PhysicsService.
 */
class BodyComponent : public Component
{
public:
    b2BodyId id = b2_nullBodyId;
    std::function<void(BodyComponent&)> build;
    PhysicsService* physics;

    BodyComponent() {}

    /**
     * Constructor for BodyComponent with existing body ID.
     *
     * @param id The Box2D body ID.
     */
    BodyComponent(b2BodyId id) : id(id) {}

    /**
     * Specify a lambda for creating the physics body which will be called during init.
     * It is the user's responsibility to assign the body id to id in this function.
     *
     * @param build A user provided function for creating a physics body.
     */
    BodyComponent(std::function<void(BodyComponent&)> build = {}) : build(std::move(build)) {}

    ~BodyComponent()
    {
        if (b2Body_IsValid(id))
        {
            b2DestroyBody(id);
        }
    }

    /**
     * Initialize the body component.
     */
    void init() override
    {
        physics = owner->scene->get_service<PhysicsService>();
        if (build)
        {
            build(*this);
        }
    }

    /**
     * Enable the body in the physics simulation.
     */
    void enable()
    {
        b2Body_Enable(id);
    }

    /**
     * Disable the body in the physics simulation.
     */
    void disable()
    {
        b2Body_Disable(id);
    }

    /**
     * Get the position of the body in meters.
     */
    b2Vec2 get_position_meters() const
    {
        return b2Body_GetPosition(id);
    }

    /**
     * Get the position of the body in pixels.
     */
    Vector2 get_position_pixels() const
    {
        return physics->convert_to_pixels(get_position_meters());
    }

    /**
     * Set the position of the body in meters.
     *
     * @param meters The position in meters.
     */
    void set_position(b2Vec2 meters)
    {
        b2Rot rotation = b2Body_GetRotation(id);
        b2Body_SetTransform(id, meters, rotation);
    }

    /**
     * Set the position of the body in pixels.
     *
     * @param pixels The position in pixels.
     */
    void set_position(Vector2 pixels)
    {
        set_position(physics->convert_to_meters(pixels));
    }

    /**
     * Set the rotation of the body in degrees.
     *
     * @param degrees The rotation in degrees.
     */
    void set_rotation(float degrees)
    {
        b2Vec2 position = b2Body_GetPosition(id);
        b2Rot rotation = b2MakeRot(degrees * DEG2RAD);
        b2Body_SetTransform(id, position, rotation);
    }

    /**
     * Get the velocity of the body in meters per second.
     *
     * @return The velocity in meters per second.
     */
    b2Vec2 get_velocity_meters() const
    {
        return b2Body_GetLinearVelocity(id);
    }

    /**
     * Get the velocity of the body in pixels per second.
     *
     * @return The velocity in pixels per second.
     */
    Vector2 get_velocity_pixels() const
    {
        return physics->convert_to_pixels(get_velocity_meters());
    }

    /**
     * Set the velocity of the body in meters per second.
     *
     * @param meters_per_second The velocity in meters per second.
     */
    void set_velocity(b2Vec2 meters_per_second)
    {
        b2Body_SetLinearVelocity(id, meters_per_second);
    }

    /**
     * Set the velocity of the body in pixels per second.
     *
     * @param pixels_per_second The velocity in pixels per second.
     */
    void set_velocity(Vector2 pixels_per_second)
    {
        set_velocity(physics->convert_to_meters(pixels_per_second));
    }

    /**
     * Get the rotation of the body in degrees.
     *
     * @return The rotation in degrees.
     */
    float get_rotation() const
    {
        auto rot = b2Body_GetRotation(id);
        return b2Rot_GetAngle(rot) * RAD2DEG;
    }

    /**
     * Get a list of all bodies colliding with this one.
     * https://box2d.org/documentation/md_simulation.html#autotoc_md94
     *
     * @return A list of b2BodyIds that are touching this one. Combine with User Data to get your objects.
     */
    std::vector<b2BodyId> get_contacts()
    {
        // Choose 10 as an arbitrary max number of contacts on the body.
        constexpr int capacity = 10;
        b2ContactData contact_data[capacity];

        int count = b2Body_GetContactData(id, contact_data, capacity);
        std::vector<b2BodyId> contacts;
        for (int i = 0; i < count; i++)
        {
            auto contact = contact_data[i];
            auto body_a = b2Shape_GetBody(contact.shapeIdA);
            auto body_b = b2Shape_GetBody(contact.shapeIdB);
            auto body = body_a == id ? body_b : body_a;
            contacts.push_back(body);
        }

        // Remove duplicate bodies.
        std::sort(contacts.begin(), contacts.end());
        contacts.erase(std::unique(contacts.begin(), contacts.end()), contacts.end());
        return contacts;
    }

    /**
     * Get a list of all bodies overlapping with sensors in this body.
     * The shape definitions must have isSensor and enableSensorEvents set.
     * https://box2d.org/documentation/md_simulation.html#autotoc_md81
     *
     * @return A list of b2BodyIds that are overlapping the sensor shapes in this body. Combine with User Data to get
     * your objects.
     */
    std::vector<b2BodyId> get_sensor_overlaps()
    {
        // Choose 10 as an arbitrary max number of shapes on the body.
        constexpr int shape_capacity = 10;
        b2ShapeId shapes[shape_capacity];
        int shape_count = b2Body_GetShapes(id, shapes, shape_capacity);

        std::vector<b2BodyId> contacts;
        for (int i = 0; i < shape_count; i++)
        {
            auto shape = shapes[i];
            if (b2Shape_IsSensor(shape))
            {
                // Choose 10 as an arbitrary max number of contacts on the sensor shape.
                constexpr int shape_capacity = 10;
                b2ShapeId shapes[shape_capacity];
                int shape_count = b2Shape_GetSensorOverlaps(shape, shapes, shape_capacity);

                for (int j = 0; j < shape_count; j++)
                {
                    auto shape = shapes[j];
                    auto body = b2Shape_GetBody(shape);
                    // Check if body is already in contacts to avoid duplicates.
                    if (std::find(contacts.begin(), contacts.end(), body) == contacts.end())
                    {
                        contacts.push_back(body);
                    }
                }
            }
        }

        // Remove duplicate bodies.
        std::sort(contacts.begin(), contacts.end());
        contacts.erase(std::unique(contacts.begin(), contacts.end()), contacts.end());
        return contacts;
    }
};

/**
 * A component for rendering a sprite.
 * Depends on TextureService.
 */
class SpriteComponent : public Component
{
public:
    std::string filename;
    BodyComponent* body = nullptr;

    Texture2D sprite;
    Vector2 position = {0, 0};
    float rotation = 0.0f;
    float scale = 1.0f;
    Color tint = WHITE;
    bool is_active = true;

    /**
     * Constructor for SpriteComponent.
     *
     * @param filename The filename of the texture to load.
     */
    SpriteComponent(std::string filename) : filename(filename) {}

    /**
     * Constructor for SpriteComponent with optional BodyComponent to follow.
     *
     * @param body The BodyComponent to follow for position and rotation.
     * @param filename The filename of the texture to load.
     */
    SpriteComponent(std::string filename, BodyComponent* body) : filename(filename), body(body) {}

    /**
     * Initialize the sprite component.
     */
    void init() override
    {
        auto texture_service = owner->scene->get_service<TextureService>();
        sprite = texture_service->get_texture(filename);
    }

    /**
     * Draw the sprite.
     */
    void draw() override
    {
        if (!is_active)
        {
            return;
        }

        if (body)
        {
            position = body->get_position_pixels();
            rotation = body->get_rotation();
        }

        Rectangle source = {0, 0, (float)sprite.width, (float)sprite.height};
        Rectangle dest = {position.x, position.y, (float)sprite.width * scale, (float)sprite.height * scale};
        Vector2 origin = {sprite.width / 2.0f * scale, sprite.height / 2.0f * scale};

        DrawTexturePro(sprite, source, dest, origin, rotation, tint);
    }

    /**
     * Set the position of the sprite.
     *
     * @param position The position to set.
     */
    void set_position(Vector2 position)
    {
        this->position = position;
    }

    /**
     * Set the rotation of the sprite.
     *
     * @param rotation The rotation to set in degrees.
     */
    void set_rotation(float rotation)
    {
        this->rotation = rotation;
    }

    /**
     * Set the scale of the sprite.
     *
     * @param scale The scale to set.
     */
    void set_scale(float scale)
    {
        this->scale = scale;
    }

    /**
     * Set the tint color of the sprite.
     *
     * @param tint The tint color to set.
     */
    void set_tint(Color tint)
    {
        this->tint = tint;
    }

    /**
     * Set whether the sprite is active or not.
     * The sprite will not be drawn if inactive.
     *
     * @param active True to make the sprite active, false to deactivate it.
     */
    void set_active(bool active)
    {
        is_active = active;
    }
};

/**
 * A class for handling frame-based animations.
 * Depends on TextureService.
 */
class Animation
{
public:
    std::vector<Texture2D> frames;
    float fps = 15.0f;
    float frame_timer = 0.0f;
    bool loop = true;

    int current_frame = 0;
    bool playing = true;
    bool is_active = true;

    /**
     * Constructor for Animation.
     *
     * @param frames The frames of the animation as Texture2D objects.
     * @param fps The frames per second of the animation.
     * @param loop Whether the animation should loop or not.
     */
    Animation(const std::vector<Texture2D>& frames, float fps = 15.0f, bool loop = true) :
        frames(frames),
        fps(fps),
        frame_timer(1.0f / fps),
        loop(loop)
    {
    }

    /**
     * Constructor for Animation that loads frames from filenames.
     *
     * @param texture_service The TextureService to load textures from.
     * @param filenames The filenames of the frames of the animation.
     * @param fps The frames per second of the animation.
     * @param loop Whether the animation should loop or not.
     */
    Animation(TextureService* texture_service,
              const std::vector<std::string>& filenames,
              float fps = 15.0f,
              bool loop = true) :
        fps(fps),
        frame_timer(1.0f / fps),
        loop(loop)
    {
        for (const auto& filename : filenames)
        {
            frames.push_back(texture_service->get_texture(filename));
        }
    }

    /**
     * Update the animation.
     *
     * @param delta_time The time elapsed since the last frame.
     */
    void update(float delta_time)
    {
        if (frames.empty())
        {
            return;
        }
        if (!playing || !is_active)
        {
            return;
        }

        frame_timer -= delta_time;
        if (frame_timer <= 0.0f)
        {
            frame_timer = 1.0f / fps;
            current_frame++;
        }

        if (current_frame > frames.size() - 1)
        {
            if (loop)
                current_frame = 0;
            else
            {
                current_frame = (int)frames.size() - 1;
            }
        }
    }

    /**
     * Draw the animation.
     *
     * @param position The position to draw the animation at.
     * @param rotation The rotation of the animation in degrees.
     * @param tint The tint color to apply to the animation.
     */
    void draw(Vector2 position, float rotation = 0.0f, Color tint = WHITE)
    {
        if (!is_active)
        {
            return;
        }

        auto sprite = frames[current_frame];
        DrawTexturePro(sprite,
                       {0.0f, 0.0f, static_cast<float>(sprite.width), static_cast<float>(sprite.height)},
                       {position.x, position.y, static_cast<float>(sprite.width), static_cast<float>(sprite.height)},
                       {static_cast<float>(sprite.width) / 2.0f, static_cast<float>(sprite.height) / 2.0f},
                       rotation,
                       tint);
    }

    /**
     * Draw the animation with a specific origin.
     *
     * @param position The position to draw the animation at.
     * @param origin The origin point for rotation and scaling.
     * @param rotation The rotation of the animation in degrees.
     * @param scale The scale of the animation.
     * @param flip_x Whether to flip the animation horizontally.
     * @param flip_y Whether to flip the animation vertically.
     * @param tint The tint color to apply to the animation.
     */
    void draw(Vector2 position,
              Vector2 origin,
              float rotation = 0.0f,
              float scale = 1.0f,
              bool flip_x = false,
              bool flip_y = false,
              Color tint = WHITE)
    {
        if (!is_active)
        {
            return;
        }

        auto sprite = frames[current_frame];
        DrawTexturePro(sprite,
                       {0.0f,
                        0.0f,
                        static_cast<float>(sprite.width) * (flip_x ? -1.0f : 1.0f),
                        static_cast<float>(sprite.height) * (flip_y ? -1.0f : 1.0f)},
                       {position.x,
                        position.y,
                        static_cast<float>(sprite.width) * scale,
                        static_cast<float>(sprite.height) * scale},
                       origin * scale,
                       rotation,
                       tint);
    }

    /**
     * Play the animation.
     */
    void play()
    {
        playing = true;
    }

    /**
     * Pause the animation.
     */
    void pause()
    {
        playing = false;
    }

    /**
     * Stop the animation and reset to the first frame.
     */
    void stop()
    {
        playing = false;
        frame_timer = 1.0f / fps;
        current_frame = 0;
    }
};

/**
 * A component for controlling animations.
 * Depends on TextureService.
 */
class AnimationController : public Component
{
public:
    std::unordered_map<std::string, std::unique_ptr<Animation>> animations;
    Animation* current_animation = nullptr;
    Vector2 position = {0.0f, 0.0f};
    float rotation = 0.0f;
    Vector2 origin = {0.0f, 0.0f};
    float scale = 1.0f;
    bool flip_x = false;
    bool flip_y = false;
    BodyComponent* body = nullptr;

    AnimationController() = default;

    /**
     * Constructor for AnimationController that follows a BodyComponent.
     *
     * @param body The BodyComponent to follow for position and rotation.
     */
    AnimationController(BodyComponent* body) : body(body) {}

    /**
     * Update the animation controller.
     *
     * @param delta_time The time elapsed since the last frame.
     */
    void update(float delta_time) override
    {
        if (current_animation)
        {
            current_animation->update(delta_time);
        }
    }

    /**
     * Draw the current animation.
     */
    void draw() override
    {
        if (body)
        {
            position = body->get_position_pixels();
            rotation = body->get_rotation();
        }

        if (current_animation)
        {
            current_animation->draw(position, origin, rotation, scale, flip_x, flip_y);
        }
    }

    /**
     * Add an existing animation to the controller.
     *
     * @param name The name to give the animation.
     * @param animation The animation to add.
     */
    void add_animation(const std::string& name, std::unique_ptr<Animation> animation)
    {
        animations[name] = std::move(animation);
        if (!current_animation)
        {
            current_animation = animations[name].get();
            auto sprite = current_animation->frames[current_animation->current_frame];
            origin = {sprite.width / 2.0f, sprite.height / 2.0f};
        }
    }

    /**
     * Create an animation and add it to the controller.
     *
     * @param name The name to give the animation.
     * @param args The arguments to forward to the Animation constructor.
     * @return A pointer to the added animation.
     */
    template <typename... TArgs>
    Animation* add_animation(const std::string& name, TArgs&&... args)
    {
        auto texture_service = owner->scene->get_service<TextureService>();
        auto new_animation = std::make_unique<Animation>(texture_service, std::forward<TArgs>(args)...);
        Animation* animation_ptr = new_animation.get();
        add_animation(name, std::move(new_animation));
        return animation_ptr;
    }

    /**
     * Get an animation by name.
     *
     * @param name The name of the animation.
     * @return A pointer to the animation.
     */
    Animation* get_animation(const std::string& name)
    {
        return animations[name].get();
    }

    /**
     * Play the current animation.
     */
    void play()
    {
        if (current_animation)
        {
            current_animation->play();
        }
    }

    /**
     * Play an animation by name.
     *
     * @param name The name of the animation to play.
     */
    void play(const std::string& name)
    {
        auto it = animations.find(name);
        if (it != animations.end())
        {
            current_animation = it->second.get();
            current_animation->play();
            auto sprite = current_animation->frames[current_animation->current_frame];
        }
    }

    /**
     * Pause the current animation.
     */
    void pause()
    {
        if (current_animation)
        {
            current_animation->pause();
        }
    }

    /**
     * Set whether the current animation is playing or paused.
     *
     * @param play True to play the animation, false to pause it.
     */
    void set_play(bool play)
    {
        if (current_animation)
        {
            if (play)
            {
                current_animation->play();
            }
            else
            {
                current_animation->pause();
            }
        }
    }

    /**
     * Stop the current animation.
     */
    void stop()
    {
        if (current_animation)
        {
            current_animation->stop();
        }
    }

    /**
     * Set the position of the animation.
     *
     * @param pos The position to set.
     */
    void set_position(Vector2 pos)
    {
        position = pos;
    }

    /**
     * Set the rotation of the animation.
     *
     * @param rot The rotation to set in degrees.
     */
    void set_rotation(float rot)
    {
        rotation = rot;
    }

    /**
     * Set the origin of the animation.
     *
     * @param orig The origin to set.
     */
    void set_origin(Vector2 orig)
    {
        origin = orig;
    }

    /**
     * Set the scale of the animation.
     *
     * @param s The scale to set.
     */
    void set_scale(float s)
    {
        scale = s;
    }

    /**
     * Set whether to flip the animation horizontally.
     *
     * @param fx True to flip horizontally, false otherwise.
     */
    void set_flip_x(bool fx)
    {
        flip_x = fx;
    }

    /**
     * Set whether to flip the animation vertically.
     *
     * @param fy True to flip vertically, false otherwise.
     */
    void set_flip_y(bool fy)
    {
        flip_y = fy;
    }
};

/**
 * Parameters for PlatformerMovementComponent.
 */
struct PlatformerMovementParams
{
    float width = 24.0f; // pixels
    float height = 40.0f; // pixels

    // Movement
    float max_speed = 220.0f; // pixels / second
    float accel = 2000.0f; // pixels / second / second
    float decel = 2500.0f; // pixels / second / second

    // Gravity / jump
    float gravity = 1400.0f; // pixels / second / second
    float jump_speed = 520.0f; // pixels / second
    float fall_speed = 1200.0f; // pixels / second
    float jump_cutoff_multiplier = 0.45f; // jump multiplier when the jump button is released early

    // Forgiveness
    float coyote_time = 0.08f; // seconds
    float jump_buffer = 0.10f; // seconds
};

/**
 * A component for 2D platformer movement.
 * Depends on PhysicsService and BodyComponent.
 */
class PlatformerMovementComponent : public Component
{
public:
    PlatformerMovementParams p;
    PhysicsService* physics;
    BodyComponent* body;

    bool grounded = false;
    bool on_wall_left = false;
    bool on_wall_right = false;
    float coyote_timer = 0.0f;
    float jump_buffer_timer = 0.0f;

    float move_x = 0;
    bool jump_pressed = false;
    bool jump_held = false;

    /**
     * Constructor for PlatformerMovementComponent.
     *
     * @param p The movement parameters.
     */
    PlatformerMovementComponent(PlatformerMovementParams p) : p(p) {}

    /**
     * Initialize the movement component.
     */
    void init() override
    {
        physics = owner->scene->get_service<PhysicsService>();
        body = owner->get_component<BodyComponent>();
    }

    /**
     * Update the movement component.
     *
     * @param delta_time The time elapsed since the last frame.
     */
    void update(float delta_time) override
    {
        if (!b2Body_IsValid(body->id))
        {
            return;
        }

        coyote_timer = std::max(0.0f, coyote_timer - delta_time);
        jump_buffer_timer = std::max(0.0f, jump_buffer_timer - delta_time);

        if (jump_pressed)
        {
            jump_buffer_timer = p.jump_buffer;
        }

        // Grounded check
        grounded = false;
        on_wall_left = false;
        on_wall_right = false;

        // Convert probe distances to meters
        float ray_length = physics->convert_to_meters(4.0f);

        float half_width = physics->convert_to_meters(p.width) / 2.0f;
        float half_height = physics->convert_to_meters(p.height) / 2.0f;

        // Ground: cast down from two points near the feet (left/right)
        auto pos = body->get_position_meters();
        b2Vec2 ground_left_start = {pos.x - half_width, pos.y + half_height};
        b2Vec2 ground_right_start = {pos.x + half_width, pos.y + half_height};
        b2Vec2 ground_translation = {0, ray_length};
        const b2WorldId world = physics->world;

        RayHit left_ground_hit = raycast_closest(world, body->id, ground_left_start, ground_translation);
        RayHit right_ground_hit = raycast_closest(world, body->id, ground_right_start, ground_translation);
        grounded = left_ground_hit.hit || right_ground_hit.hit;

        // Walls: cast left/right at mid-body height
        b2Vec2 mid = {pos.x, pos.y};
        b2Vec2 wall_left_start = {pos.x - half_width, mid.y};
        b2Vec2 wall_left_translation = {-ray_length, 0};
        b2Vec2 wall_right_start = {pos.x + half_width, mid.y};
        b2Vec2 wall_right_translation = {ray_length, 0};

        RayHit left_wall_hit = raycast_closest(world, body->id, wall_left_start, wall_left_translation);
        RayHit right_wall_hit = raycast_closest(world, body->id, wall_right_start, wall_right_translation);

        on_wall_left = left_wall_hit.hit;
        on_wall_right = right_wall_hit.hit;
        if (grounded)
        {
            coyote_timer = p.coyote_time;
        }

        float target_vx = move_x * p.max_speed;

        auto v = body->get_velocity_pixels();

        if (std::fabs(target_vx) > 0.001f)
        {
            float a = p.accel;
            v.x = move_towards(v.x, target_vx, a * delta_time);
        }
        else
        {
            float a = p.decel;
            v.x = move_towards(v.x, 0.0f, a * delta_time);
        }

        // Gravity (custom)
        v.y += p.gravity * delta_time;
        v.y = std::max(-p.fall_speed, std::min(p.fall_speed, v.y));

        // Jump
        const bool can_jump = (grounded || coyote_timer > 0.0f);
        if (jump_buffer_timer > 0.0f && can_jump)
        {
            v.y = -p.jump_speed;
            jump_buffer_timer = 0.0f;
            coyote_timer = 0.0f;
            grounded = false;
        }

        // Variable jump height: cut upward velocity when jump released
        if (!jump_held && v.y < 0.0f)
        {
            v.y *= p.jump_cutoff_multiplier;
        }

        // Write velocity back
        body->set_velocity(v);
    }

    /**
     * Calculates a value moved towards a target by a maximum delta.
     *
     * @param current The current value.
     * @param target The target value.
     * @param max_delta The maximum change that can be applied.
     * @return The new value after moving towards the target.
     */
    static float move_towards(float current, float target, float max_delta)
    {
        float delta = target - current;
        if (std::fabs(delta) <= max_delta)
            return target;
        return current + (delta > 0 ? max_delta : -max_delta);
    }

    /**
     * Set the input for movement.
     *
     * @param horizontal_speed The horizontal speed input (-1.0 to 1.0).
     * @param jump_pressed Whether the jump button was pressed this frame.
     * @param jump_held Whether the jump button is currently held down.
     */
    void set_input(float horizontal_speed, bool jump_pressed, bool jump_held)
    {
        move_x = horizontal_speed;
        this->jump_pressed = jump_pressed;
        this->jump_held = jump_held;
    }
};

struct TopDownMovementParams
{
    float max_speed = 300.0f; // max speed in px/s
    float accel = 1200.0f; // accel when holding input
    float friction = 1200.0f; // decel when no input
    float deadzone = 0.1f; // input deadzone
};

/**
 * A component for 2D top-down movement.
 * Depends on PhysicsService and BodyComponent.
 *
 * Movement is controlled by setting a 2D input vector (move_x, move_y),
 * and this component accelerates/decelerates the body towards a target
 * velocity using simple acceleration + friction.
 */
class TopDownMovementComponent : public Component
{
public:
    TopDownMovementParams p;
    PhysicsService* physics = nullptr;
    BodyComponent* body = nullptr;

    // Raw input in [-1, 1] range for each axis.
    float move_x = 0.0f;
    float move_y = 0.0f;

    // Store last facing direction for aiming/animation.
    float facing_dir = 0.0f;

    TopDownMovementComponent(TopDownMovementParams p) : p(p) {}

    void init() override
    {
        physics = owner->scene->get_service<PhysicsService>();
        body = owner->get_component<BodyComponent>();
    }

    void update(float delta_time) override
    {
        if (!b2Body_IsValid(body->id))
        {
            return;
        }

        // Current velocity in pixels/sec (assuming your BodyComponent uses this).
        Vector2 v = body->get_velocity_pixels();

        // Build desired movement input vector.
        Vector2 input = {move_x, move_y};
        float input_len_sq = input.x * input.x + input.y * input.y;

        Vector2 desired_vel = {0.0f, 0.0f};

        // Deadzone.
        if (input_len_sq > p.deadzone * p.deadzone)
        {
            desired_vel.x = input.x * p.max_speed;
            desired_vel.y = input.y * p.max_speed;

            // Update facing direction.
            facing_dir = atan2f(input.y, input.x) * RAD2DEG;

            // Accelerate towards desired velocity.
            v = move_towards_vec(v, desired_vel, p.accel * delta_time);
        }
        else
        {
            // No input: apply friction to slow down.
            v = apply_friction(v, p.friction * delta_time);
        }

        // Clamp to max speed just in case.
        float speed_sq = v.x * v.x + v.y * v.y;
        float max_speed_sq = p.max_speed * p.max_speed;
        if (speed_sq > max_speed_sq)
        {
            float speed = std::sqrt(speed_sq);
            float scale = p.max_speed / speed;
            v.x *= scale;
            v.y *= scale;
        }

        body->set_velocity(v);
    }

    /**
     * Move a velocity vector towards a target vector by at most max_delta length.
     */
    static Vector2 move_towards_vec(const Vector2& current, const Vector2& target, float max_delta)
    {
        Vector2 delta = {target.x - current.x, target.y - current.y};
        float len = std::sqrt(delta.x * delta.x + delta.y * delta.y);
        if (len <= max_delta || len < 1e-5f)
        {
            return target;
        }
        float scale = max_delta / len;
        return Vector2{current.x + delta.x * scale, current.y + delta.y * scale};
    }

    /**
     * Apply friction to a velocity vector (reduce its magnitude).
     * `friction_delta` is how much speed we remove this frame.
     */
    static Vector2 apply_friction(const Vector2& v, float friction_delta)
    {
        float speed = std::sqrt(v.x * v.x + v.y * v.y);
        if (speed < 1e-5f)
        {
            return Vector2{0.0f, 0.0f};
        }

        float new_speed = speed - friction_delta;
        if (new_speed <= 0.0f)
        {
            return Vector2{0.0f, 0.0f};
        }

        float scale = new_speed / speed;
        return Vector2{v.x * scale, v.y * scale};
    }

    /**
     * Set the input for movement.
     *
     * @param horizontal Horizontal input (-1.0 to 1.0).
     * @param vertical   Vertical input   (-1.0 to 1.0).
     */
    void set_input(float horizontal, float vertical)
    {
        move_x = horizontal;
        move_y = vertical;
    }
};
