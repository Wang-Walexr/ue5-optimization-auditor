# UE5 Optimization Auditor — Tool Specification

**Version:** 1.0  
**Engine:** Unreal Engine 5.7  
**Type:** Editor Utility Widget (EUW)  
**Author:** Adewale Abdulkabir  
**Status:** Pre-build spec. Approved for development

---

## Problem Statement

TAs and artists working in Unreal Engine 5 have no single tool to identify 
and fix performance issues across scenes and assets. Optimization problems 
are caught late in production, often only when a scene is already in the 
hands of a director or client, causing expensive rework and pipeline 
disruption.

This tool gives any team member a one-click optimization audit with clear, 
prioritized results and automated fixes where safe to apply.

---

## Target Users

- Technical Artists running project-wide audits
- Artists checking their own assets before submission
- TDs reviewing scene performance before milestone deliveries

---

## Tool Overview

A single Editor Utility Widget panel with two audit modes (Scene and Asset),
platform-aware thresholds, frame budget awareness, color-coded severity 
results, and automated fixes for safe operations.

---

## UI Layout

```
┌─────────────────────────────────────────────────────┐
│  UE5 OPTIMIZATION AUDITOR                           │
├─────────────────────────────────────────────────────┤
│  PLATFORM SETTINGS                                  │
│  Platform: [PC ▼]          Frame Target: [60fps ▼] │
│                                                     │
│  Max Texture Size:  [4096]  Max Draw Calls: [5000] │
│  Max Lights:        [20  ]  LOD Threshold:  [5000] │
│  Instance Threshold:[30  ]                          │
│                             [Reset to Defaults]     │
├─────────────────────────────────────────────────────┤
│  SCAN TARGET (Asset Audit only)                     │
│  Folder: /Game/             [Use Selected Folder]   │
├─────────────────────────────────────────────────────┤
│  [    Scene Audit    ]      [    Asset Audit    ]   │
├─────────────────────────────────────────────────────┤
│  Last scan: — not run yet —                         │
│  ┌───────────────────────────────────────────────┐  │
│  │ [CRIT]  SM_Rock_01 — No LODs — [AUTO]        │  │
│  │ [WARN]  T_Floor_D — 4K texture — [MANUAL]    │  │
│  │ [INFO]  22 lights in scene — [MANUAL]        │  │
│  └───────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────┤
│  [    Fix Selected    ]     [      Fix All      ]   │
└─────────────────────────────────────────────────────┘
```

---

## Platform Presets

Default values per platform. All values are editable from the UI.
Changing platform does not auto-rerun. User must click audit again.

| Setting | PC | Console | Mobile |
|---|---|---|---|
| Max texture size (px) | 4096 | 2048 | 1024 |
| Max draw calls | 5000 | 3000 | 300 |
| Max dynamic lights | 20 | 10 | 4 |
| LOD required above (tris) | 5000 | 3000 | 1000 |
| Instancing threshold (copies) | 30 | 20 | 10 |

---

## Frame Budget Targets

| Target | Frame budget |
|---|---|
| 30 FPS | 33.3ms |
| 60 FPS | 16.6ms |
| 120 FPS | 8.3ms |

Frame budget is used to contextualise GPU timing data where available.
Same data reads differently at different frame targets. A 20ms GPU time
is PASS at 30fps, WARNING at 60fps, CRITICAL at 120fps.

---

## Severity Levels

| Level | Color | Meaning |
|---|---|---|
| CRITICAL | Red | Will cause performance problems. Fix before shipping. |
| WARNING | Yellow | Likely to cause problems at scale or on lower-end hardware. |
| INFO | White | Worth knowing. Monitor as project grows. |
| PASS | Green | No issue found. |

Severity thresholds:
- CRITICAL: exceeds platform preset by more than 2x
- WARNING: exceeds platform preset or approaching limit (>75%)
- INFO: notable but within acceptable range

---

## Scene Audit

Scans the current open level for performance issues.

### Checks performed

**Static Mesh Actor Count**
- Count all StaticMeshActor instances in the level
- Flag if count exceeds instancing threshold × 10
- Severity: WARNING if >500, CRITICAL if >1000 (PC preset)
- Fix type: MANUAL. Recommend converting to HISM

