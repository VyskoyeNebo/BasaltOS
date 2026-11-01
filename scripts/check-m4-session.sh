#!/usr/bin/env bash
# Run from Konsole in the real normal-user gaming desktop session.
set -euo pipefail
(( EUID != 0 )) || { echo 'Run in the normal gaming user session.' >&2; exit 1; }
action="${1:-baseline}"
export LC_ALL=C.UTF-8
case "$action" in
baseline)
    log="$HOME/m4-session-check.log"
    exec > >(tee "$log") 2>&1
    trap 'status=$?; curl -fsS -T "$log" http://10.0.2.2:8181/work/m4/session-check.log || true; exit "$status"' EXIT
    id
    hostnamectl --static
    [[ "$(hostnamectl --static)" == basaltos ]]
    [[ "$(readlink /etc/localtime)" == /usr/share/zoneinfo/Asia/Shanghai ]]
    cat /etc/locale.conf
    df -h / /run/archiso/cowspace
    available="$(df -P -B1 / | awk 'NR==2 {print $4}')"
    (( available >= 1000000000 )) || { echo 'Live writable layer is too small for Steam.' >&2; exit 1; }
    pacman -Q steam steam-devices lutris gamescope mangohud lib32-mangohud \
        gamemode lib32-gamemode mesa lib32-mesa vulkan-icd-loader lib32-vulkan-icd-loader \
        vulkan-radeon lib32-vulkan-radeon vulkan-intel lib32-vulkan-intel \
        vulkan-swrast lib32-vulkan-swrast wine-staging winetricks python-protobuf
    grep -A1 '^\[multilib\]' /etc/pacman.conf
    [[ "$(pacman-conf -r multilib Server)" == https://mirrors.tuna.tsinghua.edu.cn/archlinux/multilib/os/x86_64 ]]
    [[ -r "$HOME/.config/MangoHud/MangoHud.conf" ]]
    [[ -x "$HOME/Desktop/steam.desktop" && -x "$HOME/Desktop/lutris.desktop" ]]
    [[ "$(systemctl --user is-enabled gamemoded.service)" == enabled ]]
    [[ "$(systemctl --user is-active gamemoded.service)" == active ]]
    systemctl --user status gamemoded.service --no-pager
    vulkaninfo --summary
    glxinfo -B
    wine --version
    gamescope --version
    lutris --version
    ip -br a
    pgrep -a fcitx5
    curl -fsSI --max-time 30 https://mirrors.tuna.tsinghua.edu.cn/archlinux/
    echo M4_SESSION_BASELINE_PASSED
    ;;
demo)
    if [[ "${2:-vulkan}" == opengl ]]; then
        nohup gamemoderun mangohud --dlsym glxgears -geometry 960x640 > "$HOME/m4-glxgears.log" 2>&1 &
    else
        nohup gamemoderun mangohud vkcube --width 960 --height 640 > "$HOME/m4-vkcube.log" 2>&1 &
    fi
    echo "$!" > "$HOME/m4-demo.pid"
    echo 'Started the real GameMode + MangoHud graphics demo.'
    ;;
gamemode)
    log="$HOME/m4-gamemode-check.log"
    exec > >(tee "$log") 2>&1
    trap 'status=$?; curl -fsS -T "$log" http://10.0.2.2:8181/work/m4/gamemode-check.log || true; exit "$status"' EXIT
    systemctl --user status gamemoded.service --no-pager
    status="$(gamemoded -s)"
    printf '%s\n' "$status"
    grep -Eq '(^|[[:space:]])active([[:space:]]|$)' <<< "$status"
    gamemodelist
    pgrep -a 'vkcube|glxgears'
    echo M4_GAMEMODE_ACTIVE_PASSED
    ;;
*) echo 'Use baseline, demo or gamemode.' >&2; exit 2 ;;
esac
