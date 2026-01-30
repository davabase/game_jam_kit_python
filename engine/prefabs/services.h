#pragma once

#include <LDtkLoader/Project.hpp>

#include "engine/framework.h"
#include "engine/physics_debug.h"
#include "engine/raycasts.h"

/**
 * For when you want multiple of the same service.
 */
template <typename T>
class MultiService : public Service
{
public:
    std::unordered_map<std::string, std::unique_ptr<T>> services;

    MultiService() = default;

    /**
     * Initialize all services.
     */
    void init_service() override
    {
        for (auto& service : services)
        {
            service.second->init();
        }
        Service::init_service();
    }

    /**
     * Update all services.
     */
    void update(float delta_time) override
    {
        for (auto& service : services)
        {
            service.second->update();
        }
        Service::update(delta_time);
    }

    /**
     * Draw all services.
     */
    void draw() override
    {
        for (auto& service : services)
        {
            service.second->draw();
        }
    }

    /**
     * Add a service to the MultiService.
     *
     * @param name The name to give the service.
     * @param service The service to add.
     */
    void add_service(std::string name, std::unique_ptr<T> service)
    {
        static_assert(std::is_base_of<Service, T>::value, "T must derive from Service");
        services[name] = std::move(service);
    }

    /**
     * Create a service and add it to the MultiService.
     *
     * @param name The name to give the service.
     * @param args The arguments to forward to the service constructor.
     * @return A pointer to the added service.
     */
    template <typename... TArgs>
    T* add_service(std::string name, TArgs&&... args)
    {
        static_assert(std::is_base_of<Service, T>::value, "T must derive from Service");
        auto new_service = std::make_unique<T>(std::forward<TArgs>(args)...);
        T* service_ptr = new_service.get();
        add_service(name, std::move(new_service));
        return service_ptr;
    }

    /**
     * Get a service by name.
     *
     * @param name The name of the service.
     * @return A pointer to the service.
     */
    T* get_service(std::string name)
    {
        return services[name].get();
    }
};

/**
 * Service for managing textures.
 * Useful when you don't want to load the same texture multiple times.
 */
class TextureService : public Service
{
public:
    std::unordered_map<std::string, Texture2D> textures;

    TextureService() = default;
    ~TextureService()
    {
        for (auto& pair : textures)
        {
            UnloadTexture(pair.second);
        }
    }

    /**
     * Get a texture by filename.
     * Loads the texture if it is not already loaded.
     *
     * @param filename The filename of the texture.
     * @return A reference to the texture.
     */
    Texture2D& get_texture(const std::string& filename)
    {
        if (textures.find(filename) == textures.end())
        {
            Texture2D texture = LoadTexture(filename.c_str());
            textures[filename] = texture;
        }
        return textures[filename];
    }
};

/**
 * Service for managing sounds.
 * Useful when you don't want to load the same sound multiple times and want to play overlapping sounds.
 */
class SoundService : public Service
{
public:
    std::unordered_map<std::string, std::vector<Sound>> sounds;

    SoundService() = default;
    ~SoundService()
    {
        for (auto& pair : sounds)
        {
            // The first sound is a real sound.
            UnloadSound(pair.second[0]);
            for (int i = 1; i < pair.second.size(); i++)
            {
                UnloadSoundAlias(pair.second[i]);
            }
        }
    }

    /**
     * Get a sound by filename.
     * Loads the sound if it is not already loaded.
     * Creates a new alias if the sound is already loaded to allow overlapping sounds.
     *
     * @param filename The filename of the sound.
     * @return A reference to the sound.
     */
    Sound& get_sound(const std::string& filename)
    {
        if (sounds.find(filename) == sounds.end())
        {
            Sound sound = LoadSound(filename.c_str());
            sounds[filename] = {sound};
        }
        else
        {
            // Create a new alias to allow overlapping sounds.
            Sound sound = LoadSoundAlias(sounds[filename][0]);
            sounds[filename].push_back(sound);
        }
        return sounds[filename].back();
    }
};

