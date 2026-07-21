"""List components of a spawnable's object template in a sequence.

Usage: python diag_bp_components.py <seq_path> <spawnable_display_name_substring>
"""
import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

seq_path, keyword = sys.argv[1], sys.argv[2].lower()

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
seq = unreal.load_asset(''' + repr(seq_path) + ''')
res = []
for sp in seq.get_spawnables():
    if ''' + repr(keyword) + ''' not in str(sp.get_display_name()).lower():
        continue
    tmpl = sp.get_object_template()
    comps = []
    if tmpl:
        for c in tmpl.get_components_by_class(unreal.SceneComponent):
            e = {"name": str(c.get_name()), "class": str(c.get_class().get_name())}
            try:
                mesh = c.get_editor_property("static_mesh")
                e["mesh"] = str(mesh.get_name()) if mesh else ""
            except Exception:
                pass
            comps.append(e)
    res.append({"spawn": str(sp.get_display_name()), "components": comps})
print("COMP_JSON:" + json.dumps(res))
'''

result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output', '')
    if 'COMP_JSON:' in o:
        print(o.strip())
re.close_command_connection()
re.stop()
