IMAGE_INSTALL:append = " xrt-dev"
IMAGE_INSTALL:append = " xrt"
IMAGE_INSTALL:append = " zocl"
IMAGE_INSTALL:append = " opencl-headers-dev"
IMAGE_INSTALL:append = " opencl-clhpp-dev"

# Ensure sudo and bash are present for the xilinx user added below.
IMAGE_INSTALL:append = " sudo bash"

# ---------------------------------------------------------------------------
# Default user account for PYNQ.remote images
# ---------------------------------------------------------------------------
# Create an `xilinx` user with password `xilinx` so users can SSH into a
# freshly-flashed board without going through PetaLinux's first-boot password
# prompt. The user is a member of the `sudo` group so it can `sudo` with its
# password (no NOPASSWD by default).
#
# SECURITY: The credentials xilinx/xilinx are well-known. This is convenient
# for lab use only. Users SHOULD change the password on first login with
# `passwd`, and SHOULD NOT expose these boards directly to untrusted networks.
#
# The password is stored as a pre-computed SHA-512 crypt hash so the build
# does not depend on `openssl passwd` being available on the host. To
# regenerate, run on a Linux host:
#     python3 -c "import crypt; print(crypt.crypt('xilinx', crypt.mksalt(crypt.METHOD_SHA512)))"
# and replace the hash below.
inherit extrausers

EXTRA_USERS_PARAMS = "\
    useradd -m -d /home/xilinx -s /bin/bash -p '\$6\$pynqRem0te\$NYqCojvG5GNJmsxZTdwpXoD4wHz/q0LO8PxHIeADwFfkcFfeblT/c7LXeqhX4R1SqLZhBk.4ryTqEwIqwooU6/' xilinx; \
    usermod -a -G sudo,video,audio,dialout,plugdev xilinx; \
    userdel -r petalinux || true; \
    "
