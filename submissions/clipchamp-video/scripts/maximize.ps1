Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win {
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int t, bool r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
}
"@ -ErrorAction SilentlyContinue

Add-Type -AssemblyName System.Windows.Forms
$wa = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea

$targets = Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" |
  Where-Object { $_.CommandLine -like '*video-work\edge-tenant*' } |
  Select-Object -ExpandProperty ProcessId

$done = 0
foreach ($procId in $targets) {
  $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
  if ($p -and $p.MainWindowHandle -ne 0 -and [Win]::IsWindowVisible($p.MainWindowHandle)) {
    [Win]::ShowWindow($p.MainWindowHandle, 9) | Out-Null   # SW_RESTORE
    [Win]::MoveWindow($p.MainWindowHandle, $wa.X, $wa.Y, $wa.Width, $wa.Height, $true) | Out-Null
    [Win]::ShowWindow($p.MainWindowHandle, 3) | Out-Null   # SW_MAXIMIZE
    [Win]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
    Write-Host "maximized pid=$procId to $($wa.Width)x$($wa.Height)"
    $done++
  }
}
if ($done -eq 0) { Write-Host "no visible edge window found" }
