import sys, os, json, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start()
time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES"); sys.exit(1)
node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id)
time.sleep(1)

assets = sys.argv[1].split(',')
filt = sys.argv[2] if len(sys.argv) > 2 else 'angle,open,rot,deg'
cmd = '''
import unreal, json
filt = [f.lower() for f in ''' + repr(filt) + '''.split(',')]
results = {}
try:
    for path in ''' + repr(assets) + ''':
        bp = unreal.load_asset(path)
        if not bp:
            results[path] = "LOAD_FAIL"; continue
        gc = bp.generated_class()
        cdo = unreal.get_default_object(gc)
        # candidate property names from dir(cdo) matching filter
        cands = []
        for a in dir(cdo):
            al = a.lower()
            if any(f in al for f in filt):
                cands.append(a)
        vals = {}
        for name in cands:
            try:
                v = cdo.get_editor_property(name)
                vals[name] = str(v)
            except Exception as e:
                vals[name] = "GETERR:" + str(e)
        results[path] = {"candidates": cands, "values": vals}
    print("BP_JSON:" + json.dumps(results, ensure_ascii=True))
except Exception as e:
    import traceback
    print("PYERR:" + repr(e)); print(traceback.format_exc())
'''
result = re.run_command(cmd, unattended=True)
found = False
for line in result.get('output', []):
    out = line.get('output','')
    if 'BP_JSON:' in out or 'PYERR:' in out or 'Traceback' in out:
        print(out.strip()); found = True
if not found:
    print("SUCCESS_FLAG:", result.get('success'))
    for line in result.get('output', []):
        print("LINE:", line.get('output','')[:1500])
re.close_command_connection(); re.stop()
