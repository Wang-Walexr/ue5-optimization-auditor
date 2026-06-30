# UE5 Optimization Auditor

**Status:** Work in progress (UI complete, audit logic in development)

An Editor Utility Widget for Unreal Engine 5.7 that audits scenes 
and assets for common performance issues, with platform-aware 
thresholds and automated fixes where safe.

See [SPEC.md](SPEC.md) for the full design specification.

## Planned Features

- Scene Audit — instancing opportunities, draw call cost, 
  dynamic light count
- Asset Audit — missing LODs, Nanite candidates, oversized 
  textures, incorrect sRGB settings
- Platform presets (PC / Console / Mobile) with editable thresholds
- Frame budget awareness (30/60/120 FPS)
- Auto-fix for safe operations, clear recommendations for 
  artist-judgement issues

## Current Progress

- [x] Full UI shell built (Editor Utility Widget)
- [x] Platform preset system with editable thresholds
- [x] Reusable result row widget with severity color coding
- [ ] Scene Audit logic
- [ ] Asset Audit logic
- [ ] Fix operations
- [ ] Demo video

## Installation

### Option 1: Migrate (Recommended)
1. Open this project in Unreal Engine 5.7
2. In the Content Browser, locate `EUW_OptimizationAuditor`
3. Right click → Asset Actions → Migrate
4. Select your project's Content folder as the destination
5. Unreal will copy the tool and all dependencies automatically

### Option 2: Manual Copy
1. Copy the `Content/OptimizationAuditor/` folder from this 
   repo into your project's Content folder
2. Reopen your project in Unreal
3. Right click `EUW_OptimizationAuditor` → Run Editor Utility Widget

## Requirements
- Unreal Engine 5.7+
- Python Editor Script Plugin enabled
- Editor Scripting Utilities plugin enabled


## Built With

- Unreal Engine 5.7
- Blueprint
- Python


## Screenshot
![Optimization Auditor Preview](preview.png)