import sys, time

ue_python_path = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, ue_python_path)
import remote_execution as remote

re = remote.RemoteExecution()
re.start(); time.sleep(5)
if not re.remote_nodes:
    print("NO_NODES"); sys.exit(1)
re.open_command_connection(re.remote_nodes[0]['node_id']); time.sleep(1)

outfile = 'E:/KAI_VCBT/fa50visualdev_new/Saved/hidden_bindings.json'
# Sample a few of the 24 sequences that hide door2216, list ALL bindings whose
# Visibility track default/last value = False (hidden). True=visible, False=hidden.
cmd = '''
import unreal, json
outfile = ''' + repr(outfile) + '''
SAMPLES = [
 "/Game/01_Visual/02_Animation/VCBT/13_Lighting/ConsolePanelLighting_Checkout/Sub/sub_group/330002_016/330002_016_02",
 "/Game/01_Visual/02_Animation/VCBT/01_Communication_System/UVHF_Checkout/Sub/sub_group/232001_008/232001_008_02",
 "/Game/01_Visual/02_Animation/VCBT/15_Engine_System/Engine_Motoring/Sub/sub_group/700002_005/700002_005_02",
]
def hidden_default(sec):
    for ch in sec.get_all_channels():
        try:
            return ch.get_default()
        except Exception:
            return None
    return None
out = {}
for path in SAMPLES:
    seq = unreal.load_asset(path)
    if not seq:
        out[path] = "LOAD_FAIL"; continue
    hidden = []
    visible = []
    for b in seq.get_bindings():
        bn = str(b.get_display_name())
        for tr in b.get_tracks():
            if not isinstance(tr, unreal.MovieSceneVisibilityTrack):
                continue
            for sec in tr.get_sections():
                dv = hidden_default(sec)
                if dv is False:
                    hidden.append(bn)
                elif dv is True:
                    visible.append(bn)
    out[path.split('/')[-1]] = {"hidden_count": len(hidden), "hidden": sorted(set(hidden)), "visible_on": sorted(set(visible))}
with open(outfile, 'w', encoding='utf-8') as fp:
    json.dump(out, fp, ensure_ascii=False, indent=1)
print("DONE")
'''
result = re.run_command(cmd, unattended=True)
print("SUCCESS:", result.get('success'))
for line in result.get('output', []):
    if line.get('output','').strip():
        print(line['output'].strip()[:300])
re.close_command_connection(); re.stop()
