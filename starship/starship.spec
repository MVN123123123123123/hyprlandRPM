%global debug_package %{nil}
%undefine _package_note_file
%global commit 3df5dd254e930f4828e31c035626f6565cb1158c
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name: starship
Version: 1.24.2
Release: 1%{?dist}.%{shortcommit}
Summary: The minimal, blazing-fast, and infinitely customizable prompt for any shell!

License: ISC
URL: https://github.com/starship/starship
Source: %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires: cargo >= 1.90
BuildRequires: cmake3
BuildRequires: gcc
BuildRequires: rust >= 1.90

BuildRequires: pkgconfig(openssl)
BuildRequires: pkgconfig(zlib)

%description
%{summary}.


%prep
%autosetup


%install
export CARGO_PROFILE_RELEASE_BUILD_OVERRIDE_OPT_LEVEL=3
export CMAKE=cmake3
RUSTFLAGS='-C strip=symbols' cargo install --root=%{buildroot}%{_prefix} --path=.
rm -f %{buildroot}%{_prefix}/.crates.toml \
    %{buildroot}%{_prefix}/.crates2.json


%files
%license LICENSE
%doc README.md CONTRIBUTING.md
%{_bindir}/%{name}
%changelog
%autochangelog