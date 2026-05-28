SUMMARY = "PYNQ network interface configuration"
SECTION = "PETALINUX/apps"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

# Mirrors classic PYNQ's sdbuild/packages/ethernet/eth0:
# DHCP on eth0 plus a static 192.168.2.99 alias for hardwired access to a
# headless board. systemd-networkd is the default networking stack on the
# PetaLinux rootfs, so this ships a .network file rather than a Debian-style
# /etc/network/interfaces.d entry. Default behaviour is identical to classic
# PYNQ: static .99 + concurrent DHCP, no multi-board conflict handling.
#
# pynq-network-autoip is shipped but DISABLED by default. It is an opt-in
# oneshot that runs before systemd-networkd and picks a free address in
# 192.168.2.99..110 via arping-based duplicate address detection, writing
# its result to /run/systemd/network/05-eth0-autoip.network (which sorts
# before, and therefore wins against, the shipped /etc/systemd/network/
# 10-eth0.network). Enable it in multi-board labs with:
#   sudo systemctl enable --now pynq-network-autoip

SRC_URI = " \
    file://10-eth0.network \
    file://pynq-network-autoip \
    file://pynq-network-autoip.service \
    file://motd \
    file://hostname \
"

S = "${WORKDIR}"

inherit systemd

RDEPENDS:${PN} = "systemd iputils-arping"

SYSTEMD_SERVICE:${PN} = "pynq-network-autoip.service"
SYSTEMD_AUTO_ENABLE:${PN} = "disable"

do_install() {
    install -d ${D}${sysconfdir}/systemd/network
    install -m 0644 ${WORKDIR}/10-eth0.network ${D}${sysconfdir}/systemd/network/

    install -d ${D}${sbindir}
    install -m 0755 ${WORKDIR}/pynq-network-autoip ${D}${sbindir}/pynq-network-autoip

    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${WORKDIR}/pynq-network-autoip.service \
        ${D}${systemd_system_unitdir}/pynq-network-autoip.service

    install -d ${D}${localstatedir}/lib/pynq-network

    # Ship the PYNQ.remote /etc/motd banner under our own datadir to avoid
    # conflicting with base-files (which already owns /etc/motd). A
    # pkg_postinst hook below copies it into place at rootfs creation, so
    # the welcome banner is visible on the very first SSH/serial login.
    # The pynq-network-autoip service later appends the assigned board IP.
    install -d ${D}${datadir}/pynq-network
    install -m 0644 ${WORKDIR}/motd ${D}${datadir}/pynq-network/motd
    install -m 0644 ${WORKDIR}/hostname ${D}${datadir}/pynq-network/hostname
}

FILES:${PN} += " \
    ${sysconfdir}/systemd/network/10-eth0.network \
    ${sbindir}/pynq-network-autoip \
    ${systemd_system_unitdir}/pynq-network-autoip.service \
    ${localstatedir}/lib/pynq-network \
    ${datadir}/pynq-network/motd \
    ${datadir}/pynq-network/hostname \
"

# Overwrite /etc/motd and /etc/hostname with the PYNQ.remote defaults at
# rootfs assembly time (offline postinst) so those files remain owned by
# base-files. Also append a 127.0.1.1 entry to /etc/hosts so the chosen
# hostname resolves locally, mirroring classic PYNQ's pynq_hostname.sh.
pkg_postinst:${PN} () {
    if [ -f $D${datadir}/pynq-network/motd ]; then
        cp -f $D${datadir}/pynq-network/motd $D${sysconfdir}/motd
    fi
    if [ -f $D${datadir}/pynq-network/hostname ]; then
        cp -f $D${datadir}/pynq-network/hostname $D${sysconfdir}/hostname
        hn=$(cat $D${datadir}/pynq-network/hostname)
        if ! grep -q "127.0.1.1[[:space:]]\+$hn" $D${sysconfdir}/hosts 2>/dev/null; then
            echo "127.0.1.1    $hn" >> $D${sysconfdir}/hosts
        fi
    fi
}