/**
 * Service for managing the physics world.
 */
class PhysicsService : public Service
{
public:
    b2WorldId world = b2_nullWorldId;
    b2Vec2 gravity = {0.0f, 10.0f};
    float time_step = 1.0f / 60.0f;
    int sub_steps = 6;
    float meters_to_pixels = 30.0f;
    float pixels_to_meters = 1.0f / meters_to_pixels;
    PhysicsDebugRenderer debug_draw;

    /**
     * Constructor for PhysicsService.
     *
     * @param gravity The gravity vector for the physics world.
     * @param time_step The time step for the physics simulation.
     * @param sub_steps The number of sub-steps for the physics simulation.
     * @param meters_to_pixels The scale factor from meters to pixels.
     */
    PhysicsService(b2Vec2 gravity = b2Vec2{0.0f, 10.0f},
                   float time_step = 1.0f / 60.0f,
                   int sub_steps = 6,
                   float meters_to_pixels = 30.0f) :
        gravity(gravity),
        time_step(time_step),
        sub_steps(sub_steps),
        meters_to_pixels(meters_to_pixels),
        pixels_to_meters(1.0f / meters_to_pixels)
    {
    }

    ~PhysicsService()
    {
        if (b2World_IsValid(world))
        {
            b2DestroyWorld(world);
        }
    }

    /**
     * Initialize the physics world.
     */
    void init() override
    {
        b2WorldDef world_def = b2DefaultWorldDef();
        world_def.gravity = gravity;
        world_def.contactHertz = 120;
        world = b2CreateWorld(&world_def);
        debug_draw.init(meters_to_pixels);
    }

    /**
     * Update the physics world.
     *
     * @param delta_time The time elapsed since the last frame.
     */
    void update(float delta_time) override
    {
        if (!b2World_IsValid(world))
        {
            return;
        }
        b2World_Step(world, time_step, sub_steps);
    }

    /**
     * Draw the physics debug information.
     */
    void draw_debug()
    {
        debug_draw.draw_debug(world);
    }

    /**
     * Convert between pixels and meters.
     *
     * @param meters The value in meters.
     * @return The value in pixels.
     */
    Vector2 convert_to_pixels(b2Vec2 meters) const
    {
        const auto converted = meters * meters_to_pixels;
        return {converted.x, converted.y};
    }

    /**
     * Convert between pixels and meters.
     *
     * @param pixels The value in pixels.
     * @return The value in meters.
     */
    b2Vec2 convert_to_meters(Vector2 pixels) const
    {
        const auto converted = pixels * pixels_to_meters;
        return {converted.x, converted.y};
    }

    /**
     * Convert a length from meters to pixels.
     *
     * @param meters The length in meters.
     * @return The length in pixels.
     */
    float convert_to_pixels(float meters) const
    {
        return meters * meters_to_pixels;
    }

    /**
     * Convert a length from pixels to meters.
     *
     * @param pixels The length in pixels.
     * @return The length in meters.
     */
    float convert_to_meters(float pixels) const
    {
        return pixels * pixels_to_meters;
    }

    /**
     * Raycast in pixels.
     *
     * @param ignore Box2d body to ignore.
     * @param from The start point of the ray.
     * @param to The end point of the ray.
     * @return A RayHit struct describing the hit.
     */
    RayHit raycast(b2BodyId ignore, Vector2 from, Vector2 to)
    {
        auto start = convert_to_meters(from);
        auto translation = convert_to_meters(to - from);

        return raycast_closest(world, ignore, start, translation);
    }

    /**
     * Check for circle shape overlaps in pixels.
     *
     * @param center The center of the circle.
     * @param radius The radius of the circle.
     * @param ignore_body The body to ignore.
     * @return A vector of body IDs that overlap with the circle.
     */
    std::vector<b2BodyId> circle_overlap(Vector2 center, float radius, b2BodyId ignore_body = b2_nullBodyId)
    {
        auto center_m = convert_to_meters(center);
        auto radius_m = convert_to_meters(radius);
        return circle_hit(world, ignore_body, center_m, radius_m);
    }

