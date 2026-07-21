"""Request end of PIE on all editor nodes."""
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
import unreal
es = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if es.get_editor_world():
    print("PIE_STATE: editor mode (no PIE)")
else:
    les.editor_request_end_play()
    print("PIE_STATE: end play requested")
print("PROJ:" + unreal.Paths.get_project_file_path()[-44:])
'''

for node in re.remote_nodes:
    re.open_command_connection(node['node_id'])
    time.sleep(1)
    result = re.run_command(cmd, unattended=True)
    for line in result.get('output', []):
        o = line.get('output', '')
        if 'PIE_STATE' in o or 'PROJ' in o:
            print(o.strip())
    re.close_command_connection()
re.stop()
