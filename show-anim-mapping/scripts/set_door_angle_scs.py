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

pairs = [p.split('=') for p in sys.argv[1].split(',')]
cmd = '''
import unreal, json
pairs = ''' + repr(pairs) + '''
out = {}
for path, ang in pairs:
    ang = float(ang)
    bp = unreal.load_asset(path)
    if not bp:
        out[path] = "LOAD_FAIL"; continue
    info = {"scs_changed": [], "errors": []}
    # access SimpleConstructionScript node templates (persisted defaults)
    scs = None
    for pn in ('simple_construction_script','SimpleConstructionScript'):
        try:
            scs = bp.get_editor_property(pn)
            if scs: break
        except Exception as e:
            info["errors"].append("scs:"+str(e)[:60])
    if scs:
        try:
            nodes = scs.get_all_nodes()
        except Exception as e:
            nodes = []
            info["errors"].append("nodes:"+str(e)[:60])
        for n in nodes:
            tmpl = None
            for tp in ('component_template','ComponentTemplate'):
                try:
                    tmpl = n.get_editor_property(tp)
                    if tmpl: break
                except Exception:
                    pass
            if tmpl and tmpl.get_class().get_name() == 'AccessDoorComponent':
                b = tmpl.get_editor_property('OpenedAngle')
                tmpl.set_editor_property('OpenedAngle', ang)
                a = tmpl.get_editor_property('OpenedAngle')
                info["scs_changed"].append([tmpl.get_name(), b, a])
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    saved = unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    # independent re-read of CDO after compile+save
    gc = bp.generated_class()
    cdo = unreal.get_default_object(gc)
    cdo_val = None
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    for h in sds.k2_gather_subobject_data_for_blueprint(bp):
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(sds.k2_find_subobject_data_from_handle(h))
        if o and o.get_class().get_name()=='AccessDoorComponent':
            cdo_val = o.get_editor_property('OpenedAngle'); break
    info["saved"] = saved
    info["cdo_after"] = cdo_val
    out[path] = info
print("SCS_JSON:" + json.dumps(out, ensure_ascii=True))
'''
result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output','')
    if 'SCS_JSON:' in o or 'Error' in o or 'Traceback' in o:
        print(o.strip()[:1500])
re.close_command_connection(); re.stop()
