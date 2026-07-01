import unreal

frame_target_multipliers = {
    30: 1.2,
    60: 1.0,
    120: 0.7
}

def run_asset_audit(folder, max_texture_size = 2048, lod_triangle_threshold = 5000, frame_target = 30):
    """
    Runs a full asset audit on a folder, checking for missing LODs, Nanite candidates, and oversized textures.

    Args:
        :param folder: (str) Content Browser path to scan
        :param max_texture_size: (int) Maximum recommended texture dimension
        :param lod_triangle_threshold: (int) Triangle count above which LODs are required, before frame_target adjustment
        :param frame_target: (int) Target FPS - 30, 60, or 120.
               Adjusts thresholds: lower fps = more lenient, higher fps = stricter.

    Return:
        :return: (list) List of result dicts, each containing: name, path, issue, severity, fix_type, fix_function
    """



    multiplier = frame_target_multipliers.get(frame_target, 1.0)
    adjusted_lod_threshold = int(lod_triangle_threshold * multiplier)

    # Get the asset registry
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    all_assets = asset_registry.get_assets_by_path(folder, recursive = True)
    mesh_subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

    results = []

    for asset in all_assets:
        asset_type = str(asset.asset_class_path.asset_name)
        asset_name = str(asset.asset_name)
        asset_path = str(asset.package_name)

        # Static Mesh
        if asset_type == "StaticMesh":
            mesh = unreal.EditorAssetLibrary.load_asset(asset_path)

            if not mesh:
                continue

            #lod_count = mesh_subsystem.get_lod_count(mesh)
            lod_count = mesh.get_num_lods()
            triangle_count = mesh.get_num_triangles(0)

            # Missing LOD
            if lod_count <= 1 and triangle_count > adjusted_lod_threshold:
                results.append({
                    "name": asset_name,
                    "path": asset_path,
                    "issue": f"{triangle_count:,} tris, no LODs (threshold {adjusted_lod_threshold:,} @ {frame_target}fps)",
                    "severity": "CRITICAL",
                    "fix_type": "AUTO",
                    "fix_function": "generate_lods"
                })

            elif lod_count > 1:
                results.append({
                    "name": asset_name,
                    "path": asset_path,
                    "issue": f"LODs present ({lod_count})",
                    "severity": "PASS",
                    "fix_type": "NONE",
                    "fix_function": ""
                })

            #print(lod_count)
            #print(triangle_count)
            #print(asset_type, asset_name, asset_path)


        # Textures
        elif asset_type == "Texture2D":
            texture = unreal.EditorAssetLibrary.load_asset(asset_path)

            if not texture:
                continue

            texture_width = texture.blueprint_get_size_x()
            texture_height = texture.blueprint_get_size_y()

            if texture_width > max_texture_size or texture_height > max_texture_size:
                severity = "CRITICAL" if texture_width > max_texture_size * 2 else "WARNING"

                results.append({
                    "name": asset_name,
                    "path": asset_path,
                    "issue": f"{texture_width}x{texture_height}, exceeds {max_texture_size}px limit",
                    "severity": severity,
                    "fix_type": "MANUAL",
                    "fix_function": ""
                })

            #print(texture_width, texture_height)

    return results


def format_results_for_blueprint(results):
    """
    Converts a results list into a delimited string for passing
    back to Blueprint via Execute Python Script output pin.

    Format per row: name|path|issue|severity|fix_type|fix_function
    Rows separated by newline.

    Args:
        :param results: (list) List of results from the scans

    Return
        :return: (str)
    """

    row_result = []

    for r in results:
        row = f"{r['name']}|{r['path']}|{r['issue']}|{r['severity']}|{r['fix_type']}|{r['fix_function']}"
        row_result.append(row)

    return "\n".join(row_result)

#re = run_asset_audit("/Game/Assets")

#print(format_results_for_blueprint(re))


