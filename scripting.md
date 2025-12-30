# Cubity Scripting Guide — 2D and 3D

This guide shows how to script Cubity projects (both 2D and 3D). It covers the runtime API, examples, and best practices (including graceful stopping via `STOP_EVENT`).

Files
- Put user code into `main.cpk` of a project (opened by the editor). The editor runs `main.cpk` in a sandboxed global environment exposing Cubity APIs.
- Assets: stored under `projects/<project>/assets`. Use the editor's Assets pane to create/upload assets and folders.

Common note: your script runs with `cubity` module available (the helpers) and other functions provided depending on project mode.

STOP_EVENT
- When running, the environment exposes `STOP_EVENT`, a `threading.Event()` instance.
- Check it in long loops to stop gracefully:
  if STOP_EVENT.is_set(): break

2D API (only available in 2D projects)
- set_context(canvas, assets_path)
  - Called by the editor automatically. Not usually needed in your script.
- spawn_sprite(file_names, x=0, y=0)
  - file_names: a string or list of filenames relative to the project's `assets` folder (e.g. `"player.png"` or `["run1.png","run2.png"]`).
  - Returns a sprite id (Tk canvas image id).
  Example:
    player = spawn_sprite("player.png", 50, 100)

- move_sprite(sprite_id, dx=0, dy=0)
  - Move the sprite by deltas.

- stop_sprite(sprite_id)
  - No-op for now; included for API parity.

- check_collision(a, b)
  - Returns True if two sprite canvas items collide (AABB).

- movement_2d(object_id, speed)
  - Blocking helper that listens to keyboard keys (w/a/s/d) and moves the object once a key is pressed.
  - Example:
    movement_2d(player, 5)

- set_layer(number)
  - Set drawing layer for last spawned sprite (lower number drawn first).

2D example
```
# simple 2D example
player = spawn_sprite("player.png", 30, 50)

for i in range(1000):
    if STOP_EVENT.is_set():
        print("Stopping early")
        break
    move_sprite(player, 1, 0)
```

3D API (only available in 3D projects)
- spawn_object(name, path_obj, path_texture='', x=0, y=0, z=0, rotx=0, roty=0, rotz=0, scale=1)
  - path_obj: path relative to project root or absolute path to .obj file. Prefer to put the .obj in the project's assets folder and provide the relative path.
  - Example:
    spawn_object("teapot", "models/teapot.obj", "textures/teapot.png", x=0, y=0, z=10)

- spawn_cube(name, size=1, ..., path_obj=None, path_texture='')
  - Convenience helper; requires OBJ path if you want actual mesh.

- move_object(name, dx=0, dy=0, dz=0)
  - Moves object by deltas.

- rotate_object(name, rotx=0, roty=0, rotz=0)
  - Adds rotation deltas.

- stop_object(name)
  - Placeholder for stopping motion (no velocity model yet).

- check_collision_3d(name_a, name_b)
  - Axis-aligned bounding-box collision check.

- set_camera(cam) / get_camera()
  - Save or read a camera override array [x, y, z, yaw, pitch]. To actually influence the renderer you may need to modify cubegl.main to read this override (see advanced section).

- render_3d_start() / render_3d_stop()
  - Start or attempt to stop the 3D renderer (editor calls `render_3d_start()` automatically when running a 3D project).
  - `render_3d_stop()` is best-effort — if the renderer loop is blocking, it may not stop immediately.

3D example
```
# spawn and move a cube
spawn_object("c1", "models/cube.obj", "textures/cube.png", x=0, y=0, z=20)
for t in range(10000):
    if STOP_EVENT.is_set():
        print("Stop requested")
        break
    move_object("c1", 0.05, 0, 0)
```

Asset paths and relative references
- The editor copies/saves assets into `projects/<project>/assets`.
- When you pass filenames to 2D functions, use paths relative to the assets folder. Example: if the file is `projects/myproj/assets/sprites/player.png` call `spawn_sprite("sprites/player.png", ...)`.
- The editor's Assets pane will create folders and files directly under the project's `assets` so paths remain stable and reproducible.

Graceful stop patterns
- Scripts should respect `STOP_EVENT` for long-running loops. For example:
```
while True:
    if STOP_EVENT.is_set():
        break
    # do work
```

Tips and advanced
- If you need the 3D renderer camera controlled by scripts, we can add a small API to allow cubegl to read an override camera each frame. Ask me and I'll add that.
- For more complex UIs or large code, split logic into functions and keep the main script short.
- Use the Assets pane to create folders and keep assets organized (e.g. `sprites/`, `models/`, `textures/`).

If you'd like, I can:
- Add a code template generator (New Project → example main.cpk for 2D and 3D).
- Modify cubegl.main to consume `get_camera()` override each frame so scripts can control the camera in real-time.
- Add STOP_EVENT into the global names exposed as `STOP_EVENT` already — the editor does that; use it in scripts to stop loops.

Happy to add the template examples now (2D & 3D) if you want — say "add templates" and I'll insert example main.cpk files into the new project creation step.
