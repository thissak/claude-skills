"""Fix spawnable-overlap: possess real CP actors + add visibility-hide tracks,
optionally remove static-duplicate spawnables. Reads config from JSON file.

Usage: python fix_spawn_overlap.py <config.json>
Config: [{"seq": "/Game/...", "hide_labels": ["label", ...], "remove_spawns": ["display name", ...]}, ...]
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
re.open_command_connection(re.remote_nodes[0]['node_id'])
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
        entry = {"seq": job["seq"], "hidden": [], "removed": [], "skipped": [], "errors": []}
        start = seq.get_playback_start()
        end = seq.get_playback_end()
        existing = set(str(p.get_display_name()) for p in seq.get_possessables())

        for label in job.get("hide_labels", []):
            actor = actors_by_label.get(label)
            if not actor:
                entry["errors"].append("actor not found: " + label)
                continue
            if str(actor.get_actor_label()) in existing or actor.get_name() in existing:
                entry["skipped"].append(label + " (already bound)")
                continue
            try:
                binding = seq.add_possessable(actor)
                track = binding.add_track(unreal.MovieSceneVisibilityTrack)
                section = track.add_section()
                section.set_range(start, end)
                section.set_completion_mode(unreal.MovieSceneCompletionMode.RESTORE_STATE)
                ch = section.get_all_channels()[0]
                ch.add_key(unreal.FrameNumber(start), False)
                entry["hidden"].append(label)
            except Exception:
                entry["errors"].append(label + ": " + traceback.format_exc())

        for spawn_name in job.get("remove_spawns", []):
            removed = False
            for sp in seq.get_spawnables():
                if str(sp.get_display_name()) == spawn_name:
                    children = [str(p.get_display_name()) for p in seq.get_possessables()
                                if p.get_parent() and str(p.get_parent().get_display_name()) == spawn_name]
                    if children:
                        entry["errors"].append("spawn has children, NOT removed: " + spawn_name + " -> " + ",".join(children))
                    else:
                        sp.remove()
                        entry["removed"].append(spawn_name)
                        removed = True
                    break
            if not removed and spawn_name not in [e.split(" ")[-1] for e in entry["errors"]]:
                pass

        ok = unreal.EditorAssetLibrary.save_asset(job["seq"])
        entry["saved"] = bool(ok)
        log.append(entry)
    print("FIX_JSON:" + json.dumps(log))
except Exception:
    print("FIX_FATAL:" + traceback.format_exc())
'''

result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output', '')
    if 'FIX_JSON:' in o or 'FIX_FATAL:' in o:
        print(o.strip())
re.close_command_connection()
re.stop()