**Instancing Opportunities**
- Group identical meshes by asset path
- Calculate instance count per unique mesh
- Flag any mesh appearing more than instancing threshold times
  without being an ISM/HISM component
- Severity: WARNING
- Fix type: AUTO. Convert to ISM (where safe)
- Display: "SM_Rock appears 47 times uninstanced — 47 draw calls.
  Convert to ISM to reduce to 1."

**Material Slot Draw Call Cost**
- For each unique static mesh in the level:
  - Get material slot count
  - Get instance count
  - Calculate cost: slots × instances
- Flag if cost exceeds draw call threshold contribution
- Severity: WARNING if cost > 100, CRITICAL if cost > 500
- Fix type: MANUAL. Recommend texture atlasing to reduce slots
- Display: "SM_Barrel — 4 slots × 200 instances = 800 draw calls.
  Reduce to 1-2 slots via texture atlasing."

**Dynamic Light Count**
- Count all dynamic shadow-casting lights
- Flag if count exceeds platform preset max lights
- Severity: WARNING if >max, CRITICAL if >max × 2
- Fix type: MANUAL. Recommend switching to static/stationary
- Display: "28 dynamic lights found. PC preset recommends max 20.
  Consider baking static lights."

**Particle and Niagara System Count**
- Count all NiagaraActor and ParticleSystemActor instances
- Flag if count exceeds 20 (INFO) or 50 (WARNING)
- Fix type: MANUAL. Recommend VFX budget review
- Severity: INFO / WARNING
- Note: Particle count is INFO-level only because count alone doesn't correlate reliably with performance cost. Flagging it as actionable would overstate the tool's certainty.

---

## Asset Audit

Scans a Content Browser folder for asset quality issues.
Folder is selectable via dropdown or Content Browser selection.

### Checks performed

**Missing LODs**
- Find all StaticMesh assets with LOD count <= 1
- Cross-reference triangle count against LOD threshold
- Only flag meshes above the threshold. Small meshes may not need LODs
- Severity: CRITICAL if above threshold with no LODs
- Fix type: AUTO. Generate 4-LOD chain using StaticMeshEditorSubsystem
- Display: "SM_Rock_Hero — 12,847 tris — No LODs. Will auto-generate."

**Nanite Candidates**
- Find StaticMesh assets with Nanite disabled
- Qualify candidates: opaque material, not skeletal, not foliage
- Severity: WARNING
- Fix type: AUTO. Enable Nanite via Python
- Display: "SM_ColumnBase — Nanite disabled. Qualifies for Nanite.
  Enable to remove polygon budget concern."

**Oversized Textures**
- Find Texture2D assets exceeding platform max texture size
- Severity: WARNING if >max, CRITICAL if >max × 2
- Fix type: MANUAL. Flag with recommended size
- Display: "T_WallConcrete_D — 8192×8192 — exceeds 4096px limit.
  Resize to 4096×4096 in source DCC."

**Wrong sRGB Settings**
- Color/albedo textures should have sRGB ON
- Normal, roughness, metallic, AO textures should have sRGB OFF
- Detect by texture name suffix convention:
  _D / _Albedo / _Color → sRGB should be ON
  _N / _Normal → sRGB should be OFF, compression Normalmap
  _R / _Roughness / _M / _Metallic / _AO → sRGB should be OFF
- Severity: WARNING
- Fix type: AUTO. Set correct sRGB value via Python
- Display: "T_Rock_N — Normal map has sRGB ON. Auto-fix available."

**Missing Mipmaps**
- Check if MipGenSettings is set to NoMipmaps
- Severity: WARNING
- Fix type: AUTO. Enable mipmap generation
- Display: "T_ProceduralNoise — Mipmaps disabled. Enable for
  correct distance rendering."

---

## Fix System

### Fix Selected
- User selects one or more rows in the results panel
- Clicking Fix Selected runs AUTO fixes on selected rows only
- MANUAL rows are skipped with a note explaining why
- Results panel updates after fix to show new status

### Fix All
- Runs AUTO fixes on every flagged item in the results panel
- MANUAL items are skipped and remain in results with
  their recommendation visible
