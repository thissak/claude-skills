"""List StaticMeshActors with 'panel' in label or mesh path, and all AFTER_COCKPIT panel actors. Writes JSON to E:\\temp_actors.json."""
import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start()
time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)
re.open_command_connection(re.remote_nodes[0]['node_id'])
time.sleep(1)

cmd = '''
import unreal, json
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
sm_panels = []
after_panels = []
for a in sub.get_all_level_actors():
    label = str(a.get_actor_label())
    cls = str(a.get_class().get_name())
    if cls == "StaticMeshActor":
        try:
            mesh = a.static_mesh_component.get_editor_property("static_mesh")
            mpath = str(mesh.get_path_name()) if mesh else ""
        except Exception:
            mpath = ""
        if "panel" in label.lower() or "panel" in mpath.lower():
            sm_panels.append({"label": label, "mesh": mpath})
    if label.startswith("AFTER_COCKPIT."):
        after_panels.append({"label": label, "class": cls})
with open(r"E:\\temp_actors.json", "w", encoding="utf-8") as f:
    json.dump({"static_panels": sm_panels, "after_cockpit": after_panels}, f, ensure_ascii=False, indent=1)
print("DONE static=" + str(len(sm_panels)) + " after=" + str(len(after_panels)))
'''

result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    print(line.get('type', '?'), '|', line.get('output', '').strip())
re.close_command_connection()
re.stop()
