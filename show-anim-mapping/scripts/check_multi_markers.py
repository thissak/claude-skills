import sys, os, json, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start()
time.sleep(2)

if not re.remote_nodes:
    print("NO_NODES")
    sys.exit(1)

node_id = re.remote_nodes[0]['node_id']
re.open_command_connection(node_id)
time.sleep(1)

assets = sys.argv[1].split(',')
cmd = '''
import unreal, json
results = {}
for path in ''' + repr(assets) + ''':
    seq = unreal.load_asset(path)
    if seq:
        markers = seq.get_marked_frames_from_sequence(unreal.MovieSceneTimeUnit.DISPLAY_RATE)
        results[path] = [m.label for m in markers]
    else:
        results[path] = "LOAD_FAIL"
print("MARKERS_JSON:" + json.dumps(results))
'''

result = re.run_command(cmd, unattended=True)
for line in result.get('output', []):
    out = line.get('output', '')
    if 'MARKERS_JSON:' in out:
        print(out.strip())

re.close_command_connection()
re.stop()