    /**
     * Check for rectangle shape overlaps in pixels.
     *
     * @param rectangle The rectangle to check.
     * @param rotation The rotation of the rectangle in degrees.
     * @param ignore_body The body to ignore.
     * @return A vector of body IDs that overlap with the rectangle.
     */
    std::vector<b2BodyId> rectangle_overlap(Rectangle rectangle,
                                            float rotation = 0.0f,
                                            b2BodyId ignore_body = b2_nullBodyId)
    {
        Vector2 size = {rectangle.width, rectangle.height};
        Vector2 center = {rectangle.x + size.x / 2.0f, rectangle.y + size.y / 2.0f};
        auto size_m = convert_to_meters(size);
        auto center_m = convert_to_meters(center);
        return rectangle_hit(world, ignore_body, center_m, size_m, rotation);
    }
};

/**
 * Hash for ldtk::IntPoint to be used in unordered_map/set.
 */
struct IntPointHash
{
    size_t operator()(const ldtk::IntPoint& p) const noexcept
    {
        std::size_t h1 = std::hash<int>{}(p.x);
        std::size_t h2 = std::hash<int>{}(p.y);
        return h1 ^ (h2 << 1);
    }
};

/**
 * Undirected edge between two IntPoints, stored canonically (a < b).
 */
struct Edge
{
    ldtk::IntPoint a, b;
};

/**
 * Equality operator for Edge.
 *
 * @param e1 The first edge.
 * @param e2 The second edge.
 * @return True if the edges are equal, false otherwise.
 */
static inline bool operator==(const Edge& e1, const Edge& e2)
{
    return e1.a == e2.a && e1.b == e2.b;
}

/**
 * Hash for Edge to be used in unordered_map/set.
 */
struct EdgeHash
{
    size_t operator()(const Edge& e) const noexcept
    {
        IntPointHash h;
        std::size_t h1 = h(e.a);
        std::size_t h2 = h(e.b);
        return h1 ^ (h2 << 1);
    }
};

struct LayerRenderer
{
    RenderTexture2D renderer;
    ldtk::IID layer_iid;
    bool visible = true;
};

/**
 * Service for managing LDtk levels.
 * Depends on TextureService and PhysicsService.
 */
class LevelService : public Service
{
public:
    ldtk::Project project;
    std::string project_file;
    std::string level_name;
    std::vector<std::string> collision_names;
    std::vector<LayerRenderer> renderers;
    std::vector<b2BodyId> layer_bodies;
    float scale = 1.0f;
    PhysicsService* physics;

    /**
     * Constructor for LevelService.
     *
     * @param project_file The path to the LDtk project file.
     * @param level_name The name of the level to load.
     * @param collision_names The names of the layers to create collision bodies for.
     * @param scale The scale factor for the level.
     */
    LevelService(std::string project_file,
                 std::string level_name,
                 std::vector<std::string> collision_names,
                 float scale = 1.0f) :
        project_file(project_file),
        level_name(level_name),
        collision_names(collision_names),
        scale(scale)
    {
    }

    virtual ~LevelService()
    {
        for (auto& renderer : renderers)
        {
            UnloadRenderTexture(renderer.renderer);
        }

        for (auto& body : layer_bodies)
        {
            if (b2Body_IsValid(body))
            {
                b2DestroyBody(body);
            }
        }
    }

