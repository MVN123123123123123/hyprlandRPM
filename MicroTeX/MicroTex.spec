Name:           microtex
Version:        0
Release:        1.1
Summary:        A dynamic, cross-platform, and embeddable LaTeX rendering library

# The core project is MIT, but resources/fonts are under different licenses.
License:        MIT and others
URL:            https://github.com/NanoMichael/MicroTeX
Source0:        https://github.com/NanoMichael/MicroTeX

BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  gtkmm4.0
BuildRequires:  gtksourceview5
%description
It is a dynamic, cross-platform, and embeddable LaTeX rendering library. Its main purpose is to display mathematical formulas written in LaTeX. It can be embedded in applications on various platforms.

%prep
%autosetup

%build
# Disabling HAVE_LOG and GRAPHICS_DEBUG for a cleaner release build
%cmake -DHAVE_LOG=OFF -DGRAPHICS_DEBUG=OFF
%cmake_build

%install
%cmake_install

%files
%license LICENSE
%doc README.md
%{_bindir}/LaTeX
# Note: Add %{_libdir}/*.so and %{_includedir}/* if the CMake install target exports the library/headers.
