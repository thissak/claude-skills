"""Print the mesh asset behind each spawnable of a sequence.

Usage: python diag_spawn_meshes.py <asset_path>
"""
import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

asset_path = sys.argv[1]

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
seq = unreal.load_asset(''' + repr(asset_path) + ''')
res = []
for sp in seq.get_spawnables():
    e = {"name": str(sp.get_display_name())}
    tmpl = sp.get_object_template()
    if tmpl:
        e["class"] = str(tmpl.get_class().get_name())
        for prop in ("skeletal_mesh_component", "static_mesh_component"):
            try:
                comp = tmpl.get_editor_property(prop)
                if comp:
                    for mprop in ("skeletal_mesh", "static_mesh"):
                        try:
                            mesh = comp.get_editor_property(mprop)
                            if mesh:
                                e["mesh"] = str(mesh.get_path_name())
                        except Exception:
                            pass
            except Exception:
                pass
    res.append(e)
print("MESH_JSON:" + json.dumps(res))
'''

result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output', '')
    if 'MESH_JSON:' in o:
        print(o.strip())
re.close_command_connection()
re.stop()
