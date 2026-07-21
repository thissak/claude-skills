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

cmd = '''
import unreal, json
asset_path = "/Game/01_Visual/02_Animation/VCBT/05_Weapon/LAU117_Interface_Checkout/LAU117_Interface_Checkout_Master"
seq = unreal.load_asset(asset_path)
if seq:
    markers = seq.get_marked_frames_from_sequence(unreal.MovieSceneTimeUnit.DISPLAY_RATE)
    labels = [m.label for m in markers]
    print("MARKERS_JSON:" + json.dumps(labels))
else:
    print("LOAD_FAIL")
'''

result = re.run_command(cmd, unattended=True)
print(json.dumps(result, default=str))

re.close_command_connection()
re.stop()
