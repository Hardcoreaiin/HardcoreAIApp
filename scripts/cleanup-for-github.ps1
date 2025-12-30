# Cleanup script for GitHub release
# Run this before git add to remove unwanted files

Write-Host "🧹 Cleaning up Hardcore.ai for GitHub release..." -ForegroundColor Cyan

$rootPath = Split-Path -Parent $PSScriptRoot
if (-not $rootPath) { $rootPath = "." }

# Files to delete in Hardcore.ai (temporary/development scripts)
$hardcoreFiles = @(
    "add_complete_modal.py",
    "add_endpoints.py",
    "add_modal.py",
    "add_modal_final.py",
    "add_sensor_method.py",
    "add_wireless_button_simple.py",
    "add_wireless_features.py",
    "backend_endpoints.py",
    "connection_methods.js",
    "create_clean_chat.py",
    "debug_parser.js",
    "fix_boards_endpoint.py",
    "fix_chat_duplicates.py",
    "fix_chat_html.py",
    "implement_all.py",
    "implementation_plan.html",
    "test_api.py",
    "test_direct_api.py",
    "test_generator.js",
    "test_output.kicad_sch",
    "test_renderer.js",
    "test_schematic.kicad_sch",
    "test_symbols.js",
    "hardcore.db",
    "resolved_pins.h",
    "netlify.toml",
    "vercel.json",
    "render.yaml"
)

# Files to delete in hardcore-desktop
$desktopFiles = @(
    "ERRORS_EXPLAINED.md",
    "IMPLEMENTATION_CHECKLIST.md",
    "IMPROVEMENTS_SUMMARY.md",
    "README_UPDATED.md",
    "UI-DEMO.html",
    "package-simple.json",
    "installer.nsi",
    "test-electron.js",
    "test.js"
)

# Directories to delete
$dirsToDelete = @(
    "Hardcore-Desktop",      # Duplicate
    "Hardcore-Tauri",        # Not used
    "hardcore-desktop/node_modules",
    "hardcore-desktop/dist",
    "hardcore-desktop/dist-react",
    "hardcore-desktop/dist-electron",
    "hardcore-desktop/build",
    "hardcore-desktop/bundled/python",
    "hardcore-desktop/bundled/drivers",
    "Hardcore.ai/__pycache__",
    "Hardcore.ai/orchestrator/__pycache__",
    "Hardcore.ai/workspace",
    "Hardcore.ai/firmware_workspace",
    "Hardcore.ai/diagnostics",
    ".vscode"
)

Write-Host "`n📁 Removing development files from Hardcore.ai..." -ForegroundColor Yellow
foreach ($file in $hardcoreFiles) {
    $path = Join-Path "$rootPath\Hardcore.ai" $file
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "  ✓ Deleted: $file" -ForegroundColor Green
    }
}

Write-Host "`n📁 Removing development files from hardcore-desktop..." -ForegroundColor Yellow
foreach ($file in $desktopFiles) {
    $path = Join-Path "$rootPath\hardcore-desktop" $file
    if (Test-Path $path) {
        Remove-Item $path -Force
        Write-Host "  ✓ Deleted: $file" -ForegroundColor Green
    }
}

Write-Host "`n📂 Removing build/temp directories..." -ForegroundColor Yellow
foreach ($dir in $dirsToDelete) {
    $path = Join-Path $rootPath $dir
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Deleted: $dir" -ForegroundColor Green
    }
}

# Remove .env (has API keys)
$envPath = Join-Path "$rootPath\Hardcore.ai" ".env"
if (Test-Path $envPath) {
    Remove-Item $envPath -Force
    Write-Host "  ✓ Deleted: .env (contains API keys)" -ForegroundColor Green
}

Write-Host "`n✅ Cleanup complete!" -ForegroundColor Cyan
Write-Host "`n📋 Next steps:" -ForegroundColor White
Write-Host "  1. Review remaining files"
Write-Host "  2. git add ."
Write-Host "  3. git commit -m 'Prepare for release'"
Write-Host "  4. git push"
