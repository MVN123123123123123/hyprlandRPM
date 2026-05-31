Name:           aquamarine
Version:        0.12.0
Release:        202605310900%{?dist}
Summary:        A very light linux rendering backend library
License:        BSD-3-Clause
URL:            https://github.com/hyprwm/aquamarine
Source:         %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch:    %{ix86}

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  mesa-libEGL-devel
BuildRequires:  pkgconfig(gbm)
BuildRequires:  pkgconfig(hwdata)
BuildRequires:  pkgconfig(hyprutils)
BuildRequires:  pkgconfig(hyprwayland-scanner)
BuildRequires:  pkgconfig(libdisplay-info)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libinput)
BuildRequires:  pkgconfig(libseat)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols)

%description
%{summary}.

%package        devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{version}-%{release}
%description    devel
Development files for %{name}.

%prep
%autosetup -p1

%build
%cmake -DCMAKE_BUILD_TYPE=Release
%cmake_build

%install
%cmake_install

# Calculate SO versions from the minor component of Version (X.MINOR.Z)
# The library ships two SO symlinks: .MINOR and .(MINOR-1)
%{lua:
  local ver = rpm.expand("%{version}")
  local minor = tonumber(ver:match("^%d+%.(%d+)%."))
  rpm.define("so_major " .. minor)
  rpm.define("so_lower " .. (minor - 1))
}

%files
%license LICENSE
%doc README.md
%{_libdir}/lib%{name}.so.%{so_major}
%{_libdir}/lib%{name}.so.%{so_lower}

%files devel
%{_includedir}/%{name}/
%{_libdir}/lib%{name}.so
%{_libdir}/pkgconfig/%{name}.pc

%changelog
%autochangelog
