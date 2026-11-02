#!/usr/bin/env bash
# shellcheck disable=SC2034
iso_name="basaltos"
iso_label="basaltos"
iso_publisher="BasaltOS"
iso_application="BasaltOS M5 Security Live ISO"
iso_version="$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)"
install_dir="basalt"
bootmodes=('bios.syslinux' 'uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/usr/bin/basaltos-update"]="0:0:755"
  ["/etc/skel/Desktop/lutris.desktop"]="0:0:755"
  ["/etc/skel/Desktop/steam.desktop"]="0:0:755"
  ["/root/Desktop/install-basaltos.desktop"]="0:0:755"
  ["/usr/local/lib/basaltos/finalize-installed.sh"]="0:0:755"
  ["/usr/local/bin/install-basaltos"]="0:0:755"
  ["/etc/shadow"]="0:0:400"
  ["/root"]="0:0:750"
)
