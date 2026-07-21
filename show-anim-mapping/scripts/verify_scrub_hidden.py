"""Open a sequence in Sequencer, scrub to a frame, and report actors' temporarily-hidden state.

Usage: python verify_scrub_hidden.py <seq_path> <frame> <label1,label2,...>
"""
import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

seq_path, frame, labels = sys.argv[1], int(sys.argv[2]), sys.argv[3].split(',')

re = remote.RemoteExecution()
re.start()
time.sleep(2)
if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)
re.open_command_connection(re.remote_nodes[0]['node_id'])
time.sleep(1)

cmd = '''
import unreal, json
seq = unreal.load_asset(''' + repr(seq_path) + ''')
lsl = unreal.LevelSequenceEditorBlueprintLibrary
lsl.open_level_sequence(seq)
lsl.set_current_time(''' + str(frame) + ''')
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
res = {}
for a in actor_sub.get_all_level_actors():
    label = str(a.get_actor_label())
    if label in ''' + repr(labels) + ''':
        res[label] = {"temp_hidden": bool(a.is_temporarily_hidden_in_editor()),
                      "hidden_prop": bool(a.get_editor_property("hidden"))}
lsl.close_level_sequence()
print("SCRUB_JSON:" + json.dumps(res))
'''

result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    o = line.get('output', '')
    if 'SCRUB_JSON:' in o:
        print(o.strip())
re.close_command_connection()
re.stop()
