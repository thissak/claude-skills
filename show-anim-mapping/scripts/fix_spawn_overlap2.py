"""Refined spawn-overlap fix:
- new hides with range [start, end-1) (hold frame shows real actors)
- trim existing visibility sections to [start, end-1)
- key spawn tracks True@start / False@(end-1) so duplicates despawn at the hold frame
- optionally remove static-duplicate spawnables

Usage: python fix_spawn_overlap2.py <config.json>
Config: [{"seq", "hide_labels": [], "trim_vis": [], "spawn_off": [], "remove_spawns": []}]
Writes detailed log to E:\\temp_fix_log.json (remote side).
"""
import sys, time, json

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

config = json.load(open(sys.argv[1], encoding='utf-8'))

re = remote.RemoteExecution()
re.start()
time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)

# pick the CP editor node (project path without _AC)
probe = "import unreal; print('PROBE:' + unreal.Paths.get_project_file_path())"
cp_node = None
for node in re.remote_nodes:
    re.open_command_connection(node['node_id'])
    time.sleep(1)
    r = re.run_command(probe, unattended=True)
    proj = next((l.get('output', '') for l in r.get('output', []) if 'PROBE:' in l.get('output', '')), '')
    re.close_command_connection()
    if '_AC' not in proj:
        cp_node = node
        break
if not cp_node:
    print("NO_CP_NODE")
    sys.exit(1)
re.open_command_connection(cp_node['node_id'])
time.sleep(1)

cmd = '''
import unreal, json, traceback
config = ''' + repr(config) + '''
log = []
try:
    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors_by_label = {}
    for a in actor_sub.get_all_level_actors():
        actors_by_label[str(a.get_actor_label())] = a

    for job in config:
        seq = unreal.load_asset(job["seq"])
        if not seq:
            log.append({"seq": job["seq"], "error": "load fail"})
            continue
        entry = {"seq": job["seq"], "hidden": [], "trimmed": [], "spawn_keyed": [],
                 "removed": [], "errors": []}
        start = seq.get_playback_start()
        end = seq.get_playback_end()
        hold = end - 1
        entry["range"] = [start, end, hold]

        # 1) new hides, range [start, hold)
        existing = {}
        for p in seq.get_possessables():
            existing[str(p.get_display_name())] = p
        for label in job.get("hide_labels", []):
            actor = actors_by_label.get(label)
            if not actor:
                entry["errors"].append("actor not found: " + label)
                continue
            if label in existing:
                entry["errors"].append("already bound (use trim_vis): " + label)
                continue
            try:
                binding = seq.add_possessable(actor)
                track = binding.add_track(unreal.MovieSceneVisibilityTrack)
                section = track.add_section()
                section.set_range(start, hold)
                section.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
                ch = section.get_all_channels()[0]
                ch.add_key(unreal.FrameNumber(start), False)
                entry["hidden"].append(label)
            except Exception:
                entry["errors"].append(label + ": " + traceback.format_exc())

        # 2) trim existing visibility sections to [start, hold)
        for name in job.get("trim_vis", []):
            p = existing.get(name)
            if not p:
                entry["errors"].append("possessable not found: " + name)
                continue
            done = False
            for t in p.get_tracks():
                if isinstance(t, unreal.MovieSceneVisibilityTrack):
                    for s in t.get_sections():
                        s.set_range(start, hold)
                        done = True
            entry["trimmed"].append(name) if done else entry["errors"].append("no vis track: " + name)

        # 3) spawn keys: True@start, False@hold
        for name in job.get("spawn_off", []):
            done = False
            for sp in seq.get_spawnables():
                if str(sp.get_display_name()) != name:
                    continue
                for t in sp.get_tracks():
                    if isinstance(t, unreal.MovieSceneSpawnTrack):
                        for s in t.get_sections():
                            ch = s.get_all_channels()[0]
                            ch.add_key(unreal.FrameNumber(start), True)
                            ch.add_key(unreal.FrameNumber(hold), False)
                            done = True
                break
            entry["spawn_keyed"].append(name) if done else entry["errors"].append("spawn track not found: " + name)

        # 4) remove static-duplicate spawnables (no children only)
        for spawn_name in job.get("remove_spawns", []):
            for sp in seq.get_spawnables():
                if str(sp.get_display_name()) == spawn_name:
                    children = [str(p.get_display_name()) for p in seq.get_possessables()
                                if p.get_parent() and str(p.get_parent().get_display_name()) == spawn_name]
                    if children:
                        entry["errors"].append("spawn has children, NOT removed: " + spawn_name)
                    else:
                        sp.remove()
                        entry["removed"].append(spawn_name)
                    break

        entry["saved"] = bool(unreal.EditorAssetLibrary.save_asset(job["seq"]))
        log.append(entry)
    with open(r"E:\\temp_fix_log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=1)
    errs = sum(len(e.get("errors", [])) for e in log)
    print("FIX_DONE: jobs=" + str(len(log)) + " errors=" + str(errs))
except Exception:
    print("FIX_FATAL:" + traceback.format_exc())
'''

result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output', '')
    if 'FIX_DONE:' in o or 'FIX_FATAL:' in o:
        print(o.strip())
re.close_command_connection()
re.stop()
