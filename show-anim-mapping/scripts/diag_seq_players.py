"""List LevelSequenceActors in the running world(s) with playback state."""
import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start()
time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)

cmd = '''
import unreal, json
es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = es.get_editor_world() or es.get_game_world()
res = []
if world:
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LevelSequenceActor):
        e = {"name": str(a.get_name())}
        try:
            seq = a.get_sequence()
            e["seq"] = str(seq.get_name()) if seq else ""
        except Exception:
            e["seq"] = "ERR"
        try:
            p = a.get_editor_property("sequence_player")
            if p:
                e["playing"] = bool(p.is_playing())
                e["paused"] = bool(p.is_paused())
                e["time"] = p.get_current_time().time.frame_number.value
                e["end"] = p.get_end_time().time.frame_number.value
        except Exception as ex:
            e["player"] = "ERR:" + str(ex)
        res.append(e)
print("PLAYERS_JSON:" + json.dumps(res) + " proj=" + unreal.Paths.get_project_file_path()[-40:])
'''

for node in re.remote_nodes:
    re.open_command_connection(node['node_id'])
    time.sleep(1)
    result = re.run_command(cmd, unattended=True)
    if not result.get('output'):
        print("EMPTY:", str(result)[:300])
    for line in result.get('output', []):
        o = line.get('output', '')
        if 'PLAYERS_JSON:' in o:
            print(o.strip())
    re.close_command_connection()
re.stop()
