# Pinned commit from:
# https://git.outfoxxed.me/quickshell/quickshell/commits/branch/master
%global commit          7511545ee20664e3b8b8d3322c0ffe7567c56f7a
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

# The upstream project version in CMakeLists.txt at pinned commit
%global upstream_ver    0.1.0

Name:           quickshell-git
Version:        %{upstream_ver}^1.git%{shortcommit}
Release:        1%{?dist}
Summary:        quickshell-git pinned commit and extra deps for illogical-impulse

License:        LGPL-3.0-only
URL:            https://git.outfoxxed.me/quickshell/quickshell
Source0:        %{url}/archive/%{commit}.tar.gz#/quickshell-%{shortcommit}.tar.gz

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch:    %{ix86}

Conflicts:      quickshell

# ─── Build dependencies (from PKGBUILD makedepends) ──────────────────────────
BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  ninja-build
BuildRequires:  git-core
BuildRequires:  cli11-devel
BuildRequires:  spirv-tools-devel
BuildRequires:  vulkan-headers
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols)
BuildRequires:  qt6-qtshadertools-devel

# ─── Build dependencies (from PKGBUILD depends, needed at build time) ────────
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libpipewire-0.3)
BuildRequires:  pkgconfig(xcb)
BuildRequires:  mesa-libEGL-devel
BuildRequires:  cpptrace-devel
BuildRequires:  libzstd-devel
BuildRequires:  jemalloc-devel
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qtdeclarative-devel
BuildRequires:  qt6-qtsvg-devel
BuildRequires:  qt6-qtwayland-devel
BuildRequires:  qt6-qtbase-private-devel
BuildRequires:  qt6-qtdeclarative-private-devel
BuildRequires:  libunwind-devel

# ─── Runtime dependencies (from PKGBUILD depends) ────────────────────────────
Requires:       cpptrace%{?_isa}
Requires:       jemalloc%{?_isa}
Requires:       mesa-libEGL%{?_isa}
Requires:       qt6-qtdeclarative%{?_isa}
Requires:       qt6-qtbase%{?_isa}
Requires:       qt6-qtsvg%{?_isa}
Requires:       libdrm%{?_isa}
Requires:       pipewire-libs%{?_isa}
Requires:       libxcb%{?_isa}
Requires:       wayland%{?_isa}

# ─── illogical-impulse custom runtime dependencies ───────────────────────────
Requires:       qt6-qt5compat%{?_isa}
Requires:       qt6-qtimageformats%{?_isa}
Requires:       qt6-qtmultimedia%{?_isa}
Requires:       qt6-qtpositioning%{?_isa}
Requires:       qt6-qtquicktimeline%{?_isa}
Requires:       qt6-qtsensors%{?_isa}
Requires:       qt6-qttools%{?_isa}
Requires:       qt6-qttranslations
Requires:       qt6-qtvirtualkeyboard%{?_isa}
Requires:       qt6-qtwayland%{?_isa}
Requires:       kf6-kirigami%{?_isa}
Requires:       kdialog
Requires:       kf6-syntax-highlighting%{?_isa}

Provides:       quickshell = %{version}-%{release}

%description
Quickshell is a flexible QtQuick-based desktop shell toolkit, pinned to a
specific commit with additional dependencies required by the illogical-impulse
Hyprland rice.

%prep
%autosetup -n quickshell -p1

%build
%cmake -GNinja \
    -DCMAKE_BUILD_TYPE=RelWithDebInfo \
    -DCMAKE_INSTALL_PREFIX=%{_prefix} \
    -DDISTRIBUTOR="COPR (package: quickshell-git)" \
    -DDISTRIBUTOR_DEBUGINFO_AVAILABLE=NO \
    -DINSTALL_QML_PREFIX=%{_lib}/qt6/qml

%cmake_build

%install
%cmake_install

# CMake install script creates a symlink quickshell -> qs; ensure it is present
ln -sf quickshell %{buildroot}%{_bindir}/qs

%files
%license LICENSE
%{_bindir}/quickshell
%{_bindir}/qs
%{_libdir}/qt6/qml/Quickshell/
%{_datadir}/applications/org.quickshell.desktop
%{_datadir}/icons/hicolor/scalable/apps/org.quickshell.svg

# ─── libalpm hook emulation ──────────────────────────────────────────────────
# The PKGBUILD ships quickshell-check.hook which runs
#   /usr/bin/quickshell --private-check-compat
# after qt6-base or qt6-wayland are installed/upgraded.
# On RPM we emulate this with %%triggerin.
%triggerin -- qt6-qtbase, qt6-qtwayland
/usr/bin/quickshell --private-check-compat || :

%changelog
%autochangelog
