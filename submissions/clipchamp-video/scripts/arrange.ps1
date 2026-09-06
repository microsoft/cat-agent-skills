# arrange.ps1 — put the automated browser on the left half and Scout on the right half,
# so a single gdigrab desktop capture shows the agent actions AND the chat, in sync.
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinArr {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int t, bool r);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
}
"@ -ErrorAction SilentlyContinue

Add-Type -AssemblyName System.Windows.Forms
$wa   = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea
$half = [int]($wa.Width / 2)

function Place([IntPtr]$h, [int]$x, [int]$w) {
  [WinArr]::ShowWindow($h, 9) | Out-Null                                   # SW_RESTORE first
  [WinArr]::MoveWindow($h, $x, $wa.Y, $w, $wa.Height, $true) | Out-Null
}

# Left half: the automated browser (matched by its cloned profile dir on the command line)
$placedBrowser = 0
Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
  Where-Object { $_.CommandLine -like '*edge-tenant*' } | ForEach-Object {
    $p = Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue
    if ($p -and $p.MainWindowHandle -ne 0 -and [WinArr]::IsWindowVisible($p.MainWindowHandle)) {
      Place $p.MainWindowHandle 0 $half
      Write-Host "browser pid=$($p.Id) -> left ${half}x$($wa.Height)"
      $placedBrowser++
    }
  }
if ($placedBrowser -eq 0) { Write-Host "WARN: no automated browser window found" }

# Right half: the Scout window
$placedScout = 0
Get-Process -ErrorAction SilentlyContinue |
  Where-Object { $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -and
                 ($_.ProcessName -match 'Scout|Clawpilot' -or $_.MainWindowTitle -match 'Scout') } |
  ForEach-Object {
    Place $_.MainWindowHandle $half $half
    Write-Host "scout pid=$($_.Id) '$($_.MainWindowTitle)' -> right ${half}x$($wa.Height)"
    $placedScout++
  }
if ($placedScout -eq 0) { Write-Host "WARN: no Scout window found - right half will show the desktop" }