- Results panel re-runs the relevant audit after fixing
  to confirm issues are resolved

### Fix confirmation
No popup confirmation dialog. The results panel itself
serves as the confirmation. What is shown is what will be fixed.
MANUAL items are visually distinct so there is no ambiguity
about what the tool will and won't change automatically.

## Fix Distribution

Most auto-fixable issues come from Asset Audit (technical, reversible
problems). Most Scene Audit findings are MANUAL by design — instancing,
material slot reduction, and lighting mobility all involve tradeoffs
that require artist or TA judgment and cannot be safely automated
without risking unintended visual or gameplay changes.

---

## Auto-fixable Operations

| Issue | Fix applied | API used |
|---|---|---|
| Missing LODs | Generate 4-LOD chain | StaticMeshEditorSubsystem.set_lods() |
| Nanite disabled | Enable Nanite | StaticMesh.set_editor_property('nanite_settings') |
| Wrong sRGB | Set correct value | Texture2D.set_editor_property('srgb') |
| Missing mipmaps | Enable mip generation | Texture2D.set_editor_property('mip_gen_settings') |

---

## Recommendation Only (MANUAL)

| Issue | Recommendation shown |
|---|---|
| Oversized texture | "Resize to Xpx in source DCC and reimport" |
| Too many material slots | "Reduce to 1-2 slots via texture atlasing" |
| Uninstanced meshes | "Convert to ISM via right click in Outliner" |
| Too many dynamic lights | "Switch distant lights to Static or Stationary" |

---

## Python Script Architecture

All audit logic lives in Python scripts called from the EUW via
Execute Python Script nodes. Results are passed back to Blueprint
via output pins for display in the results panel.

```
EUW (Blueprint)
    ↓ calls
scene_audit.py
    → check_instancing_opportunities()
    → check_material_slot_cost()
    → check_dynamic_light_count()
    → check_particle_count()

asset_audit.py  
    → find_meshes_without_lods()
    → find_nanite_candidates()
    → find_oversized_textures()
    → find_wrong_srgb_textures()
    → find_missing_mipmaps()

fix_operations.py
    → generate_lods()
    → enable_nanite()
    → fix_srgb()
    → enable_mipmaps()
```

Each function returns a list of result dicts:
```python
{
    "name": "SM_Rock_01",
    "path": "/Game/Meshes/SM_Rock_01",
    "issue": "No LODs — 12,847 triangles",
    "severity": "CRITICAL",
    "fix_type": "AUTO",
    "fix_function": "generate_lods"
}
```

---

## Out of Scope (v1)

- Texture resizing automation (requires DCC round-trip)
- Material merging and texture atlasing
- Skeletal mesh optimization
- Landscape optimization
- VFX budget analysis beyond count
- Lighting bake recommendations
- HTML/PDF report export
- Change tracking between audits
- Unreal Insights integration
- Batch scene profiling across multiple levels
- Sample/test scene loader

These are documented as v2 features in the GitHub README.

---

## Success Criteria

The tool is complete when:
- Scene Audit correctly flags all defined issues in a test scene
- Asset Audit correctly flags all defined issues in a test folder
- AUTO fixes resolve flagged issues and results update to PASS
- MANUAL recommendations display clearly with actionable guidance
- Platform presets change thresholds correctly
- Frame target changes severity correctly
- Tool runs without errors on a clean UE5.7 project

---

## Portfolio Documentation Plan

**GitHub repo:** ue5-optimization-auditor  
**Demo video:** 3-4 minutes showing full workflow  
  - Before: unoptimized scene with known issues  
  - Scene Audit: catching all issues with severity  
  - Asset Audit: catching asset-level issues  
  - Fix All: auto-fixing qualifying issues  
  - After: re-audit showing resolved issues  

**Portfolio writeup:**  
- Problem: studios catch optimization issues too late  
- Solution: one-click audit tool with platform-aware thresholds  
- Result: issues caught at asset creation time, not at delivery  

**LinkedIn post:**  
- Show before/after audit results  
- Highlight the auto-fix vs recommend distinction  
- Explain the platform preset system  

