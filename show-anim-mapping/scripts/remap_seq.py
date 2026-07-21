import sys, json, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

# args: listfile axis_csv lo hi target mode(dry|apply)
listfile, axis_csv, lo, hi, target, mode = sys.argv[1:7]
axes = axis_csv.split(',')
lo = float(lo); hi = float(hi); target = float(target)

re = remote.RemoteExecution()
re.start(); time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES"); sys.exit(1)
node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id); time.sleep(1)

outfile = 'E:/KAI_VCBT/fa50visualdev_new/Saved/remap_result.json'
cmd = '''
import unreal, json
paths = [l.strip() for l in open(''' + repr(listfile) + ''', encoding="utf-8") if l.strip()]
axes = ''' + repr(axes) + '''
lo, hi, target = ''' + repr(lo) + ''', ''' + repr(hi) + ''', ''' + repr(target) + '''
apply = ''' + repr(mode == 'apply') + '''
outfile = ''' + repr(outfile) + '''

res = {"assets": 0, "keys_changed": 0, "saved": 0, "errors": [], "samples": []}
for path in paths:
    try:
        seq = unreal.load_asset(path)
        if not seq:
            res["errors"].append(path + ":LOAD_FAIL"); continue
        ach = 0
        sample = []
        for b in seq.get_bindings():
            if str(b.get_display_name()) not in axes:
                continue
            for tr in b.get_tracks():
                if not isinstance(tr, unreal.MovieScene3DTransformTrack):
                    continue
                for sec in tr.get_sections():
                    for ch in sec.get_all_channels():
                        try:
                            cn = str(ch.get_name()).lower()
                        except Exception:
                            cn = ''
                        if 'rot' not in cn:
                            continue
                        for k in ch.get_keys():
                            v = float(k.get_value())
                            if lo <= abs(v) <= hi:
                                nv = -target if v < 0 else target
                                if apply:
                                    k.set_value(nv)
                                ach += 1
                                if len(sample) < 3:
                                    sample.append([cn, round(v,2), round(nv,2)])
        if ach:
            res["assets"] += 1
            res["keys_changed"] += ach
            if apply:
                if unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False):
                    res["saved"] += 1
            if len(res["samples"]) < 6:
                res["samples"].append([path.split('/')[-1], sample])
    except Exception as e:
        res["errors"].append(path + ":" + str(e)[:80])
with open(outfile, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print("REMAP_DONE apply=%s assets=%d keys=%d saved=%d errors=%d" % (str(apply), res["assets"], res["keys_changed"], res["saved"], len(res["errors"])))
'''
result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output','')
    if o.strip():
        print(o.strip()[:300])
re.close_command_connection(); re.stop()
