import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start(); time.sleep(5)
print("NODES:", len(re.remote_nodes))
for n in re.remote_nodes:
    print("  node:", n.get('node_id'), n.get('project_name'), n.get('project_root'))
if not re.remote_nodes:
    print("NO_NODES"); sys.exit(1)
node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id); time.sleep(1)

outfile = 'E:/KAI_VCBT/fa50visualdev_new/Saved/cmp_master_inspect.json'
SEQ = '/Game/01_Visual/02_Animation/VCBT/10_Fuel_System/Boostpump_Checkout/Boostpump_Checkout_Master'
KEYWORDS = ['cmp','lamp','light','fuel','panel','f3','f4','f1','f5','ffp','fadec','boost','transfer','pump']

cmd = '''
import unreal, json
outfile = ''' + repr(outfile) + '''
SEQ = ''' + repr(SEQ) + '''
KEYWORDS = ''' + repr(KEYWORDS) + '''

seq = unreal.load_asset(SEQ)
out = {"seq": SEQ, "loaded": bool(seq), "bindings": [], "flagged": [], "spawnables": []}
if seq:
    # subsequence/shot tracks at master level
    master_tracks = []
    try:
        for mt in seq.get_master_tracks():
            master_tracks.append(str(type(mt).__name__))
    except Exception as e:
        master_tracks.append("ERR:"+str(e))
    out["master_tracks"] = master_tracks

    for b in seq.get_bindings():
        name = str(b.get_display_name())
        try:
            pcls = str(b.get_possessed_object_class())
        except Exception:
            pcls = None
        tracks = []
        for tr in b.get_tracks():
            tracks.append(str(type(tr).__name__))
        # spawnable detection
        is_spawn = False
        try:
            is_spawn = b.get_object_template() is not None
        except Exception:
            pass
        rec = {"name": name, "class": pcls, "tracks": tracks, "spawnable": is_spawn}
        out["bindings"].append(rec)
        if is_spawn:
            out["spawnables"].append(name)
        low = name.lower()
        if any(k in low for k in KEYWORDS):
            out["flagged"].append(rec)

out["binding_count"] = len(out["bindings"])
with open(outfile, 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, indent=1)
print("DONE loaded=%s bindings=%d flagged=%d spawnables=%d" % (out["loaded"], len(out["bindings"]), len(out["flagged"]), len(out["spawnables"])))
'''
result = re.run_command(cmd, unattended=True)
import json as _j
print("RESULT:", _j.dumps(result)[:4000])
re.close_command_connection(); re.stop()
