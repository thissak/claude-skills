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

asset = sys.argv[1]
cmd = '''
import unreal, json
path = ''' + repr(asset) + '''
out = {}
try:
    bp = unreal.load_asset(path)
    gc = bp.generated_class()
    cdo = unreal.get_default_object(gc)
    # SimpleConstructionScript components via SubobjectDataSubsystem
    comps = []
    try:
        sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        handles = sds.k2_gather_subobject_data_for_blueprint(bp)
        for h in handles:
            data = sds.k2_find_subobject_data_from_handle(h)
            obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
            if not obj:
                continue
            nm = obj.get_name()
            entry = {"name": nm, "class": obj.get_class().get_name()}
            try:
                rr = obj.get_editor_property('relative_rotation')
                entry["rel_rot"] = [round(rr.roll,3), round(rr.pitch,3), round(rr.yaw,3)]
            except Exception:
                pass
            for pn in ('OpenedAngle','ClosedAngle','bReverseRotation','bUseParentLocalAxis','PivotRotation','AnimationDuration'):
                try:
                    entry[pn] = str(obj.get_editor_property(pn))
                except Exception:
                    pass
            comps.append(entry)
    except Exception as e:
        out['_comp_err'] = str(e)[:200]
    out['components'] = comps
    # CDO-level probe of candidate angle vars
    cdo_vals = {}
    for pn in ('bReverseRotation','OpenAngle','OpenRotation','TotalRotationAngle','OpenAngleDegree','TargetAngle','OpenedAngle','AngleDegree'):
        try:
            cdo_vals[pn] = str(cdo.get_editor_property(pn))
        except Exception:
            pass
    out['cdo'] = cdo_vals
    print("FULL_JSON:" + json.dumps(out, ensure_ascii=True))
except Exception as e:
    import traceback
    print("PYERR:" + repr(e)); print(traceback.format_exc())
'''
result = re.run_command(cmd, unattended=True)
found = False
for line in result.get('output', []):
    o = line.get('output','')
    if 'FULL_JSON:' in o or 'PYERR:' in o or 'Traceback' in o:
        print(o.strip()); found = True
if not found:
    print("SUCCESS_FLAG:", result.get('success'))
    for line in result.get('output', []):
        print("LINE:", line.get('output','')[:1500])
re.close_command_connection(); re.stop()
