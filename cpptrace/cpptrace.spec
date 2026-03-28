
Name:           cpptrace
Version:        1.0.4
Release:        %autorelease
Summary:        Cpptrace is a simple and portable C++ stacktrace library 

License:        MIT
URL:            https://boutproject.github.io/
Source0:        https://github.com/jeremy-rifkin/cpptrace/archive/refs/tags/v%{version}.tar.gz

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch: %{ix86}

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  libdwarf-devel
BuildRequires:  libcxxabi-devel
BuildRequires:  libzstd-devel

%description
Cpptrace is a simple and portable C++ stacktrace library supporting
C++11 and greater on Linux, macOS, and Windows including MinGW and
Cygwin environments. The goal: Make stack traces simple for once.

In addition to providing access to stack traces, cpptrace also
provides a mechanism for getting stacktraces from thrown exceptions
which is immensely valuable for debugging and triaging.

%package devel
Summary: Development files for cpptrace

%description devel
Development files for cpptrace

%prep
%autosetup -C -p1

%build

%cmake \
    -DCPPTRACE_DEMANGLE_WITH_CXXABI=ON \
    -DCPPTRACE_USE_EXTERNAL_ZSTD=ON \
    -DCPPTRACE_USE_EXTERNAL_LIBDWARF=ON \
    -DCPPTRACE_FIND_LIBDWARF_WITH_PKGCONFIG=ON \
    -DBUILD_TESTING=OFF \
    -DBUILD_SHARED_LIBS=ON

%cmake_build

%install

%cmake_install

%check

%files
%{_libdir}/libcpptrace.so.1.0.4
%license LICENSE

%files devel
%{_libdir}/libcpptrace.so
%{_libdir}/libcpptrace.so.1
%{_libdir}/cmake/cpptrace
%{_includedir}/ctrace
%{_includedir}/cpptrace
%license LICENSE

%changelog
%autochangelog
