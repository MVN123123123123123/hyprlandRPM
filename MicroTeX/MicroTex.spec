Name:           microtex
Version:        0
Release:        1.1
Summary:        A dynamic, cross-platform, and embeddable LaTeX rendering library

# The core project is MIT, but resources/fonts are under different licenses.
License:        MIT and others
URL:            https://github.com/NanoMichael/MicroTeX
# Points directly to a downloadable tarball of the master branch
Source0:        https://github.com/NanoMichael/MicroTeX/archive/refs/heads/master.tar.gz#/%{name}-%{version}.tar.gz

BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  gtkmm4.0
BuildRequires:  gtksourceview5

%description
It is a dynamic, cross-platform, and embeddable LaTeX rendering library.
Its main purpose is to display mathematical formulas written in LaTeX. It can be embedded in applications on various platforms.

%prep
# Since GitHub's master tarball extracts to "MicroTeX-master", we must specify the directory name
%autosetup -n MicroTeX-master

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
# Note: Add %%{_libdir}/*.so and %%{_includedir}/* if the CMake install target exports the library/headers.

%changelog
* Sat Mar 21 2026 Your Name <your.email@example.com> - 0-1.1
- Fixed Source0 URL to point to a valid tar archive
- Escaped macros in comments
- Added initial changelog section