# Game Jam Kit
A simple framework for making small games with [raylib](https://www.raylib.com/), [box2d](https://box2d.org/), and [LDtk](https://ldtk.io/).

Python version of the [C++ Game Jam Kit](https://github.com/davabase/game_jam_kit).

## Introduction
The framework in setup as a series of classes that manage the lifecycle of each other.

`Game` manages `Manager`s and `Scene`s.

A `Manager` holds resources that are used across scenes. The resources are loaded at `Game::init()`.

`Scene` manages `Service`s and `GameObject`s.

`Scene`s also perform game logic for each level.

A `Service` holds resources that are used in a single scene. The resources are loaded during init and disposed when the scene is disposed.

`GameObject` manages `Component`s

`GameObject`s also perform game logic for individual game entities.

A `Component` is a reusable tool for creating `GameObject` behavior.

Each of these pieces has lifecycle functions for `init()`, `update()`, and `draw()` that can be overridden when creating your own subclasses. These functions are called by the containing manager. If you do not wish for your class to be managed you shouldn't inherit from these base classes.

The managers also have larger overridable functions, `init_*()`, `update_*()`, and `draw_*()` that give you increased control over how the manager is used.

See `engine/prefabs` for prebuilt managers, services, game objects, and components.

See `samples` for examples on how to build a `Scene`.

See `main.py` for how to build a `Game`.

## Running
Create a python 3 venv:
```
python -m venv venv
```

Initialize it:

on Windows:
```
venv\Scripts\activate
```
on the other ones:
```
source venv/bin/activate
```

Install requirements:
```
pip install -r requirements.txt
```

Run the main file:
```
python main.py
```
