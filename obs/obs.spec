%ifarch %{power64} s390x riscv64
# LuaJIT is not available for POWER, IBM Z, and RISC-V
%bcond lua_scripting 0
%else
%bcond lua_scripting 1
%endif

%ifarch x86_64
# VPL/QSV is only available on x86_64
%bcond vpl 1
%else
%bcond vpl 0
%endif

# x264 is not in Fedora
%bcond x264 0

%if "%{__isa_bits}" == "64"
%global lib64_suffix ()(64bit)
%endif
%global libvlc_soversion 5

%global obswebsocket_version 5.7.3

Name:           obs-studio
Version:        32.1.2
Release:        1%{?dist}
Summary:        Open Broadcaster Software Studio

License:        GPL-2.0-or-later AND MIT AND BSD-2-Clause AND BSD-3-Clause AND BSL-1.0 AND LGPL-2.1-or-later AND CC0-1.0 AND (CC0-1.0 OR OpenSSL OR Apache-2.0) AND LicenseRef-Fedora-Public-Domain AND (BSD-3-Clause OR GPL-2.0-only)
URL:            https://obsproject.com/
Source0:        https://github.com/obsproject/obs-studio/archive/%{version}/%{name}-%{version}.tar.gz
Source1:        https://github.com/obsproject/obs-websocket/archive/%{obswebsocket_version}/obs-websocket-%{obswebsocket_version}.tar.gz

ExcludeArch:    %{ix86}

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  cmake >= 3.28
BuildRequires:  ninja-build
BuildRequires:  extra-cmake-modules
BuildRequires:  libappstream-glib
BuildRequires:  desktop-file-utils

BuildRequires:  alsa-lib-devel
BuildRequires:  asio-devel
BuildRequires:  fdk-aac-free-devel
BuildRequires:  ffmpeg-free-devel
BuildRequires:  fontconfig-devel
BuildRequires:  freetype-devel
BuildRequires:  jansson-devel >= 2.5
BuildRequires:  json-devel
BuildRequires:  libcurl-devel
BuildRequires:  libdatachannel-devel >= 0.20
BuildRequires:  libdrm-devel
BuildRequires:  libGL-devel
BuildRequires:  libglvnd-devel
BuildRequires:  librist-devel
BuildRequires:  srt-devel
BuildRequires:  libuuid-devel
BuildRequires:  libv4l-devel
BuildRequires:  libva-devel
BuildRequires:  libX11-devel
BuildRequires:  libxcb-devel
BuildRequires:  libXcomposite-devel
BuildRequires:  libXinerama-devel
BuildRequires:  libxkbcommon-devel
%if %{with lua_scripting}
BuildRequires:  luajit-devel
%endif
BuildRequires:  mbedtls-devel
BuildRequires:  nv-codec-headers
%if %{with vpl}
BuildRequires:  libvpl-devel
%endif
BuildRequires:  pciutils-devel
BuildRequires:  pipewire-devel
BuildRequires:  pipewire-jack-audio-connection-kit-devel
BuildRequires:  pulseaudio-libs-devel
BuildRequires:  python3-devel
BuildRequires:  libqrcodegencpp-devel
BuildRequires:  qt6-qtbase-devel
BuildRequires:  qt6-qtbase-private-devel
BuildRequires:  qt6-qtsvg-devel
BuildRequires:  qt6-qtwayland-devel
BuildRequires:  rnnoise-devel
BuildRequires:  simde-devel
BuildRequires:  speexdsp-devel
BuildRequires:  swig
BuildRequires:  systemd-devel
BuildRequires:  uthash-devel
BuildRequires:  wayland-devel
BuildRequires:  websocketpp-devel
%if %{with x264}
BuildRequires:  x264-devel
%endif

Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Requires:       /usr/bin/ffmpeg
Recommends:     openh264%{?_isa}

# Ensure QtWayland is installed when libwayland-client is installed
Requires:       (qt6-qtwayland%{?_isa} if libwayland-client%{?_isa})

# For icon folder hierarchy
Requires:       hicolor-icon-theme

## License: BSL-1.0
Provides:       bundled(decklink-sdk)

## License: CC0-1.0 or OpenSSL or Apache-2.0
Provides:       bundled(blake2)

## License: MIT
Provides:       bundled(json11)

## License: MIT
Provides:       bundled(libcaption)

## License: BSD-3-Clause
Provides:       bundled(rnnoise)

## License: LGPL-2.1-or-later and LicenseRef-Fedora-Public-Domain
Provides:       bundled(librtmp)

## License: MIT
Provides:       bundled(libnsgif)

## Cf. https://github.com/obsproject/obs-studio/pull/8327
Provides:       bundled(intel-mediasdk)

##obs hates this
Conflicts:      obs-studio-plugin-pwvideo

%description
Open Broadcaster Software is free and open source
software for video recording and live streaming.

# --------------------------------------------------------------------------
%package libs
Summary:        Open Broadcaster Software Studio libraries

%description libs
Library files for Open Broadcaster Software.

# --------------------------------------------------------------------------
%package devel
Summary:        Open Broadcaster Software Studio header files
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}
Requires:       simde-devel

%description devel
Header files for Open Broadcaster Software.

# --------------------------------------------------------------------------
%package plugin-vlc-video
Summary:        Open Broadcaster Software Studio - VLC-based video plugin
BuildRequires:  vlc-devel

# We dlopen() libvlc
Requires:       libvlc.so.%{libvlc_soversion}%{?lib64_suffix}
Requires:       obs-studio%{?_isa} = %{version}-%{release}
Supplements:    obs-studio%{?_isa}

