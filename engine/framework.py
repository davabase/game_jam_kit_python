from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
import pyray as rl

T = TypeVar("T")


class Component:
    """Base class for all game object components.

    Attributes:
        owner: The GameObject that owns this component, or None if unassigned.
    """
    def __init__(self) -> None:
        self.owner: Optional[GameObject] = None

    def init(self) -> None:
        """Lifecycle hook called when the component is initialized.

        Returns:
            None
        """
        pass

    def update(self, delta_time: float) -> None:
        """Lifecycle hook called every frame to update the component.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        pass

    def draw(self) -> None:
        """Lifecycle hook called every frame to draw the component.

        Returns:
            None
        """
        pass


class GameObject:
    """Base class for all game objects (entities) in a scene.

    Attributes:
        scene: The Scene this object belongs to.
        components: Mapping of component type to component instance.
        tags: Set of string tags for lookup/filtering.
        is_active: If False, update/draw are skipped.
    """
    def __init__(self) -> None:
        self.scene: Optional[Scene] = None
        self.components: Dict[Type[Any], Component] = {}
        self.tags: set[str] = set()
        self.is_active: bool = True

    def init(self) -> None:
        """Lifecycle hook called when the object is initialized.

        Returns:
            None
        """
        pass

    def update(self, delta_time: float) -> None:
        """Lifecycle hook called every frame to update the object.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        pass

    def draw(self) -> None:
        """Lifecycle hook called every frame to draw the object.

        Returns:
            None
        """
        pass

    def init_object(self) -> None:
        """Initialize the object and its components.

        Returns:
            None
        """
        self.init()
        for component in list(self.components.values()):
            component.init()

    def update_object(self, delta_time: float) -> None:
        """Update the object and its components if active.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        if not self.is_active:
            return
        self.update(delta_time)
        for component in list(self.components.values()):
            component.update(delta_time)

    def draw_object(self) -> None:
        """Draw the object and its components if active.

        Returns:
            None
        """
        if not self.is_active:
            return
        self.draw()
        for component in list(self.components.values()):
            component.draw()

    def add_component(self, component_or_cls: Any, *args: Any, **kwargs: Any) -> Component:
        """Add a component instance or construct one from a class.

        Args:
            component_or_cls: A Component instance or a Component class.
            *args: Positional args forwarded to the component constructor.
            **kwargs: Keyword args forwarded to the component constructor.

        Returns:
            The component instance added.
        """
        if isinstance(component_or_cls, Component):
            component = component_or_cls
        else:
            component = component_or_cls(*args, **kwargs)
        component.owner = self
        key = component.__class__
        if key in self.components:
            print(f"Duplicate component added: {key.__name__}")
        self.components[key] = component
        return component

    def get_component(self, cls: Type[T]) -> Optional[T]:
        """Get a component by type, if present.

        Args:
            cls: Component class to look up.

        Returns:
            The component instance if found, otherwise None.
        """
        component = self.components.get(cls)
        return component if component is None else component  # type: ignore[return-value]

    def add_tag(self, tag: str) -> None:
        """Add a tag to this object.

        Args:
            tag: Tag string to add.

        Returns:
            None
        """
        self.tags.add(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this object.

        Args:
            tag: Tag string to remove.

        Returns:
            None
        """
        self.tags.discard(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if a tag is present.

        Args:
            tag: Tag string to check.

        Returns:
            True if the tag is present, otherwise False.
        """
        return tag in self.tags


class Service:
    """Base class for scene-level services.

    Attributes:
        scene: The Scene this service is attached to.
        is_init: True once init_service has been run.
        is_visible: If False, draw_service is skipped.
    """
    def __init__(self) -> None:
        self.scene: Optional[Scene] = None
        self.is_init: bool = False
        self.is_visible: bool = True

    def init(self) -> None:
        """Lifecycle hook called when the service is initialized.

        Returns:
            None
        """
        pass

    def update(self, delta_time: float) -> None:
        """Lifecycle hook called every frame to update the service.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        pass

    def draw(self) -> None:
        """Lifecycle hook called every frame to draw the service.

        Returns:
            None
        """
        pass

    def init_service(self) -> None:
        """Initialize the service once.

        Returns:
            None
        """
        if self.is_init:
            return
        self.init()
        self.is_init = True

    def draw_service(self) -> None:
        """Draw the service if visible.

        Returns:
            None
        """
        if self.is_visible:
            self.draw()


class Manager:
    """Base class for global managers.

    Attributes:
        is_init: True once init_manager has been run.
    """
    def __init__(self) -> None:
        self.is_init: bool = False

    def init(self) -> None:
        """Lifecycle hook called when the manager is initialized.

        Returns:
            None
        """
        pass

    def init_manager(self) -> None:
        """Initialize the manager once.

        Returns:
            None
        """
        if self.is_init:
            return
        self.init()
        self.is_init = True


class Scene:
    """Base class for scenes that contain objects and services.

    Attributes:
        game_objects: List of GameObjects in the scene.
        services: List of (type, Service) pairs.
        game: Owning Game instance.
        is_init: True once init_scene has been run.
    """
    def __init__(self) -> None:
        self.game_objects: List[GameObject] = []
        self.services: List[Tuple[Type[Any], Service]] = []
        self.game: Optional[Game] = None
        self.is_init: bool = False

    def init_services(self) -> None:
        """Hook to add services before scene init.

        Returns:
            None
        """
        pass

    def init(self) -> None:
        """Lifecycle hook called when the scene initializes.

        Returns:
            None
        """
        pass

    def update(self, delta_time: float) -> None:
        """Lifecycle hook called every frame to update the scene.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        pass

    def draw(self) -> None:
        """Lifecycle hook called every frame to draw the scene.

        Returns:
            None
        """
        pass

    def init_scene(self) -> None:
        """Initialize services, scene, and objects.

        Returns:
            None
        """
        if self.is_init:
            return
        self.init_services()
        for _, service in self.services:
            service.init_service()
        self.init()
        for game_object in list(self.game_objects):
            game_object.init_object()
        self.is_init = True

    def update_scene(self, delta_time: float) -> None:
        """Update the scene, services, and objects.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        self.update(delta_time)
        for _, service in self.services:
            service.update(delta_time)
        for game_object in list(self.game_objects):
            game_object.update_object(delta_time)

    def draw_scene(self) -> None:
        """Draw the scene, services, and objects.

        Returns:
            None
        """
        self.draw()
        for _, service in self.services:
            service.draw_service()
        for game_object in list(self.game_objects):
            game_object.draw_object()

    def on_enter(self) -> None:
        """Hook called when the scene becomes active.

        Returns:
            None
        """
        pass

    def on_exit(self) -> None:
        """Hook called when the scene is exited.

        Returns:
            None
        """
        pass

    def add_game_object(self, game_object: GameObject) -> GameObject:
        """Add an existing object to this scene.

        Args:
            game_object: The object to add.

        Returns:
            The same object, after being attached to the scene.
        """
        game_object.scene = self
        self.game_objects.append(game_object)
        return game_object

    def add_game_object_type(self, cls: Type[T], *args: Any, **kwargs: Any) -> T:
        """Create and add a new object of a given type.

        Args:
            cls: GameObject class to instantiate.
            *args: Positional args forwarded to the constructor.
            **kwargs: Keyword args forwarded to the constructor.

        Returns:
            The newly created object.
        """
        game_object = cls(*args, **kwargs)
        self.add_game_object(game_object)
        return game_object

    def add_service(self, service_or_cls: Any, *args: Any, **kwargs: Any) -> Service:
        """Add a service instance or construct one from a class.

        Args:
            service_or_cls: A Service instance or a Service class.
            *args: Positional args forwarded to the constructor.
            **kwargs: Keyword args forwarded to the constructor.

        Returns:
            The service instance added.
        """
        if isinstance(service_or_cls, Service):
            service = service_or_cls
        else:
            service = service_or_cls(*args, **kwargs)
        service.scene = self
        key = service.__class__
        for svc_key, _ in self.services:
            if svc_key == key:
                print(f"Duplicate service added: {key.__name__}")
                return service
        self.services.append((key, service))
        return service

    def get_service(self, cls: Type[T]) -> T:
        """Get a service by type.

        Args:
            cls: Service class to look up.

        Returns:
            The service instance.

        Raises:
            RuntimeError: If no matching service exists.
        """
        for svc_key, svc in self.services:
            if svc_key == cls:
                if not svc.is_init:
                    print(f"Service not initialized: {cls.__name__}")
                return svc  # type: ignore[return-value]
        print(f"Service of requested type not found in scene: {cls.__name__}")
        raise RuntimeError(f"Service not found: {cls.__name__}")

    def get_game_objects_with_tag(self, tag: str) -> List[GameObject]:
        """Get all objects that contain a tag.

        Args:
            tag: Tag string to match.

        Returns:
            List of matching game objects.
        """
        return [obj for obj in self.game_objects if obj.has_tag(tag)]


class Game:
    """Main game class that owns managers and scenes.

    Attributes:
        managers: Mapping of manager type to instance.
        scenes: Mapping of scene name to instance.
        scene_order: Ordered list of scene names.
        current_scene: Active scene.
        next_scene: Scene queued for transition.
    """
    def __init__(self) -> None:
        self.managers: Dict[Type[Any], Manager] = {}
        self.scenes: Dict[str, Scene] = {}
        self.scene_order: List[str] = []
        self.current_scene: Optional[Scene] = None
        self.next_scene: Optional[Scene] = None

    def init(self) -> None:
        """Initialize all managers.

        Returns:
            None
        """
        for manager in self.managers.values():
            manager.init_manager()

    def update(self, delta_time: float) -> None:
        """Update the active scene and render it.

        Args:
            delta_time: Seconds since the last frame.

        Returns:
            None
        """
        if self.current_scene:
            self.current_scene.init_scene()
            self.current_scene.update_scene(delta_time)

            rl.begin_drawing()
            rl.clear_background(rl.RAYWHITE)
            self.current_scene.draw_scene()
            rl.end_drawing()

        if self.next_scene:
            if self.current_scene:
                self.current_scene.on_exit()
            self.current_scene = self.next_scene
            self.current_scene.on_enter()
            self.next_scene = None

    def add_manager(self, manager_or_cls: Any, *args: Any, **kwargs: Any) -> Manager:
        """Add a manager instance or construct one from a class.

        Args:
            manager_or_cls: A Manager instance or a Manager class.
            *args: Positional args forwarded to the constructor.
            **kwargs: Keyword args forwarded to the constructor.

        Returns:
            The manager instance added.
        """
        if isinstance(manager_or_cls, Manager):
            manager = manager_or_cls
        else:
            manager = manager_or_cls(*args, **kwargs)
        key = manager.__class__
        if key in self.managers:
            print(f"Duplicate manager added: {key.__name__}")
        self.managers[key] = manager
        return manager

    def get_manager(self, cls: Type[T]) -> T:
        """Get a manager by type.

        Args:
            cls: Manager class to look up.

        Returns:
            The manager instance.

        Raises:
            RuntimeError: If no matching manager exists.
        """
        manager = self.managers.get(cls)
        if manager is None:
            print(f"Manager of requested type not found: {cls.__name__}")
            raise RuntimeError(f"Manager not found: {cls.__name__}")
        if not manager.is_init:
            print(f"Manager not initialized: {cls.__name__}")
        return manager  # type: ignore[return-value]

    def add_scene(self, name: str, scene_or_cls: Any, *args: Any, **kwargs: Any) -> Scene:
        """Add a scene instance or construct one from a class.

        Args:
            name: Name to register the scene under.
            scene_or_cls: A Scene instance or a Scene class.
            *args: Positional args forwarded to the constructor.
            **kwargs: Keyword args forwarded to the constructor.

        Returns:
            The scene instance added.
        """
        if isinstance(scene_or_cls, Scene):
            scene = scene_or_cls
        else:
            scene = scene_or_cls(*args, **kwargs)
        self.scenes[name] = scene
        scene.game = self
        self.scene_order.append(name)
        if not self.current_scene:
            self.current_scene = scene
        return scene

    def go_to_scene(self, name: str) -> Optional[Scene]:
        """Queue a transition to a named scene.

        Args:
            name: Registered name of the scene.

        Returns:
            The target scene if found, otherwise None.
        """
        scene = self.scenes.get(name)
        if not scene:
            print(f"Scene not found: {name}")
            return None
        self.next_scene = scene
        return scene

    def go_to_scene_next(self) -> Optional[Scene]:
        """Queue a transition to the next scene in order.

        Returns:
            The next scene if one is available, otherwise None.
        """
        if not self.current_scene:
            return None
        current_name = None
        for name, scene in self.scenes.items():
            if scene == self.current_scene:
                current_name = name
                break
        if current_name is None:
            return None
        if current_name in self.scene_order:
            idx = self.scene_order.index(current_name)
            if idx + 1 < len(self.scene_order):
                next_name = self.scene_order[idx + 1]
            else:
                next_name = self.scene_order[0]
            self.next_scene = self.scenes[next_name]
        return self.next_scene
