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

outfile = 'E:/KAI_VCBT/fa50visualdev_new/Saved/door2216_visibility.json'
cmd = '''
import unreal, json
outfile = ''' + repr(outfile) + '''
TARGET_BIND = "bp_KAI_int_door2216_inspection"
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(class_names=["LevelSequence"], recursive_paths=True, package_paths=["/Game"])
assets = ar.get_assets(f)

# MovieSceneVisibilityTrack channel = bShouldBeVisible (per VisibilitySystem.cpp):
#   value/default True = VISIBLE(on), False = HIDDEN(visible OFF)
def sec_info(sec):
    try: s = sec.get_start_frame()
    except Exception: s = None
    try: e = sec.get_end_frame()
    except Exception: e = None
    chans = []
    for ch in sec.get_all_channels():
        cn = str(ch.get_name())
        dv = None
        try:
            dv = ch.get_default()
        except Exception:
            pass
        keys = []
        try:
            for k in ch.get_keys():
                t = k.get_time()
                fr = t.frame_number.value if hasattr(t,'frame_number') else t
                keys.append([fr, k.get_value()])
        except Exception:
            pass
        chans.append({"ch": cn, "default": dv, "keys": keys})
    return {"start": s, "end": e, "channels": chans}

results = []
scanned = 0
for a in assets:
    path = str(a.package_name)
    seq = unreal.load_asset(path)
    if not seq:
        continue
    scanned += 1
    for b in seq.get_bindings():
        if str(b.get_display_name()) != TARGET_BIND:
            continue
        for tr in b.get_tracks():
            if not isinstance(tr, unreal.MovieSceneVisibilityTrack):
                continue
            for sec in tr.get_sections():
                results.append({"seq": path, "section": sec_info(sec)})
with open(outfile, 'w', encoding='utf-8') as fp:
    json.dump({"scanned": scanned, "bind": TARGET_BIND, "hits": results}, fp, ensure_ascii=False, indent=1)
print("DONE scanned=%d sections=%d" % (scanned, len(results)))
'''
result = re.run_command(cmd, unattended=True)
import json as _j
print("RESULT:", _j.dumps(result)[:3000])
re.close_command_connection(); re.stop()
