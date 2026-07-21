"""List level actors whose label or name contains a keyword (case-insensitive).

Usage: python find_level_actors.py <keyword>[,<keyword>...]
"""
import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

keywords = [k.lower() for k in sys.argv[1].split(',')]

re = remote.RemoteExecution()
re.start()
time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)
cmd = '''
import unreal, json
keywords = ''' + repr(keywords) + '''
es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = es.get_editor_world() or es.get_game_world()
mode = "editor" if es.get_editor_world() else "pie"
res = []
if world:
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    for a in actors:
        label = str(a.get_actor_label()) if hasattr(a, "get_actor_label") else ""
        name = str(a.get_name())
        low = label.lower() + "|" + name.lower()
        if any(k in low for k in keywords):
            try:
                hidden = bool(a.get_editor_property("hidden")) if mode == "editor" else bool(a.is_hidden())
            except Exception:
                hidden = None
            res.append({"label": label, "name": name,
                        "class": str(a.get_class().get_name()),
                        "hidden": hidden,
                        "loc": [round(v, 1) for v in a.get_actor_location().to_tuple()]})
print("PROJ:" + unreal.Paths.get_project_file_path() + " mode=" + mode)
print("ACTORS_JSON:" + json.dumps(res))
'''

for node in re.remote_nodes:
    re.open_command_connection(node['node_id'])
    time.sleep(1)
    result = re.run_command(cmd, unattended=True)
    for line in result.get('output', []):
        o = line.get('output', '')
        if 'ACTORS_JSON:' in o or 'PROJ:' in o:
            print(o.strip())
    re.close_command_connection()
re.stop()
