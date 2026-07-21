"""Inspect a runtime actor: tags, owner, visibility — to tell sequencer-spawned vs level/gameplay actor.

Usage: python diag_actor_origin.py <label_keyword>
"""
import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

keyword = sys.argv[1].lower()

re = remote.RemoteExecution()
re.start()
time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)

cmd = '''
import unreal, json
es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = es.get_editor_world() or es.get_game_world()
res = []
if world:
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        label = str(a.get_actor_label()) if hasattr(a, "get_actor_label") else ""
        if ''' + repr(keyword) + ''' in (label.lower() + "|" + str(a.get_name()).lower()):
            e = {"label": label, "name": str(a.get_name())}
            try:
                e["tags"] = [str(t) for t in a.tags]
            except Exception as ex:
                e["tags"] = ["ERR:" + str(ex)]
            try:
                e["hidden"] = bool(a.get_editor_property("hidden"))
            except Exception:
                e["hidden"] = None
            try:
                e["owner"] = str(a.get_owner().get_name()) if a.get_owner() else ""
            except Exception:
                e["owner"] = "ERR"
            try:
                e["level"] = str(a.get_outer().get_name()) if a.get_outer() else ""
            except Exception:
                e["level"] = "ERR"
            res.append(e)
print("ORIGIN_JSON:" + json.dumps(res) + " proj=" + unreal.Paths.get_project_file_path()[-40:])
'''

for node in re.remote_nodes:
    re.open_command_connection(node['node_id'])
    time.sleep(1)
    result = re.run_command(cmd, unattended=True)
    if not result.get('output'):
        print("EMPTY:", str(result)[:500])
    for line in result.get('output', []):
        print(line.get('type', '?'), '|', line.get('output', '').strip()[:500])
    re.close_command_connection()
re.stop()
