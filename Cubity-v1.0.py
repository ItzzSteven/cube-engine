import os
import shutil
import importlib.util
from tkinter import *
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image, ImageTk

# ---------- PATHS ----------
BASE_ASSETS = "assets"
CUBITYSCRIPT_DIR = os.path.join(BASE_ASSETS, "cubityscript")
PROJECTS_DIR = os.path.join(BASE_ASSETS, "projects")

os.makedirs(CUBITYSCRIPT_DIR, exist_ok=True)
os.makedirs(PROJECTS_DIR, exist_ok=True)

# ---------- STATE ----------
current_project = None
current_project_path = None
editor_window = None
text_editor = None
render_canvas = None
assets_list = None

# ---------- PROJECT MANAGEMENT ----------
def get_projects():
    return [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]
def new_project():
    global render_mode
    name = simpledialog.askstring("New Project","Project name:")
    if not name: 
        return

    # Create a small window to choose project type
    type_win = Toplevel(project_selector)
    type_win.title("Choose Project Type")
    type_win.geometry("250x120")
    Label(type_win,text="Select Render Type",font=("Segoe UI",11)).pack(pady=10)

    def choose_mode(mode):
        global render_mode
        render_mode = mode
        path = os.path.join(PROJECTS_DIR,name)
        os.makedirs(os.path.join(path,"assets"), exist_ok=True)
        # Create empty main.cpk
        with open(os.path.join(path,"main.cpk"),"w") as f: 
            f.write("")
        # Save project config (2D or 3D)
        with open(os.path.join(path,"project_config.txt"),"w") as f: 
            f.write(mode)
        refresh_project_list()
        type_win.destroy()

    # Buttons for 2D or 3D
    Button(type_win,text="2D",bg="#007acc",fg="white",width=12,
           command=lambda: choose_mode("2D")).pack(pady=5)
    Button(type_win,text="3D",bg="#007acc",fg="white",width=12,
           command=lambda: choose_mode("3D")).pack(pady=5)

def delete_project(name):
    if messagebox.askyesno("Delete Project", f"Delete '{name}'?"):
        shutil.rmtree(os.path.join(PROJECTS_DIR, name))
        refresh_project_list()

def open_project(name):
    global current_project, current_project_path
    current_project = name
    current_project_path = os.path.join(PROJECTS_DIR, name)
    project_selector.withdraw()
    open_editor()

# ---------- PROJECT SELECTOR ----------
project_selector = Tk()
project_selector.title("Cubity – Projects")
project_selector.geometry("400x400")
project_selector.configure(bg="#1e1e1e")

Label(project_selector, text="Cubity Projects",
      font=("Segoe UI", 14, "bold"),
      bg="#1e1e1e", fg="white").pack(pady=15)

Button(project_selector, text="+ New Project",
       command=new_project,
       bg="#007acc", fg="white").pack(fill=X, padx=20)

projects_frame = Frame(project_selector, bg="#1e1e1e")
projects_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)

def refresh_project_list():
    for w in projects_frame.winfo_children():
        w.destroy()

    for name in get_projects():
        row = Frame(projects_frame, bg="#1e1e1e")
        row.pack(fill=X, pady=2)

        Button(row, text=name, anchor="w",
               bg="#2b2b2b", fg="white",
               command=lambda n=name: open_project(n)).pack(side=LEFT, fill=X, expand=True)

        Button(row, text="🗑", fg="red", bg="#2b2b2b",
               command=lambda n=name: delete_project(n)).pack(side=RIGHT)

refresh_project_list()

