import unreal

frame_target_multipliers = {
    30: 1.2,
    60: 1.0,
    120: 0.7
}

def is_nanite_candidate(mesh):
    """
    Determines if a static mesh qualifies for Nanite based on material blend mode. Nanite doesn't support translucent
    or masked materials.

    Args:
        :param mesh: (unreal object)

    Return:
        :return: (bool) True of False
    """

    static_materials = mesh.get_editor_property('static_materials')

    for slot in static_materials:
        material_interface = slot.get_editor_property('material_interface')
        if material_interface:
            blend_mode = material_interface.get_blend_mode()
            if blend_mode in [unreal.BlendMode.BLEND_TRANSLUCENT,
                              unreal.BlendMode.BLEND_MASKED]:
                return False

    return True

def check_mesh_optimization(mesh, mesh_name, mesh_path, lod_triangle_threshold, mesh_subsystem, frame_target):
    """
    Decides whether a mesh should use Nanite or traditional LODs, and flags accordingly. A mesh never receives both recommendations.
    Nanite replaces the need for manual LODs entirely when supported.

    Args:
        :param mesh: (unreal object)
        :param mesh_name: (str) Name of the mesh
        :param mesh_path: (str) Object's path in the Content browser directory
        :param lod_triangle_threshold: (int) Triangle count threshold
        :param mesh_subsystem: (unreal object) Unreal engine subsystem
        :param frame_target: (int) Current frame budget

    Return:
        :return:(list) List of result dicts, each containing: name, path, issue, severity, fix_type, fix_function
    """

    results = []
    triangle_count = mesh.get_num_triangles(0)

    if triangle_count < lod_triangle_threshold:
        return results

    nanite_settings = mesh_subsystem.get_nanite_settings(mesh)
    nanite_enabled = nanite_settings.get_editor_property("enabled")

    if nanite_enabled:
        results.append({
            "name": mesh_name,
            "path": mesh_path,
            "issue": f"{triangle_count:,} tris, Nanite enabled",
            "severity": "PASS",
            "fix_type": "NONE",
            "fix_function": "none"
        })
        return results

    if is_nanite_candidate(mesh):
        results.append({
            "name": mesh_name,
            "path": mesh_path,
            "issue": f"{triangle_count:,} tris, qualifies for Nanite. Nanite currently disabled",
            "severity": "WARNING",
            "fix_type": "AUTO",
            "fix_function": "enable_nanite"
        })

    else:
        lod_count = mesh.get_num_lods()

        if lod_count <= 1:
            results.append({
                "name": mesh_name,
                "path": mesh_path,
                "issue": f"{triangle_count:,} tris, no LODs (threshold {lod_triangle_threshold:,} @ {frame_target}fps) - Nanite unsupported (translucent/masked material)",
                "severity": "CRITICAL",
                "fix_type": "AUTO",
                "fix_function": "generate_lods"
            })
        else:
            results.append({
                "name": mesh_name,
                "path": mesh_path,
                "issue": f"LODs present ({lod_count}). Nanite unsupported for this material",
                "severity": "PASS",
                "fix_type": "NONE",
                "fix_function": "none"
            })

    return results

def check_texture_size(texture, asset_name, asset_path, max_texture_size):
    """
    Flags textures exceeding the maximum recommended dimension.

    Arg:
        :param texture: (unreal object) Texture to check
        :param asset_name: (str) Name of texture
        :param asset_path: (str) Texture's path in the Content browser directory
        :param max_texture_size:(int) Maximum recommended texture dimension

    Return:
        :return: (list) List of result dicts, each containing: name, path, issue, severity, fix_type, fix_function
    """

    results = []
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
            "fix_function": "none"
        })

    return results


def check_srgb_settings(texture, asset_name, asset_path):
    """
    Flags non-color textures (normal, roughness, metallic, AO, height) that incorrectly have sRGB enabled. Detection is based on common
    naming suffix conventions.

    Args:
        :param texture: (unreal object) Texture to check
        :param asset_name: (str) Name of texture
        :param asset_path: (str) Texture's path in the Content browser directory

    Return:
        :return: (list) List of result dicts, each containing: name, path, issue, severity, fix_type, fix_function
    """

    results = []
    srgb = texture.get_editor_property('srgb')
    name_lower = asset_name.lower()

    non_color_suffixes = ['_n', '_normal', '_r', '_roughness', '_m',
                          '_metallic', '_ao', '_h', '_height', '_orm', '_f']

    is_non_color = any(name_lower.endswith(suffix) for suffix in non_color_suffixes)

    if is_non_color and srgb:
        results.append({
            "name": asset_name,
            "path": asset_path,
            "issue": "Non-color texture has sRGB ON. sRGB option should be OFF",
            "severity": "WARNING",
            "fix_type": "AUTO",
            "fix_function": "fix_srgb_off"
        })

    return results

def check_mipmaps(texture, asset_name, asset_path):
    """
    Flags textures with mipmap generation disabled.

    Args:
        :param texture: (unreal object) Texture to check
        :param asset_name: (str) Name of texture
        :param asset_path: (str) Texture's path in the Content browser directory

    Return:
        :return: (list) List of result dicts, each containing: name, path, issue, severity, fix_type, fix_function
    """

    results = []
    mip_gen = texture.get_editor_property('mip_gen_settings')

    if mip_gen == unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS:
        results.append({
            "name": asset_name,
            "path": asset_path,
            "issue": "Mipmaps disabled",
            "severity": "WARNING",
            "fix_type": "AUTO",
            "fix_function": "enable_mipmaps"
        })

    return results

def run_asset_audit(folder, max_texture_size = 2048, lod_triangle_threshold = 5000, frame_target = 60):
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

            results.extend(check_mesh_optimization(
                mesh, asset_name, asset_path, adjusted_lod_threshold, mesh_subsystem, frame_target))


        # Textures
        elif asset_type == "Texture2D":
            texture = unreal.EditorAssetLibrary.load_asset(asset_path)

            if not texture:
                continue

            results.extend(check_texture_size(texture, asset_name, asset_path, max_texture_size))
            results.extend(check_srgb_settings(texture, asset_name, asset_path))
            results.extend(check_mipmaps(texture, asset_name, asset_path))


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
        :return: (str) List results joined into a string
    """

    row_result = []

    for r in results:
        row = f"{r['name']}|{r['path']}|{r['issue']}|{r['severity']}|{r['fix_type']}|{r['fix_function']}"
        row_result.append(row)

    return "\n".join(row_result)





