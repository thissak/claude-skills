import sys, os, json, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start(); time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES"); sys.exit(1)
node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id); time.sleep(1)

folder = '/Game/01_Visual/01_Asset/Meshes/Character/fa50/ext/bp/fa50_InspectionWindow'
outfile = 'E:/KAI_VCBT/fa50visualdev_new/Saved/door_audit.json'
cmd = '''
import unreal, json
folder = ''' + repr(folder) + '''
outfile = ''' + repr(outfile) + '''
eal = unreal.EditorAssetLibrary
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
paths = [p for p in eal.list_assets(folder, recursive=False, include_folder=False)]
results = {}
for p in paths:
    name = p.split('/')[-1].split('.')[0]
    if '점검창' not in name:
        continue
    try:
        bp = unreal.load_asset(p)
        gc = bp.generated_class()
        doors = []
        axes = []
        handles = sds.k2_gather_subobject_data_for_blueprint(bp)
        seen = set()
        for h in handles:
            data = sds.k2_find_subobject_data_from_handle(h)
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
            if not obj:
                continue
            oid = obj.get_name()
            if oid in seen:
                continue
            seen.add(oid)
            cls = obj.get_class().get_name()
            if cls in ('AccessDoorComponent','RemovableAccessDoorComponent'):
                d = {'comp': oid, 'cls': cls}
                for pn in ('OpenedAngle','ClosedAngle','bReverseRotation','bUseParentLocalAxis'):
                    try:
                        d[pn] = obj.get_editor_property(pn)
                    except Exception:
                        d[pn] = None
                try:
                    d['Axis'] = str(obj.get_editor_property('AxisEnum'))
                except Exception:
                    pass
                doors.append(d)
            if 'AXIS' in oid:
                axes.append(oid.replace('_GEN_VARIABLE',''))
        results[name] = {'doors': doors, 'axes': sorted(set(axes))}
    except Exception as e:
        results[name] = {'error': str(e)[:120]}
with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print('AUDIT_DONE count=' + str(len(results)))
'''
result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output','')
    if o.strip():
        print(o.strip()[:300])
re.close_command_connection(); re.stop()
