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
cmd = '''
import unreal, json
results = {}
try:
    for path in ''' + repr(assets) + ''':
        bp = unreal.load_asset(path)
        if not bp:
            results[path] = "LOAD_FAIL"; continue
        gc = bp.generated_class()
        cdo = unreal.get_default_object(gc)
        # parent class chain
        chain = []
        c = gc
        for _ in range(12):
            try:
                nm = c.get_name()
            except Exception:
                break
            chain.append(nm)
            try:
                c = unreal.get_base_struct(c) if False else None
            except Exception:
                c = None
            break
        # variable list via BlueprintEditorLibrary
        varinfo = {}
        try:
            bel = unreal.BlueprintEditorLibrary
            fns = [f for f in dir(bel) if 'var' in f.lower()]
            varinfo['_bel_var_fns'] = fns
        except Exception as e:
            varinfo['_bel_err'] = str(e)
        # try kismet variable listing
        try:
            names = [str(n) for n in unreal.BlueprintEditorLibrary.get_blueprint_variable_names(bp)]
            varinfo['vars'] = names
            vals = {}
            for n in names:
                try:
                    vals[n] = str(cdo.get_editor_property(n))
                except Exception as e:
                    vals[n] = "ERR:" + str(e)[:60]
            varinfo['values'] = vals
        except Exception as e:
            varinfo['_getvars_err'] = str(e)[:120]
        results[path] = {"class": gc.get_name(), "varinfo": varinfo}
    print("BPV_JSON:" + json.dumps(results, ensure_ascii=True))
except Exception as e:
    import traceback
    print("PYERR:" + repr(e)); print(traceback.format_exc())
'''
result = re.run_command(cmd, unattended=True)
found = False
for line in result.get('output', []):
    out = line.get('output','')
    if 'BPV_JSON:' in out or 'PYERR:' in out or 'Traceback' in out:
        print(out.strip()); found = True
if not found:
    print("SUCCESS_FLAG:", result.get('success'))
    for line in result.get('output', []):
        print("LINE:", line.get('output','')[:1500])
re.close_command_connection(); re.stop()