    /**
     * Initialize the level service.
     * Loads the LDtk project and level, creates textures and collision bodies.
     */
    void init() override
    {
        if (!FileExists(project_file.c_str()))
        {
            TraceLog(LOG_FATAL, "LDtk file not found: %s", project_file.c_str());
        }
        project.loadFromFile(project_file);
        const auto& world = project.getWorld();
        const auto& levels = world.allLevels();

        bool found = false;
        for (const auto& level : levels)
        {
            if (level.name == level_name)
            {
                found = true;
                break;
            }
        }
        if (!found)
        {
            TraceLog(LOG_FATAL, "LDtk level not found: %s", level_name.c_str());
        }

        physics = scene->get_service<PhysicsService>();

        const auto& level = world.getLevel(level_name);
        const auto& layers = level.allLayers();

        // Loop through all layers and create textures and collisions bodies.
        for (auto& layer : layers)
        {
            if (!layer.hasTileset())
            {
                continue;
            }

            // Load the texture and the renderer.
            auto directory = std::string(GetDirectoryPath(project_file.c_str()));
            auto tileset_file = directory + "/" + layer.getTileset().path;
            if (!FileExists(tileset_file.c_str()))
            {
                TraceLog(LOG_FATAL, "Tileset file not found: %s", tileset_file.c_str());
            }
            auto texture_service = scene->get_service<TextureService>();
            Texture2D texture = texture_service->get_texture(tileset_file);
            RenderTexture2D renderer = LoadRenderTexture(level.size.x, level.size.y);

            // Draw all the tiles.
            const auto& tiles_vector = layer.allTiles();
            BeginTextureMode(renderer);
            // Clear with transparency so we can render layers on top of each other.
            ClearBackground({0, 0, 0, 0});
            for (const auto& tile : tiles_vector)
            {
                const auto& position = tile.getPosition();
                const auto& texture_rect = tile.getTextureRect();
                Vector2 dest = {
                    static_cast<float>(position.x),
                    static_cast<float>(position.y),
                };
                Rectangle src = {static_cast<float>(texture_rect.x),
                                 static_cast<float>(texture_rect.y),
                                 static_cast<float>(texture_rect.width) * (tile.flipX ? -1.0f : 1.0f),
                                 static_cast<float>(texture_rect.height) * (tile.flipY ? -1.0f : 1.0f)};
                DrawTextureRec(texture, src, dest, WHITE);
            }
            EndTextureMode();
            LayerRenderer layer_renderer;
            layer_renderer.renderer = renderer;
            layer_renderer.layer_iid = layer.iid;
            renderers.push_back(layer_renderer);

            // Create bodies.
            const auto& size = layer.getGridSize();

            auto make_edge = [&](ldtk::IntPoint p0, ldtk::IntPoint p1) -> Edge
            {
                if (p1.x < p0.x || (p1.x == p0.x && p1.y < p0.y))
                    std::swap(p0, p1);
                return {p0, p1};
            };

            std::unordered_set<Edge, EdgeHash> edges;

            for (int y = 0; y < size.y; y++)
            {
                for (int x = 0; x < size.x; x++)
                {
                    if (!is_solid(layer, x, y, size))
                        continue;

                    // neighbor empty => boundary edge
                    if (!is_solid(layer, x, y - 1, size))
                        edges.insert(make_edge({x, y}, {x + 1, y}));
                    if (!is_solid(layer, x, y + 1, size))
                        edges.insert(make_edge({x, y + 1}, {x + 1, y + 1}));
                    if (!is_solid(layer, x - 1, y, size))
                        edges.insert(make_edge({x, y}, {x, y + 1}));
                    if (!is_solid(layer, x + 1, y, size))
                        edges.insert(make_edge({x + 1, y}, {x + 1, y + 1}));
                }
            }

            std::unordered_map<ldtk::IntPoint, std::vector<ldtk::IntPoint>, IntPointHash> adj;
            adj.reserve(edges.size() * 2);

            for (auto& e : edges)
            {
                adj[e.a].push_back(e.b);
                adj[e.b].push_back(e.a);
            }

            // Helper to remove an undirected edge from the set as we consume it
            auto erase_edge = [&](ldtk::IntPoint p0, ldtk::IntPoint p1) { edges.erase(make_edge(p0, p1)); };

            // Walk loops
            std::vector<std::vector<ldtk::IntPoint>> loops;

            while (!edges.empty())
            {
                // pick an arbitrary remaining edge
                Edge startE = *edges.begin();
                ldtk::IntPoint start = startE.a;
                ldtk::IntPoint cur = startE.b;
                ldtk::IntPoint prev = start;

                std::vector<ldtk::IntPoint> poly;
                poly.push_back(start);
                poly.push_back(cur);
                erase_edge(start, cur);

                while (!(cur == start))
                {
                    // choose next neighbor that is not prev and still has an edge remaining
                    const auto& nbs = adj[cur];
                    ldtk::IntPoint next = prev; // fallback

                    bool found = false;
                    for (const ldtk::IntPoint& cand : nbs)
                    {
                        if (cand == prev)
                            continue;
                        if (edges.find(make_edge(cur, cand)) != edges.end())
                        {
                            next = cand;
                            found = true;
                            break;
                        }
                    }

                    if (!found)
                    {
                        // Open chain (should be rare for tile boundaries unless the boundary touches the map edge)
                        break;
                    }

                    prev = cur;
                    cur = next;
                    poly.push_back(cur);
                    erase_edge(prev, cur);

                    // safety guard to avoid infinite loops on bad topology
                    if (poly.size() > 100000)
                        break;
                }

                // If closed, last vertex == start; Box2D chains usually want NOT duplicated end vertex.
                if (!poly.empty() && poly.back() == poly.front())
                {
                    poly.pop_back();
                }

                // Only keep valid chains
                if (poly.size() >= 3)
                {
                    // If we're not solid on the right, then we wrapped the wrong way.
                    if (!loop_has_solid_on_right(poly, layer))
                    {
                        std::reverse(poly.begin(), poly.end());
                    }

                    // Not really necessary but here we reduce the number of points on a line to just the ends.
                    // std::vector<ldtk::IntPoint> reduced;
                    // reduced.push_back(poly[0]);
                    // b2Vec2 original_normal = {0, 0};
                    // for (int i = 1; i < poly.size(); i++)
                    // {
                    //     auto first = poly[i - 1];
                    //     auto second = poly[i];
                    //     float length = sqrt((second.x - first.x) * (second.x - first.x) +
                    //                         (second.y - first.y) * (second.y - first.y));
                    //     b2Vec2 normal = {(second.x - first.x) / length, (second.y - first.y) / length};
                    //     if (length == 0)
                    //     {
                    //         normal = {0, 0};
                    //     }
                    //     if (i == 1)
                    //     {
                    //         original_normal = normal;
                    //     }

                    //     if (normal != original_normal)
                    //     {
                    //         reduced.push_back(first);
                    //         original_normal = normal;
                    //     }
                    // }
                    // reduced.push_back(poly.back());
                    // loops.push_back(std::move(reduced));

                    loops.push_back(std::move(poly));
                }
            }

            b2BodyDef bd = b2DefaultBodyDef();
            bd.type = b2_staticBody;
            bd.position = {0, 0};
            assert(b2World_IsValid(physics->world));
            b2BodyId layer_body = b2CreateBody(physics->world, &bd);

            for (auto& loop : loops)
            {
                std::vector<b2Vec2> verts;
                verts.reserve(loop.size());

                for (auto& p : loop)
                {
                    float xpx = p.x * layer.getCellSize() * scale;
                    float ypx = p.y * layer.getCellSize() * scale;
                    verts.push_back(physics->convert_to_meters({xpx, ypx}));
                }

                std::vector<b2SurfaceMaterial> mats;
                for (int i = 0; i < verts.size(); i++)
                {
                    b2SurfaceMaterial mat = b2DefaultSurfaceMaterial();
                    mat.friction = 0.1f;
                    mat.restitution = 0.1f;
                    mats.push_back(mat);
                }

                b2ChainDef cd = b2DefaultChainDef();
                cd.points = verts.data();
                cd.count = (int)verts.size();
                cd.materials = mats.data();
                cd.materialCount = (int)mats.size();
                cd.isLoop = true;
                b2CreateChain(layer_body, &cd);

                layer_bodies.push_back(layer_body);
            }
        }
    }

