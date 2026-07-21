"""Deep-dump a level sequence: all tracks, nested subsequences, bindings recursively.

Usage: python diag_seq_deep.py <asset_path>
"""
import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

asset_path = sys.argv[1]

re = remote.RemoteExecution()
re.start()
time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)
re.open_command_connection(re.remote_nodes[0]['node_id'])
time.sleep(1)

cmd = '''
import unreal, json, traceback

def dump_seq(path, depth, out, seen):
    if path in seen or depth > 4: return
    seen.add(path)
    seq = unreal.load_asset(path)
    if not seq:
        out.append({"path": path, "error": "load fail"})
        return
    info = {"path": path, "depth": depth, "tracks": [], "spawnables": [], "possessables": [], "errs": []}
    subs = []
    try:
        for track in seq.get_tracks():
            tname = track.get_class().get_name()
            secs = track.get_sections()
            info["tracks"].append({"type": tname, "sections": len(secs)})
            if isinstance(track, (unreal.MovieSceneSubTrack, unreal.MovieSceneCinematicShotTrack)):
                for sec in secs:
                    sub = sec.get_sequence()
                    if sub:
                        subs.append({"sub": sub.get_path_name().split(".")[0],
                                     "start": sec.get_start_frame(), "end": sec.get_end_frame()})
    except Exception:
        info["errs"].append(traceback.format_exc())
    info["subsections"] = subs
    try:
        for sp in seq.get_spawnables():
            e = {"name": str(sp.get_display_name())}
            try:
                tmpl = sp.get_object_template()
                e["class"] = tmpl.get_class().get_name() if tmpl else "?"
            except Exception:
                e["class"] = "ERR"
            try:
                e["tracks"] = [t.get_class().get_name() for t in sp.get_tracks()]
            except Exception:
                e["tracks"] = ["ERR"]
            info["spawnables"].append(e)
    except Exception:
        info["errs"].append(traceback.format_exc())
    try:
        for p in seq.get_possessables():
            e = {"name": str(p.get_display_name())}
            try:
                par = p.get_parent()
                e["parent"] = str(par.get_display_name()) if par else ""
            except Exception:
                e["parent"] = "ERR"
            try:
                e["tracks"] = [t.get_class().get_name() for t in p.get_tracks()]
            except Exception:
                e["tracks"] = ["ERR"]
            info["possessables"].append(e)
    except Exception:
        info["errs"].append(traceback.format_exc())
    out.append(info)
    for s in subs:
        dump_seq(s["sub"], depth + 1, out, seen)

try:
    out = []
    dump_seq(''' + repr(asset_path) + ''', 0, out, set())
    with open(r"E:\\temp_seq_dump.json", "w", encoding="utf-8") as f:
        json.dump(out, f)
    print("DEEP_DONE:" + str(len(out)))
except Exception:
    print("DEEP_FATAL:" + traceback.format_exc())
'''

result = re.run_command(cmd, unattended=True)
if not result.get('output'):
    print("EMPTY_RESULT:", result)
for line in result.get('output', []):
    o = line.get('output', '')
    if 'DEEP_DONE:' in o or 'DEEP_FATAL:' in o:
        print(o.strip())

re.close_command_connection()
re.stop()
