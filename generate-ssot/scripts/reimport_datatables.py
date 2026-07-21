"""
Reimport DataTables in Unreal Editor via Remote Execution.

Triggers reimport of DataTable .uasset from their source CSVs.
Requires: UE Editor running with Python Remote Execution enabled.

Both CP and AC editors will be hit if both are listening on the multicast group.
"""
import sys
import time
import json

UE_PYTHON_PATH = r'E:/Program Files/Epic Games/UE_5.4/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python'
sys.path.insert(0, UE_PYTHON_PATH)
import remote_execution as remote  # noqa: E402

ASSET_PATHS = [
    "/Game/Data/DT_ControlData",
    "/Game/Data/DT_AnimIdMarkerMapping",
]

REIMPORT_CMD = '''
import unreal, json
paths = ''' + repr(ASSET_PATHS) + '''
tools = unreal.AssetToolsHelpers.get_asset_tools()
results = {}
for path in paths:
    asset = unreal.load_asset(path)
    if not asset:
        results[path] = "NOT_FOUND"
        continue
    try:
        # Reimport via AssetImportTask with source from existing AssetImportData
        import_data = asset.get_editor_property("asset_import_data")
        filenames = import_data.extract_filenames() if import_data else []
        if not filenames:
            results[path] = "NO_SOURCE_FILE"
            continue
        src = filenames[0]
        rows_before = len(asset.get_row_names())
        # CSVImportFactory MUST carry the row struct, else the automated
        # import silently no-ops (keeps old rows, raises no error).
        row_struct = asset.get_editor_property("row_struct")
        factory = unreal.CSVImportFactory()
        settings = factory.get_editor_property("automated_import_settings")
        settings.set_editor_property("import_type", unreal.CSVImportType.ECSV_DATA_TABLE)
        settings.set_editor_property("import_row_struct", row_struct)
        task = unreal.AssetImportTask()
        task.filename = src
        # destination_path = package directory (e.g. /Game/Data)
        pkg = asset.get_outermost().get_path_name()  # /Game/Data/DT_X
        dest = pkg.rsplit("/", 1)[0]
        task.destination_path = dest
        task.destination_name = asset.get_name()
        task.replace_existing = True
        task.automated = True
        task.save = True
        task.factory = factory
        tools.import_asset_tasks([task])
        rows_after = len(unreal.load_asset(path).get_row_names())
        results[path] = "OK src=" + src + " rows=" + str(rows_before) + "->" + str(rows_after)
    except Exception as e:
        results[path] = "FAIL:" + type(e).__name__ + ":" + str(e)
print("REIMPORT_JSON:" + json.dumps(results))
'''


def main():
    re = remote.RemoteExecution()
    re.start()
    time.sleep(2)

    if not re.remote_nodes:
        print("ERROR: No UE editor nodes found. Is Python Remote Execution enabled?")
        sys.exit(1)

    print(f"Found {len(re.remote_nodes)} editor node(s):")
    for n in re.remote_nodes:
        print(f"  - {n.get('node_id')} ({n.get('host_name', '?')}/{n.get('project_name', '?')})")

    # Hit each node so both CP and AC reimport
    overall = {}
    for node in re.remote_nodes:
        node_id = node['node_id']
        proj = node.get('project_name', node_id)
        print(f"\n>>> Reimporting on: {proj}")
        try:
            re.open_command_connection(node_id)
            time.sleep(0.5)
            result = re.run_command(REIMPORT_CMD, unattended=True)
            overall[proj] = "OK"
            for line in result.get('output', []):
                out = line.get('output', '').strip()
                if out:
                    print(f"  [{line.get('type', '?')}] {out}")
        except Exception as e:
            overall[proj] = f"FAIL: {e}"
            print(f"  ERROR: {e}")
        finally:
            try:
                re.close_command_connection()
            except Exception:
                pass

    re.stop()

    print("\n=== Summary ===")
    print(json.dumps(overall, indent=2))

    # Exit non-zero if any node failed
    if any(v != "OK" for v in overall.values()):
        sys.exit(2)


if __name__ == "__main__":
    main()