    /**
     * Draw the level.
     * Draws all the layer renderers.
     */
    void draw() override
    {
        // Draw renderers in reverse.
        for (int i = (int)renderers.size() - 1; i >= 0; i--)
        {
            const auto& layer_renderer = renderers[i];
            if (!layer_renderer.visible)
            {
                continue;
            }
            const auto& renderer = layer_renderer.renderer;
            Rectangle src = {0,
                             0,
                             static_cast<float>(renderer.texture.width),
                             -static_cast<float>(renderer.texture.height)};
            Rectangle dest = {0,
                              0,
                              static_cast<float>(renderer.texture.width) * scale,
                              static_cast<float>(renderer.texture.height) * scale};
            DrawTexturePro(renderer.texture, src, dest, {0}, .0f, WHITE);
        }
    }

    /**
     * Draw a specific layer by its IID.
     *
     * @param layer_id The IID of the layer.
     */
    void draw_layer(ldtk::IID layer_id)
    {
        for (const auto& layer_renderer : renderers)
        {
            if (layer_renderer.layer_iid == layer_id)
            {
                const auto& renderer = layer_renderer.renderer;
                Rectangle src = {0,
                                 0,
                                 static_cast<float>(renderer.texture.width),
                                 -static_cast<float>(renderer.texture.height)};
                Rectangle dest = {0,
                                  0,
                                  static_cast<float>(renderer.texture.width) * scale,
                                  static_cast<float>(renderer.texture.height) * scale};
                DrawTexturePro(renderer.texture, src, dest, {0}, .0f, WHITE);
                return;
            }
        }
    }

