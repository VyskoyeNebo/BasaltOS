param(
    [ValidateSet('whpx','tcg')][string]$Accelerator = 'whpx',
    [string]$Iso,
    [int]$QmpPort = 4452
)
$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$qemuExe = Join-Path $projectDir 'work\tools\msys2\ucrt64\bin\qemu-system-x86_64.exe'
if (-not (Test-Path -LiteralPath $qemuExe)) { throw 'Run python scripts/setup-qemu-windows.py first.' }
if (-not $Iso) {
    $Iso = (Get-ChildItem (Join-Path $projectDir 'out\m2\basaltos-*.iso') | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
}
if (-not $Iso -or -not (Test-Path -LiteralPath $Iso)) { throw 'No M2 ISO found.' }
$qemuArgs = @('-L', (Join-Path $projectDir 'work\tools\msys2\ucrt64\share\qemu'),
    '-machine','q35','-m','6144','-boot','d','-cdrom',$Iso,
    '-device','virtio-vga','-display','none',
    '-device','qemu-xhci','-device','usb-tablet',
    '-netdev','user,id=net0','-device','virtio-net-pci,netdev=net0',
    '-qmp',"tcp:127.0.0.1:$QmpPort,server=on,wait=off",'-no-reboot')
if ($Accelerator -eq 'whpx') {
    $qemuArgs += @('-accel','whpx','-cpu','max','-smp','4')
} else {
    $qemuArgs += @('-accel','tcg,thread=single','-icount','shift=auto,sleep=on','-rtc','clock=vm','-cpu','qemu64','-smp','1')
}
$logPrefix = Join-Path $projectDir "work\m2-qemu-$Accelerator"
$qemuProcess = Start-Process -FilePath $qemuExe -ArgumentList $qemuArgs -WindowStyle Hidden `
    -RedirectStandardError "$logPrefix.stderr.log" -RedirectStandardOutput "$logPrefix.stdout.log" -PassThru
$qemuProcess.Id | Set-Content "$logPrefix.pid"
Write-Output "QEMU PID $($qemuProcess.Id); accelerator=$Accelerator; QMP=127.0.0.1:$QmpPort"
