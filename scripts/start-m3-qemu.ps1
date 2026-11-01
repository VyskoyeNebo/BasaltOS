param(
    [ValidateSet('live','disk')][string]$Boot = 'live',
    [ValidateSet('bios','uefi')][string]$Firmware = 'bios',
    [ValidateSet('whpx','tcg')][string]$Accelerator = 'whpx',
    [ValidateSet('sdl','none')][string]$Display = 'sdl',
    [string]$Iso,
    [string]$Disk,
    [switch]$CreateDisk,
    [int]$QmpPort = 4453
)
$ErrorActionPreference = 'Stop'
$projectDir = Split-Path -Parent $PSScriptRoot
$testDir = Join-Path $projectDir 'work\m3'
$qemuRoot = Join-Path $projectDir 'work\tools\msys2\ucrt64'
$qemuExe = Join-Path $qemuRoot 'bin\qemu-system-x86_64.exe'
if (-not (Test-Path -LiteralPath $qemuExe)) { throw 'Prepare portable QEMU first.' }
New-Item -ItemType Directory -Force -Path $testDir | Out-Null
if (-not $Disk) { $Disk = Join-Path $testDir 'installed.qcow2' }
$Disk = [IO.Path]::GetFullPath($Disk)
$allowedPrefix = [IO.Path]::GetFullPath($testDir).TrimEnd('\') + '\'
if (-not $Disk.StartsWith($allowedPrefix,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($Disk) -ne '.qcow2') {
    throw 'The M3 test disk must be a qcow2 file inside this project work/m3 directory.'
}
if ($CreateDisk) {
    if (Test-Path -LiteralPath $Disk) { throw 'Test disk already exists; choose a new filename.' }
    & (Join-Path $qemuRoot 'bin\qemu-img.exe') create -f qcow2 $Disk 48G
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create M3 test disk.' }
}
if (-not (Test-Path -LiteralPath $Disk)) { throw 'No test disk found; use -CreateDisk for a fresh disk.' }
$qemuArgs = @('-L',(Join-Path $qemuRoot 'share\qemu'),'-machine','q35','-m','8192',
    '-device','virtio-vga','-display',$Display,'-device','qemu-xhci','-device','usb-tablet',
    '-netdev','user,id=net0','-device','virtio-net-pci,netdev=net0',
    '-drive',"file=$Disk,if=none,id=target,format=qcow2",
    '-device','virtio-blk-pci,drive=target,serial=BASALTOS_M3_TARGET',
    '-qmp',"tcp:127.0.0.1:$QmpPort,server=on,wait=off",'-no-reboot')
if ($Boot -eq 'live') {
    if (-not $Iso) { $Iso = (Get-ChildItem (Join-Path $projectDir 'out\m3\basaltos-*.iso') | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName }
    if (-not $Iso -or -not (Test-Path -LiteralPath $Iso)) { throw 'No M3 ISO found.' }
    $qemuArgs += @('-boot','d','-cdrom',$Iso)
} else { $qemuArgs += @('-boot','c') }
if ($Firmware -eq 'uefi') {
    $varsFile = Join-Path $testDir 'edk2-vars.fd'
    if (-not (Test-Path -LiteralPath $varsFile)) { Copy-Item -LiteralPath (Join-Path $qemuRoot 'share\qemu\edk2-i386-vars.fd') -Destination $varsFile }
    $codeFile = Join-Path $qemuRoot 'share\qemu\edk2-x86_64-code.fd'
    $qemuArgs += @('-drive',"if=pflash,format=raw,readonly=on,file=$codeFile",'-drive',"if=pflash,format=raw,file=$varsFile")
}
if ($Accelerator -eq 'whpx') { $qemuArgs += @('-accel','whpx','-cpu','max','-smp','4') }
else { $qemuArgs += @('-accel','tcg,thread=single','-icount','shift=auto,sleep=on','-rtc','clock=vm','-cpu','qemu64','-smp','1') }
$logPrefix = Join-Path $testDir "qemu-$Boot-$Firmware-$Accelerator"
$windowStyle = if ($Display -eq 'none') { 'Hidden' } else { 'Normal' }
$qemuProcess = Start-Process -FilePath $qemuExe -ArgumentList $qemuArgs -WindowStyle $windowStyle `
    -RedirectStandardError "$logPrefix.stderr.log" -RedirectStandardOutput "$logPrefix.stdout.log" -PassThru
$qemuProcess.Id | Set-Content "$logPrefix.pid"
Write-Output "QEMU PID $($qemuProcess.Id); boot=$Boot; firmware=$Firmware; QMP=127.0.0.1:$QmpPort; disk=$Disk"
