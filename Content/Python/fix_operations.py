"""
UE5 Fix Operations
Automated fix functions called by the Optimization Auditor tool.
Each function takes an asset path and returns True/False for success,
plus a message describing what happened.
"""

import unreal


def generate_lods(asset_path, lod_count = 4):
    """
    Generates a LOD chain on a Static Mesh asset.

    :param asset_path:(str) The location of the asset in Content Browser
    :param lod_count: (int) The number of LODs to be generated. Default is 4

    :return: (tuple) Success: bool, Message: str
    """

    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)

    if not mesh:
        return False, f"Could not load asset at {asset_path}"

    if not isinstance(mesh, unreal.StaticMesh):
        return False, f"Asset is not a Static Mesh — {asset_path}"

    percent_triangles = [1.0, 0.5, 0.25, 0.1]
    screen_sizes = [1.0, 0.3, 0.1, 0.05]

    # Get Static Mesh Editor Subsystem
    sm_editor_subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

    lod_settings = []
    for lod in range(lod_count):
        reduction_settings = unreal.StaticMeshReductionSettings(
            percent_triangles = percent_triangles[lod],
            screen_size = screen_sizes[lod]
        )
        lod_settings.append(reduction_settings)
    reduction_option = unreal.StaticMeshReductionOptions(
        auto_compute_lod_screen_size = False,
        reduction_settings = lod_settings
    )

    result = sm_editor_subsystem.set_lods(mesh, reduction_option)
    unreal.EditorAssetLibrary.save_asset(asset_path)

    return True, f"Generated {result} LODs on {mesh.get_name()}"

def enable_nanite(asset_path):
    """
    Enables Nanite on a Static Mesh asset.

    :param asset_path: (str) The location of the asset in Content Browser

    :return: (tuple) Success: bool, Message: str
    """

    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)

    if not mesh:
        return False, f"Could not load asset at {asset_path}"

    if not isinstance(mesh, unreal.StaticMesh):
        return False, f"Asset is not a Static Mesh — {asset_path}"

    # Get Static Mesh Editor Subsystem
    sm_editor_subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)

    nanite_settings = sm_editor_subsystem.get_nanite_settings(mesh)
    nanite_settings.set_editor_property('enabled', True)
    sm_editor_subsystem.set_nanite_settings(mesh, nanite_settings)

    unreal.EditorAssetLibrary.save_asset(asset_path)

    return True, f"Nanite enabled on {mesh.get_name()}"

def fix_srgb_off(asset_path):
    """
    Turns off sRGB on a texture. Used for normal maps, roughness, metallic, AO, and other non-color data textures that were
    incorrectly imported with sRGB enabled.

    :param asset_path: (str) The location of the asset in Content Browser

    :return: (tuple) Success: bool, Message: str
    """

    texture = unreal.EditorAssetLibrary.load_asset(asset_path)

    if not texture:
        return False, f"Could not load asset at {asset_path}"

    if not isinstance(texture, unreal.Texture2D):
        return False, f"Asset is not a Texture2D — {asset_path}"

    texture.set_editor_property("srgb", False)
    unreal.EditorAssetLibrary.save_asset(asset_path)

    return True, f"sRGB disabled on {texture.get_name()}"


def enable_mipmaps(asset_path):
    """
    Re-enables mipmap generation on a texture that had it disabled.

    :param asset_path: (str) The location of the asset in Content Browser

    :return: (tuple) Success: bool, Message: str

    """

    texture = unreal.EditorAssetLibrary.load_asset(asset_path)

    if not texture:
        return False, f"Could not load asset at {asset_path}"

    if not isinstance(texture, unreal.Texture2D):
        return False, f"Asset is not a Texture2D — {asset_path}"

    mip_gen_settings = unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP
    texture.set_editor_property("mip_gen_settings", mip_gen_settings)
    unreal.EditorAssetLibrary.save_asset(asset_path)

    return True, f"Mipmaps enabled on {texture.get_name()}"

fixes = {
    "generate_lods": generate_lods,
    "enable_nanite": enable_nanite,
    "fix_srgb_off": fix_srgb_off,
    "enable_mipmaps": enable_mipmaps,
}

def run_fix(fix_function_name, asset_path):
    """
    Looks up and runs the correct fix function by name.

    :param fix_function_name: (str) Name of fix function to run
    :param asset_path: (str) Content browser asset path to run fix function on

    :return: (tuple) Success: bool, Message: str
    """

    fix_function = fixes.get(fix_function_name)

    if not fix_function:
        return False, f"Unknown fix function: {fix_function_name}"

    return fix_function(asset_path)