import sys, os, json, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start()
time.sleep(2)

if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)

node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id)
time.sleep(1)

assets = sys.argv[1].split(',')
cmd = '''
import unreal, json

def channel_keys(ch):
    out = []
    try:
        for k in ch.get_keys():
            t = k.get_time()
            try:
                frame = t.frame_number.value
            except Exception:
                frame = str(t)
            out.append([frame, round(float(k.get_value()), 4)])
    except Exception as e:
        out = "ERR:" + str(e)
    return out

KEYWORDS = ('점검창', 'axis', 'door', 'grp')  # 점검창

def dump_seq(seq):
    info = {"bindings": []}
    for b in seq.get_bindings():
        bname = str(b.get_display_name())
        rot = {}
        for tr in b.get_tracks():
            if isinstance(tr, unreal.MovieScene3DTransformTrack):
                for sec in tr.get_sections():
                    for ch in sec.get_all_channels():
                        try:
                            cn = str(ch.get_name())
                        except Exception:
                            cn = str(ch)
                        low = cn.lower()
                        if 'rot' in low or low in ('roll','pitch','yaw'):
                            keys = channel_keys(ch)
                            if keys:  # only non-empty
                                rot[cn] = keys
        is_relevant = any(k in bname.lower() for k in KEYWORDS)
        if rot or is_relevant:
            info["bindings"].append({"name": bname, "rot": rot})
    # master shot/sub sequence references
    shots = []
    try:
        for mt in seq.get_tracks():
            for sec in mt.get_sections():
                try:
                    sub = sec.get_sequence()
                    if sub:
                        shots.append(sub.get_path_name().split('.')[0])
                except Exception:
                    pass
    except Exception:
        pass
    if shots:
        info["shots"] = shots
    return info

results = {}
try:
    for path in ''' + repr(assets) + ''':
        seq = unreal.load_asset(path)
        if seq:
            results[path] = dump_seq(seq)
        else:
            results[path] = "LOAD_FAIL"
    print("ROT_JSON:" + json.dumps(results))
except Exception as e:
    import traceback
    print("PYERR:" + repr(e))
    print(traceback.format_exc())
'''

result = re.run_command(cmd, unattended=True)
found = False
for line in result.get('output', []):
    out = line.get('output', '')
    if 'ROT_JSON:' in out or 'PYERR:' in out or 'Traceback' in out or 'Error' in out:
        print(out.strip())
        found = True
if not found:
    print("SUCCESS_FLAG:", result.get('success'))
    for line in result.get('output', []):
        print("LINE[" + str(line.get('type')) + "]:", line.get('output', '')[:2000])

re.close_command_connection()
re.stop()