    /**
     * Draw a specific layer by its name.
     *
     * @param layer_name The name of the layer.
     */
    void draw_layer(std::string layer_name)
    {
        const auto& level = get_level();
        const auto& layer = level.getLayer(layer_name);
        draw_layer(layer.iid);
    }

    /**
     * Check if a cell in the layer is solid.
     * Used for collision generation.
     *
     * @param layer The LDtk layer.
     * @param x The x coordinate of the cell.
     * @param y The y coordinate of the cell.
     * @param size The size of the layer in cells.
     */
    bool is_solid(const ldtk::Layer& layer, int x, int y, const ldtk::IntPoint& size)
    {
        if (x < 0 || y < 0 || x >= size.x || y >= size.y)
        {
            return false;
        }

        std::string name = layer.getIntGridVal(x, y).name;
        if (std::find(collision_names.begin(), collision_names.end(), name) != collision_names.end())
        {
            return true;
        }
        return false;
    };

    /**
     * Check if there is solid on the right side of a loop of corners.
     * Used to determine loop winding.
     *
     * @param loop_corners The corners of the loop.
     * @param layer The LDtk layer.
     * @return True if there is solid on the right side of the loop, false otherwise.
     */
    bool loop_has_solid_on_right(const std::vector<ldtk::IntPoint>& loop_corners, const ldtk::Layer& layer)
    {
        const int cell_size = layer.getCellSize();

        // Pick an edge with non-zero length.
        int n = (int)loop_corners.size();
        for (int i = 0; i < n; ++i)
        {
            ldtk::IntPoint a = loop_corners[i];
            ldtk::IntPoint b = loop_corners[(i + 1) % n];
            int dx = b.x - a.x;
            int dy = b.y - a.y;
            if (dx == 0 && dy == 0)
                continue;

            // Convert corner coords to scaled pixel coords.
            float ax = a.x * cell_size * scale;
            float ay = a.y * cell_size * scale;
            float bx = b.x * cell_size * scale;
            float by = b.y * cell_size * scale;

            // Edge direction.
            float ex = bx - ax;
            float ey = by - ay;
            float len = std::sqrt(ex * ex + ey * ey);
            if (len < 1e-4f)
            {
                continue;
            }
            ex /= len;
            ey /= len;

            // Right normal = (-ey, ex)
            float rx = -ey;
            float ry = ex;

            // Midpoint of the edge.
            float mx = 0.5f * (ax + bx);
            float my = 0.5f * (ay + by);

            // Sample a point slightly to the right, a quarter cell away.
            float eps = 0.25f * cell_size * scale;
            float sx = mx + rx * eps;
            float sy = my + ry * eps;

            // Map sample pixel to grid cell.
            int gx = (int)std::floor(sx / (cell_size * scale));
            int gy = (int)std::floor(sy / (cell_size * scale));

            return is_solid(layer, gx, gy, layer.getGridSize());
        }

        // Fallback: if degenerate, say false
        return false;
    }

