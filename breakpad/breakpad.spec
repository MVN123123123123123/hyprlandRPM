%global commit 8be0e3114685fcc1589561067282edf75ea1259a
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global lss_commit 29f7c7e018f4ce706a709f0b0afbf8bacf869480
%global lss_shortcommit %(c=%{lss_commit}; echo ${c:0:7})

Name:           breakpad
Version:        0.1^20240404git%{shortcommit}
Release:        1%{?dist}
Summary:        An open-source multi-platform crash reporting system

License:        BSD
URL:            https://github.com/google/breakpad
Source0:        https://github.com/google/breakpad/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:        https://chromium.googlesource.com/linux-syscall-support/+archive/%{lss_commit}.tar.gz #/lss-%{lss_shortcommit}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  libtool
BuildRequires:  git
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(gtest)
BuildRequires:  pkgconfig(gmock)
%description
An open-source multi-platform crash reporting system.
This package contains the client and server application tools.

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
The %{name}-devel package contains libraries and header files for
developing applications that use %{name}.

%package static
Summary:        Static libraries for %{name}
Requires:       %{name}-devel%{?_isa} = %{version}-%{release}

%description static
The %{name}-static package contains static libraries for %{name}.

%prep
%autosetup -n %{name}-%{commit}

# Extract Linux Syscall Support (LSS), which is a required submodule
mkdir -p src/third_party/lss
tar -xf %{SOURCE1} -C src/third_party/lss

%build
autoreconf -vfi
%configure \
    --disable-dependency-tracking \
    --enable-m32=no

%make_build

%install
%make_install

# Clean up libtool archives
find %{buildroot} -name '*.la' -delete

%files
%license LICENSE
%doc README.md
%{_bindir}/*

%files devel
%{_includedir}/%{name}/
%{_libdir}/pkgconfig/*.pc

%files static
%{_libdir}/*.a
