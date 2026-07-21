import sys, json, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start(); time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES"); sys.exit(1)
node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id); time.sleep(1)

# argv: path1=angle1,path2=angle2
pairs = [p.split('=') for p in sys.argv[1].split(',')]
cmd = '''
import unreal, json
pairs = ''' + repr(pairs) + '''
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
out = {}
for path, ang in pairs:
    ang = float(ang)
    bp = unreal.load_asset(path)
    if not bp:
        out[path] = "LOAD_FAIL"; continue
    changed = []
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    seen = set()
    for h in handles:
        data = sds.k2_find_subobject_data_from_handle(h)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
        if not obj:
            continue
        if obj.get_name() in seen:
            continue
        seen.add(obj.get_name())
        if obj.get_class().get_name() == 'AccessDoorComponent':
            before = obj.get_editor_property('OpenedAngle')
            obj.set_editor_property('OpenedAngle', ang)
            after = obj.get_editor_property('OpenedAngle')
            changed.append([obj.get_name(), before, after])
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    out[path] = {"changed": changed, "saved": saved}
print("SET_JSON:" + json.dumps(out, ensure_ascii=True))
'''
result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output','')
    if 'SET_JSON:' in o or 'Error' in o or 'Traceback' in o:
        print(o.strip()[:1500])
re.close_command_connection(); re.stop()
