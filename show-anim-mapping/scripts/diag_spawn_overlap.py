"""Diagnose spawnable-overlap for a master sequence marker section.

Usage: python diag_spawn_overlap.py <master_asset_path> <marker_label>
Dumps: marker range, subsequences in range, and for each subsequence:
spawnables (class), possessables (parent), visibility tracks.
"""
import sys, os, json, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

master_path = sys.argv[1]
marker_label = sys.argv[2]

re = remote.RemoteExecution()
re.start()
time.sleep(2)

if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)

node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id)
time.sleep(1)

cmd = '''
import unreal, json
master_path = ''' + repr(master_path) + '''
marker_label = ''' + repr(marker_label) + '''
out = {}
seq = unreal.load_asset(master_path)
if not seq:
    print("DIAG_JSON:" + json.dumps({"error": "master load fail"}))
else:
    markers = seq.get_marked_frames_from_sequence(unreal.MovieSceneTimeUnit.DISPLAY_RATE)
    labels = [(m.label, m.frame_number.value) for m in markers]
    labels.sort(key=lambda x: x[1])
    out["markers"] = labels
    start = end = None
    for i, (lab, fr) in enumerate(labels):
        if lab == marker_label:
            start = fr
            end = labels[i+1][1] if i+1 < len(labels) else None
    out["range"] = [start, end]
    subs = []
    for track in seq.get_master_tracks() if hasattr(seq, "get_master_tracks") else seq.get_tracks():
        if isinstance(track, unreal.MovieSceneSubTrack) or isinstance(track, unreal.MovieSceneCinematicShotTrack):
            for sec in track.get_sections():
                s = sec.get_start_frame()
                e = sec.get_end_frame()
                if end is not None and s >= end: continue
                if e <= start: continue
                sub = sec.get_sequence()
                subs.append({"sub": sub.get_path_name() if sub else None, "start": s, "end": e})
    out["subsequences"] = subs
    details = {}
    for entry in subs:
        sub = unreal.load_asset(entry["sub"].split(".")[0])
        if not sub: continue
        d = {"spawnables": [], "possessables": []}
        for sp in sub.get_spawnables():
            obj_template = sp.get_object_template()
            cls = obj_template.get_class().get_name() if obj_template else "?"
            tracks = [t.get_class().get_name() for t in sp.get_tracks()]
            d["spawnables"].append({"name": sp.get_display_name(), "class": cls, "tracks": tracks})
        for p in sub.get_possessables():
            try:
                parent = p.get_parent().get_display_name()
            except Exception:
                parent = ""
            tracks = [t.get_class().get_name() for t in p.get_tracks()]
            d["possessables"].append({"name": p.get_display_name(), "parent": parent, "tracks": tracks})
        details[entry["sub"]] = d
    out["details"] = details
    print("DIAG_JSON:" + json.dumps(out))
'''

result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output', '')
    if 'DIAG_JSON:' in o:
        print(o.strip())
    elif line.get('type') == 'Error':
        print("ERR:", o.strip())

re.close_command_connection()
re.stop()