    /**
     * Set the visibility of a layer by its IID.
     *
     * @param layer_id The IID of the layer.
     * @param visible True to make the layer visible, false to hide it.
     */
    void set_layer_visibility(ldtk::IID layer_id, bool visible)
    {
        for (auto& layer_renderer : renderers)
        {
            if (layer_renderer.layer_iid == layer_id)
            {
                layer_renderer.visible = visible;
                return;
            }
        }
    }

    /**
     * Set the visibility of a layer by its name.
     *
     * @param layer_name The name of the layer.
     * @param visible True to make the layer visible, false to hide it.
     */
    void set_layer_visibility(std::string layer_name, bool visible)
    {
        const auto& level = get_level();
        const auto& layer = level.getLayer(layer_name);
        for (auto& layer_renderer : renderers)
        {
            if (layer_renderer.layer_iid == layer.iid)
            {
                layer_renderer.visible = visible;
                return;
            }
        }
    }

    /**
     * Get the LDtk world.
     *
     * @return A reference to the LDtk world.
     */
    const ldtk::World& get_world()
    {
        return project.getWorld();
    }

    /**
     * Get the LDtk level.
     *
     * @return A reference to the LDtk level.
     */
    const ldtk::Level& get_level()
    {
        const auto& world = project.getWorld();
        return world.getLevel(level_name);
    }

    /**
     * Get the level size in pixels.
     *
     * @return A Vector2 containing the size of the level.
     */
    Vector2 get_size()
    {
        const auto& level = get_level();
        return {level.size.x * scale, level.size.y * scale};
    }

    /**
     * Get a layer by its name.
     *
     * @param name The name of the layer.
     * @return A reference to the LDtk layer.
     */
    const ldtk::Layer& get_layer_by_name(const std::string& name)
    {
        const auto& level = get_level();
        return level.getLayer(name);
    }

    /**
     * Get all entities across all layers in the level.
     *
     * @return A vector of LDtk entities.
     */
    std::vector<const ldtk::Entity*> get_entities()
    {
        if (!is_init)
        {
            TraceLog(LOG_ERROR, "LDtk project not loaded.");
            return {};
        }
        const auto& level = get_level();
        const auto& layers = level.allLayers();

        std::vector<const ldtk::Entity*> entities;

        for (const auto& layer : layers)
        {
            const auto& layer_entities = layer.allEntities();

            entities.reserve(entities.size() + layer_entities.size());
            for (const auto& entity : layer_entities)
            {
                entities.push_back(&entity);
            }
        }

        return entities;
    }

    /**
     * Get all entities across all layers in the level with the given name.
     *
     * @param name The name of the entities to get.
     * @return A vector of LDtk entities.
     */
    std::vector<const ldtk::Entity*> get_entities_by_name(const std::string& name)
    {
        if (!is_init)
        {
            TraceLog(LOG_ERROR, "LDtk project not loaded.");
            return {};
        }
        const auto& level = get_level();
        const auto& layers = level.allLayers();

        std::vector<const ldtk::Entity*> entities;

        for (const auto& layer : layers)
        {
            const auto& layer_entities = layer.getEntitiesByName(name);

            entities.reserve(entities.size() + layer_entities.size());
            for (const auto& entity : layer_entities)
            {
                entities.push_back(&entity.get());
            }
        }

        return entities;
    }

