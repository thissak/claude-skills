"""Print current level and total actor count on every editor node."""
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
world = es.get_editor_world()
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
n = len(sub.get_all_level_actors())
print("LEVEL:" + world.get_path_name() + " actors=" + str(n) + " proj=" + unreal.Paths.get_project_file_path())
'''

for node in re.remote_nodes:
    re.open_command_connection(node['node_id'])
    time.sleep(1)
    result = re.run_command(cmd, unattended=True)
    if not result.get('output'):
        print("EMPTY:", result.get('result'))
    for line in result.get('output', []):
        print(line.get('type', '?'), '|', line.get('output', '').strip())
    re.close_command_connection()
re.stop()