%description plugin-vlc-video
Open Broadcaster Software is free and open source software
for video recording and live streaming.

This package contains the plugin for using VLC to embed video
as an overlay in a video stream or recording.


# --------------------------------------------------------------------------
%prep
%setup -q -n obs-studio-%{version}

# Prepare plugins/obs-websocket
tar -xf %{SOURCE1} -C plugins/obs-websocket --strip-components=1

# Disable obs-browser plugin since ENABLE_BROWSER is OFF
mkdir -p plugins/obs-browser
touch plugins/obs-browser/CMakeLists.txt

%if ! %{with x264}
# disable x264 plugin
mv plugins/obs-x264/CMakeLists.txt plugins/obs-x264/CMakeLists.txt.disabled
touch plugins/obs-x264/CMakeLists.txt
%endif

%if ! %{with vpl}
# disable unusable qsv plugin
mv plugins/obs-qsv11/CMakeLists.txt plugins/obs-qsv11/CMakeLists.txt.disabled
touch plugins/obs-qsv11/CMakeLists.txt
%endif

# Removing unused third-party deps
rm -rf deps/w32-pthreads
rm -rf deps/ipc-util
rm -rf deps/jansson

# Remove unneeded EGL/KHR files
rm -rf deps/glad/include/{EGL,KHR}
sed -e 's|include/EGL/eglplatform.h||g' -i deps/glad/CMakeLists.txt

# Collect license files
mkdir -p .fedora-rpm/licenses/deps
mkdir -p .fedora-rpm/licenses/plugins
cp plugins/obs-filters/rnnoise/COPYING .fedora-rpm/licenses/deps/rnnoise-COPYING
cp plugins/obs-websocket/LICENSE .fedora-rpm/licenses/plugins/obs-websocket-LICENSE
cp plugins/obs-outputs/librtmp/COPYING .fedora-rpm/licenses/deps/librtmp-COPYING
cp deps/json11/LICENSE.txt .fedora-rpm/licenses/deps/json11-LICENSE.txt
cp deps/libcaption/LICENSE.txt .fedora-rpm/licenses/deps/libcaption-LICENSE.txt
cp plugins/obs-qsv11/QSV11-License-Clarification-Email.txt .fedora-rpm/licenses/plugins/QSV11-License-Clarification-Email.txt || true
cp deps/blake2/LICENSE.blake2 .fedora-rpm/licenses/deps/ || true
cp libobs/graphics/libnsgif/LICENSE.libnsgif .fedora-rpm/licenses/deps/ || true
cp plugins/decklink/LICENSE.decklink-sdk .fedora-rpm/licenses/deps || true
cp plugins/obs-qsv11/obs-qsv11-LICENSE.txt .fedora-rpm/licenses/plugins/ || true


%conf

%cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo \
       -DOBS_VERSION_OVERRIDE=%{version} \
       -DCMAKE_COMPILE_WARNING_AS_ERROR=OFF \
       -DUNIX_STRUCTURE=1 -GNinja \
       -DENABLE_BROWSER=OFF \
       -DENABLE_JACK=ON \
       -DENABLE_LIBFDK=ON \
       -DENABLE_AJA=OFF \
       -DENABLE_WEBRTC=ON \
%if ! %{with lua_scripting}
       -DENABLE_SCRIPTING_LUA=OFF \
%endif
       -DOpenGL_GL_PREFERENCE=GLVND


%build
%cmake_build


%install
%cmake_install

# Fix libobs.pc Cflags
sed -e 's|^Cflags: .*|Cflags: -I${includedir} -DHAVE_OBSCONFIG_H|' -i %{buildroot}%{_libdir}/pkgconfig/libobs.pc

# Create libexecdir for obs-plugins
mkdir -p %{buildroot}%{_libexecdir}/obs-plugins

find %{buildroot} -name ".keepme" -delete
find %{buildroot} -name ".gitkeep" -delete


%check
desktop-file-validate %{buildroot}/%{_datadir}/applications/com.obsproject.Studio.desktop
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/metainfo/*.metainfo.xml


%files
%doc README.rst
%license COPYING
%{_bindir}/obs
%{_bindir}/obs-ffmpeg-mux
%ifarch %{x86_64}
%{_bindir}/obs-nvenc-test
%endif
%{_datadir}/metainfo/com.obsproject.Studio.metainfo.xml
%{_datadir}/applications/com.obsproject.Studio.desktop
%{_datadir}/icons/hicolor/*/apps/com.obsproject.Studio.*
%{_datadir}/obs/
%exclude %{_datadir}/obs/obs-plugins/vlc-video/

%files libs
%license COPYING
%license .fedora-rpm/licenses/*
%dir %{_libexecdir}/obs-plugins
%{_libdir}/obs-plugins/
%exclude %{_libdir}/obs-plugins/vlc-video.so
%{_libdir}/obs-scripting/
# unversioned so files packaged for third-party plugins
%{_libdir}/*.so
%{_libdir}/*.so.*

%files devel
%{_libdir}/cmake/libobs/
%{_libdir}/cmake/obs-frontend-api/
%{_libdir}/cmake/obs-websocket-api/
%{_libdir}/pkgconfig/libobs.pc
%{_libdir}/pkgconfig/obs-frontend-api.pc
%{_includedir}/obs/

%files plugin-vlc-video
%{_libdir}/obs-plugins/vlc-video.so
%{_datadir}/obs/obs-plugins/vlc-video/


%changelog
%autochangelog
