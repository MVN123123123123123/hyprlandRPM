Name:           linux-cachyos-rt-bore-zen4
Version:        7.1.3
Release:        1%{?dist}
Summary:        Linux BORE-RT + Cachy Sauce Kernel by CachyOS
License:        GPLv2
URL:            https://github.com/CachyOS/linux-cachyos

Source0:        https://github.com/CachyOS/linux/releases/download/cachyos-%{version}-1/cachyos-%{version}-1.tar.gz
Source1:        config
Source2:        https://raw.githubusercontent.com/cachyos/kernel-patches/master/7.1/sched/0001-bore-cachy.patch
Source3:        https://raw.githubusercontent.com/cachyos/kernel-patches/master/7.1/misc/0001-rt-i915.patch
Source4:        https://raw.githubusercontent.com/cachyos/kernel-patches/master/7.1/misc/dkms-clang.patch

BuildRequires:  gcc, make, bc, binutils, elfutils-libelf-devel, openssl-devel, perl, python3, flex, bison, zstd, rsync, kmod, tar, xz, patch
BuildRequires:  clang, llvm, lld

# Prevent stripping by rpmbuild to avoid breaking kernel modules
%global __os_install_post %{nil}
%global debug_package %{nil}

%description
Linux kernel with CachyOS patches, BORE scheduler, and RT preempt, optimized for AMD Zen4/5.
Compiled with LLVM/Clang ThinLTO.

%prep
%setup -q -n cachyos-%{version}-1
# Apply patches
patch -Np1 < %{SOURCE2}
patch -Np1 < %{SOURCE3}
patch -Np1 < %{SOURCE4}

cp %{SOURCE1} .config

# Define localversion to match our RPM name
echo "-cachyos-zen4" > localversion.10-cachyos

# Architecture optimizations for zen4
scripts/config -d GENERIC_CPU -e MZEN4 -d X86_NATIVE_CPU

# Apply config options for RT and BORE
scripts/config -e CACHY -e SCHED_BORE -e PREEMPT_RT

# Enable LLVM ThinLTO
scripts/config -e LTO_CLANG_THIN

# Enable performance optimizations
scripts/config -d CC_OPTIMIZE_FOR_PERFORMANCE -e CC_OPTIMIZE_FOR_PERFORMANCE_O3

%global make_opts LLVM=1 LLVM_IAS=1 CC=clang LD=ld.lld

make %{make_opts} olddefconfig

%build
make %{make_opts} %{?_smp_mflags} all

%install
make %{make_opts} INSTALL_MOD_PATH=%{buildroot}/usr INSTALL_MOD_STRIP=1 modules_install
KVER=$(ls %{buildroot}/usr/lib/modules/ | head -n 1)
mkdir -p %{buildroot}/boot
install -m 644 arch/x86/boot/bzImage %{buildroot}/boot/vmlinuz-${KVER}
install -m 644 System.map %{buildroot}/boot/System.map-${KVER}
install -m 644 .config %{buildroot}/boot/config-${KVER}

%post
KVER=$(ls /usr/lib/modules/ | grep "cachyos-zen4" | head -n 1)
if [ -x /usr/bin/dracut ]; then
    /usr/bin/dracut --force /boot/initramfs-${KVER}.img ${KVER}
fi
if [ -x /usr/sbin/grubby ]; then
    /usr/sbin/grubby --add-kernel=/boot/vmlinuz-${KVER} --title="CachyOS RT BORE Zen4" --initrd=/boot/initramfs-${KVER}.img
fi

%preun
KVER=$(ls /usr/lib/modules/ | grep "cachyos-zen4" | head -n 1)
if [ -x /usr/sbin/grubby ]; then
    /usr/sbin/grubby --remove-kernel=/boot/vmlinuz-${KVER}
fi

%files
/boot/vmlinuz-*
/boot/System.map-*
/boot/config-*
/usr/lib/modules/*
