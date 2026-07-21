import sys, time
ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote
re = remote.RemoteExecution()
re.start(); time.sleep(5)
if not re.remote_nodes:
    print("NO_NODES"); sys.exit(1)
re.open_command_connection(re.remote_nodes[0]['node_id']); time.sleep(1)
cmd = '''
import unreal
eas = unreal.EditorActorSubsystem()
actors = eas.get_all_level_actors()
hits = []
for a in actors:
    nm = a.get_name()
    lbl = a.get_actor_label()
    if "2216" in nm or "2216" in lbl or "inspection" in nm.lower() or "inspection" in lbl.lower():
        hits.append((nm, lbl, a.get_class().get_name()))
print("COUNT", len(hits))
for nm,lbl,cls in hits:
    print("ACTOR name=%s | label=%s | class=%s" % (nm, lbl, cls))
'''
result = re.run_command(cmd, unattended=True)
print("SUCCESS:", result.get('success'))
for line in result.get('output', []):
    if line.get('output','').strip():
        print(line['output'].strip()[:300])
re.close_command_connection(); re.stop()