    /**
     * Get all entities across all layers in the level with the given tag.
     *
     * @param tag The tag of the entities to get.
     * @return A vector of LDtk entities.
     */
    std::vector<const ldtk::Entity*> get_entities_by_tag(const std::string& tag)
    {
        if (!is_init)
        {
            TraceLog(LOG_ERROR, "LDtk project not loaded.");
            return {};
        }
        const auto& level = get_level();
        const auto& layers = level.allLayers();

        std::vector<const ldtk::Entity*> entities;

        for (const auto& layer : layers)
        {
            const auto& layer_entities = layer.getEntitiesByTag(tag);

            entities.reserve(entities.size() + layer_entities.size());
            for (const auto& entity : layer_entities)
            {
                entities.push_back(&entity.get());
            }
        }

        return entities;
    }

    /**
     * Get the first entity across all layers in the level with the given name.
     *
     * @param name The name of the entity to get.
     * @return A pointer to the LDtk entity, or nullptr if not found.
     */
    const ldtk::Entity* get_entity_by_name(const std::string& name)
    {
        auto entities = get_entities_by_name(name);
        if (entities.empty())
        {
            return nullptr;
        }

        return entities[0];
    }

    /**
     * Get the first entity across all layers in the level with the given tag.
     *
     * @param tag The tag of the entity to get.
     * @return A pointer to the LDtk entity, or nullptr if not found.
     */
    const ldtk::Entity* get_entity_by_tag(const std::string& tag)
    {
        auto entities = get_entities_by_tag(tag);
        if (entities.empty())
        {
            return nullptr;
        }

        return entities[0];
    }

    /**
     * Convert a grid point to pixels.
     *
     * @param point The grid point to convert.
     * @return A Vector2 containing the point in pixels.
     */
    Vector2 convert_to_pixels(const ldtk::IntPoint& point) const
    {
        return {point.x * scale, point.y * scale};
    }

    /**
     * Convert a cell point to pixels.
     *
     * @param cell_point The cell point to convert.
     * @param layer The LDtk layer the cell point is in.
     */
    Vector2 convert_cells_to_pixels(const ldtk::IntPoint& cell_point, const ldtk::Layer& layer) const
    {
        float cell_size = static_cast<float>(layer.getCellSize());
        return {cell_point.x * cell_size * scale, cell_point.y * cell_size * scale};
    }

    /**
     * Convert a grid point to meters.
     *
     * @param point The grid point to convert.
     * @return A b2Vec2 containing the point in meters.
     */
    b2Vec2 convert_to_meters(const ldtk::IntPoint& point) const
    {
        return physics->convert_to_meters(convert_to_pixels(point));
    }

    /**
     * Convert pixels to a grid point.
     *
     * @param pixels The pixel position to convert.
     * @return An IntPoint containing the point in grid coordinates.
     */
    ldtk::IntPoint convert_to_grid(const Vector2& pixels) const
    {
        return {static_cast<int>(pixels.x / scale), static_cast<int>(pixels.y / scale)};
    }

    /**
     * Convert meters to a grid point.
     *
     * @param meters The meter position to convert.
     * @return An IntPoint containing the point in grid coordinates.
     */
    ldtk::IntPoint convert_to_grid(const b2Vec2& meters) const
    {
        auto pixels = physics->convert_to_pixels(meters);
        return {static_cast<int>(pixels.x / scale), static_cast<int>(pixels.y / scale)};
    }

    /**
     * Get the position of an entity in pixels.
     *
     * @param entity The entity to get the position of.
     * @return A Vector2 containing the position of the entity in pixels.
     */
    Vector2 get_entity_position(ldtk::Entity* entity)
    {
        return convert_to_pixels(entity->getPosition());
    }

    /**
     * Get the size of an entity in pixels.
     *
     * @param entity The entity to get the size of.
     * @return A Vector2 containing the size of the entity in pixels.
     */
    Vector2 get_entity_size(ldtk::Entity* entity)
    {
        return convert_to_pixels(entity->getSize());
    }
};