# ---------- EDITOR ----------
def open_editor():
    global editor_window, text_editor, render_canvas, assets_list

    editor_window = Toplevel()
    editor_window.title(f"Cubity – {current_project}")
    editor_window.geometry("1300x700")
    editor_window.configure(bg="#2b2b2b")
    editor_window.protocol("WM_DELETE_WINDOW", close_editor)

    main = PanedWindow(editor_window, orient=HORIZONTAL)
    main.pack(fill=BOTH, expand=True)

    # Assets
    assets_frame = Frame(main, bg="#1e1e1e", width=200)
    main.add(assets_frame)

    Label(assets_frame, text="Assets", fg="white",
          bg="#1e1e1e").pack(pady=5)

    Button(assets_frame, text="Add Asset",
           command=upload_asset,
           bg="#007acc", fg="white").pack(fill=X)

    assets_list = Listbox(assets_frame, bg="#2b2b2b", fg="white")
    assets_list.pack(fill=BOTH, expand=True)

    # Editor
    editor_frame = Frame(main, bg="black")
    main.add(editor_frame)

    text_editor = Text(editor_frame, bg="black", fg="white",
                       insertbackground="white",
                       font=("Consolas", 12))
    text_editor.pack(fill=BOTH, expand=True)

    # Output
    output = Frame(main, bg="#111")
    main.add(output)

    Button(output, text="Run",
           command=run_code,
           bg="#00aa00", fg="white").pack(fill=X)

    render_canvas = Canvas(output, bg="#88ccff")
    render_canvas.pack(fill=BOTH, expand=True)

    load_project()
    refresh_assets()

def close_editor():
    editor_window.destroy()
    project_selector.deiconify()

# ---------- ASSETS ----------
def upload_asset():
    files = filedialog.askopenfilenames()
    if not files:
        return
    dest = os.path.join(current_project_path, "assets")
    for f in files:
        shutil.copy(f, dest)
    refresh_assets()

def refresh_assets():
    assets_list.delete(0, END)
    for f in os.listdir(os.path.join(current_project_path, "assets")):
        assets_list.insert(END, f)

# ---------- LOAD / SAVE ----------
def load_project():
    with open(os.path.join(current_project_path, "main.cpk"), "r") as f:
        text_editor.insert("1.0", f.read())

def save_project():
    with open(os.path.join(current_project_path, "main.cpk"), "w") as f:
        f.write(text_editor.get("1.0", END))

# ---------- RUN CODE (FIXED) ----------
def run_code():
    """
    Run the current project code in Cubity.
    Supports both 2D and 3D projects.
    Automatically injects all functions from cubity_script.py.
    """
    if not current_project_path:
        return

    save_project()
    code = text_editor.get("1.0", END)

    # Clear 2D canvas if in 2D mode
    if render_mode == "2D" and render_canvas:
        render_canvas.delete("all")

    try:
        # Load cubity_script.py
        spec = importlib.util.spec_from_file_location(
            "cubity_script",
            os.path.join(CUBITYSCRIPT_DIR, "cubity_script.py")
        )
        cubity = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cubity)

        # Set 2D canvas context if needed
        if render_mode == "2D":
            cubity.set_context(render_canvas, os.path.join(current_project_path, "assets"))

        # Prepare globals for user code
        exec_globals = {"__builtins__": __builtins__, "cubity": cubity}

        # Inject 2D functions
        for f in ["spawn_sprite", "move_sprite", "stop_sprite", "check_collision", "movement_2d"]:
            if hasattr(cubity, f):
                exec_globals[f] = getattr(cubity, f)

        # Inject 3D functions if in 3D mode
        if render_mode == "3D":
            for f in ["spawn_cube", "spawn_object", "move_object", "rotate_object",
                      "stop_object", "check_collision_3d", "set_camera", "get_camera", "render_3d"]:
                if hasattr(cubity, f):
                    exec_globals[f] = getattr(cubity, f)

            # Start background 3D render loop if not already running
            if not hasattr(cubity, "_3d_loop_started"):
                import threading, time
                def loop():
                    while True:
                        try:
                            cubity.render_3d()
                            time.sleep(0.01)
                        except:
                            break
                t = threading.Thread(target=loop, daemon=True)
                t.start()
                cubity._3d_loop_started = True

        # Execute the user's project code
        exec(code, exec_globals)

    except Exception as e:
        messagebox.showerror("CubityScript Error", str(e))

project_selector.mainloop()
