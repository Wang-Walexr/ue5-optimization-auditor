"""
UE5 Scene Audit
Scans the currently open level for performance issues: instancing opportunities, material slot draw call cost,
dynamic light count, and particle system count.
"""

import unreal
from collections import defaultdict

frame_target_multipliers = {
    30: 1.2,
    60: 1.0,
    120: 0.7
}



def run_scene_audit(max_draw_calls = 5000, max_lights = 20, instance_threshold = 30, frame_target = 60):
    """
    Runs a full scene audit on the currently open level.

    Args:
        :param max_draw_calls: (int) Maximum recommended draw calls for platform
        :param max_lights: (int) Maximum recommended dynamic shadow-casting lights
        :param instance_threshold: (int) Mesh copies above this should be instanced
        :param frame_target: (int) Target FPS - 30, 60, or 120

    Return
        :return: (list) List of result dicts with name, path, issue, severity, fix_type, fix_function
    """

    multiplier = frame_target_multipliers.get(frame_target, 1.0)
    adjusted_instance_threshold = int(instance_threshold * multiplier)
    adjusted_light_threshold = int(max_lights * multiplier)

    results = []

    mesh_groups = defaultdict(list) # Group static mesh actors by mesh asset
    dynamic_light_count = 0
    particle_count = 0

    # Get Level Subsystem
    level_actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = level_actor_subsystem.get_all_level_actors()



    for actor in all_actors:

        # Static Mesh
        if isinstance(actor, unreal.StaticMeshActor):
            static_mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)

            if static_mesh_component:
                mesh = static_mesh_component.get_editor_property("static_mesh")

                if mesh:
                    mesh_path = mesh.get_path_name()
                    mesh_groups[mesh_path].append(actor)


        # Light
        elif isinstance(actor, unreal.Light):
            light_component = actor.get_component_by_class(unreal.LightComponent)

            if light_component:
                light = light_component.get_editor_property("mobility")

                if light == unreal.ComponentMobility.MOVABLE:
                    dynamic_light_count += 1

        # Particles
        elif isinstance(actor, unreal.NiagaraActor):
            particle_count += 1

    # Check 1: Instancing and Material Slot (Draw Calls)
    for mesh_path, actors in mesh_groups.items():
        mesh_instance_count = len(actors)
        mesh_name = mesh_path.split(".")[-1]


        # Get material slot count
        component = actors[0].get_component_by_class(unreal.StaticMeshComponent)
        material_count = len(component.get_materials()) if component else 1
        material_count = max(material_count, 1)


        draw_call_cost = mesh_instance_count * material_count


        # Flag instancing
        if mesh_instance_count > adjusted_instance_threshold:
            results.append({
                "name": mesh_name,
                "path": mesh_path,
                "issue": f"{mesh_instance_count} uninstanced copies (threshold {adjusted_instance_threshold} @ {frame_target}fps)",
                "severity": "WARNING",
                "fix_type": "MANUAL",
                "fix_function": "none"
            })

        # Flag material slot draw call cost
        if draw_call_cost > (max_draw_calls * 0.02):
            severity = "CRITICAL" if draw_call_cost > (max_draw_calls * 0.1) else "WARNING"
            results.append({
                "name": mesh_name,
                "path": mesh_path,
                "issue": f"{material_count} slots x {mesh_instance_count} instances = {draw_call_cost} draw calls. Try reducing material slots",
                "severity": severity,
                "fix_type": "MANUAL",
                "fix_function": "none"
            })

    # Check 2: Dynamic Light
    if dynamic_light_count > adjusted_light_threshold:
        severity = "CRITICAL" if dynamic_light_count > adjusted_light_threshold * 2 else "WARNING"
        results.append({
            "name": "Scene Lights",
            "path": "N/A",
            "issue": f"{dynamic_light_count} dynamic lights (threshold {adjusted_light_threshold} @ {frame_target}fps). Try reducing lights or change some or all to static",
            "severity": severity,
            "fix_type": "MANUAL",
            "fix_function": "none"
        })
    else:
        results.append({
            "name": "Scene Lights",
            "path": "N/A",
            "issue": f"{dynamic_light_count} dynamic lights — within threshold",
            "severity": "PASS",
            "fix_type": "NONE",
            "fix_function": "none"
        })

    # Check 3: Particle count
    if particle_count > 50:
        results.append({
            "name": "Scene Particles",
            "path": "N/A",
            "issue": f"{particle_count} Niagara systems in scene",
            "severity": "WARNING",
            "fix_type": "MANUAL",
            "fix_function": "none"
        })
    elif particle_count > 20:
        results.append({
            "name": "Scene Particles",
            "path": "N/A",
            "issue": f"{particle_count} Niagara systems in scene",
            "severity": "INFO",
            "fix_type": "MANUAL",
            "fix_function": "none"
        })

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

