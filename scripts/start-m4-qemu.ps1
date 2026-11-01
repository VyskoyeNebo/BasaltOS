param(
    [ValidateSet('bios','uefi')][string]$Firmware = 'uefi',
    [ValidateSet('whpx','tcg')][string]$Accelerator = 'whpx',
    [ValidateSet('sdl','none')][string]$Display = 'sdl',
    [string]$Iso,
    [int]$QmpPort = 4454
)
$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$testDir = Join-Path $projectDir 'work\m4'
$qemuRoot = Join-Path $projectDir 'work\tools\msys2\ucrt64'
$qemuExe = Join-Path $qemuRoot 'bin\qemu-system-x86_64.exe'
if (-not (Test-Path -LiteralPath $qemuExe)) { throw 'Prepare portable QEMU first.' }
New-Item -ItemType Directory -Force -Path $testDir | Out-Null
if (-not $Iso) { $Iso = (Get-ChildItem (Join-Path $projectDir 'out\m4\basaltos-*.iso') | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName }
if (-not $Iso -or -not (Test-Path -LiteralPath $Iso)) { throw 'No M4 ISO found.' }
$qemuArgs = @('-L',(Join-Path $qemuRoot 'share\qemu'),'-machine','q35','-m','16384',
    '-device','virtio-vga','-display',$Display,'-device','qemu-xhci','-device','usb-tablet',
    '-netdev','user,id=net0','-device','virtio-net-pci,netdev=net0',
    '-boot','d','-cdrom',$Iso,
    '-qmp',"tcp:127.0.0.1:$QmpPort,server=on,wait=off",'-no-reboot')
if ($Firmware -eq 'uefi') {
    $varsFile = Join-Path $testDir 'm4-live.edk2-vars.fd'
    if (-not (Test-Path -LiteralPath $varsFile)) { Copy-Item -LiteralPath (Join-Path $qemuRoot 'share\qemu\edk2-i386-vars.fd') -Destination $varsFile }
    $codeFile = Join-Path $qemuRoot 'share\qemu\edk2-x86_64-code.fd'
    $qemuArgs += @('-drive',"if=pflash,format=raw,readonly=on,file=$codeFile",'-drive',"if=pflash,format=raw,file=$varsFile")
}
if ($Accelerator -eq 'whpx') { $qemuArgs += @('-accel','whpx','-cpu','max','-smp','4') }
else { $qemuArgs += @('-accel','tcg,thread=single','-icount','shift=auto,sleep=on','-rtc','clock=vm','-cpu','qemu64','-smp','1') }
$logPrefix = Join-Path $testDir "qemu-$Firmware-$Accelerator"
$windowStyle = if ($Display -eq 'none') { 'Hidden' } else { 'Normal' }
$qemuProcess = Start-Process -FilePath $qemuExe -ArgumentList $qemuArgs -WindowStyle $windowStyle `
    -RedirectStandardError "$logPrefix.stderr.log" -RedirectStandardOutput "$logPrefix.stdout.log" -PassThru
Start-Sleep -Milliseconds 750
if ($qemuProcess.HasExited) {
    $details = Get-Content -LiteralPath "$logPrefix.stderr.log" -Raw
    throw "QEMU exited during startup (code $($qemuProcess.ExitCode)). $details"
}
$qemuProcess.Id | Set-Content "$logPrefix.pid"
Write-Output "QEMU PID $($qemuProcess.Id); M4 live; firmware=$Firmware; QMP=127.0.0.1:$QmpPort; no hard disk attached"
