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

outfile = 'E:/KAI_VCBT/fa50visualdev_new/Saved/seq_door_angles.json'
cmd = '''
import unreal, json, re as _re
outfile = ''' + repr(outfile) + '''
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(class_names=["LevelSequence"], recursive_paths=True, package_paths=["/Game/01_Visual/02_Animation/VCBT"])
assets = ar.get_assets(f)

def max_abs_rot(sec):
    m = 0.0
    for ch in sec.get_all_channels():
        try:
            cn = str(ch.get_name()).lower()
        except Exception:
            cn = ''
        if 'rot' not in cn:
            continue
        try:
            for k in ch.get_keys():
                v = abs(float(k.get_value()))
                if v > m: m = v
        except Exception:
            pass
    return m

EXCL = ['int_door','_bt_','_sw_','cap','line','cine','camera','knob','lever','switch','cover','grp','_e_axis']
results = {}
scanned = 0
for a in assets:
    path = str(a.package_name)
    seq = unreal.load_asset(path)
    if not seq:
        continue
    scanned += 1
    doors = []          # external inspection-door ids present in this sub
    rots = []           # (binding_name, magnitude) hinge-AXIS rotations only
    for b in seq.get_bindings():
        bn = str(b.get_display_name())
        m = _re.match(r'fa50_(\\d{4})_점검창', bn)
        if m:
            doors.append(m.group(1))
        low = bn.lower()
        is_hinge = ('axis' in low) and not any(e in low for e in EXCL)
        if not is_hinge:
            continue
        for tr in b.get_tracks():
            if isinstance(tr, unreal.MovieScene3DTransformTrack):
                mx = 0.0
                for sec in tr.get_sections():
                    v = max_abs_rot(sec)
                    if v > mx: mx = v
                if mx > 0.5:
                    rots.append([bn, round(mx,2)])
    if doors and rots:
        results[path.split('/')[-1]] = {"path": path, "doors": sorted(set(doors)), "rots": rots}
with open(outfile, 'w', encoding='utf-8') as fp:
    json.dump({"scanned": scanned, "hits": results}, fp, ensure_ascii=False, indent=1)
print("SCAN_DONE scanned=%d hits=%d" % (scanned, len(results)))
'''
result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output','')
    if o.strip():
        print(o.strip()[:300])
re.close_command_connection(); re.stop()
