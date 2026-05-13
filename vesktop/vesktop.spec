Name:           vesktop
Version:        1.6.5
Release:        1%{?dist}
Summary:        Vesktop is a custom Discord desktop app

License:        GPL-3.0-or-later
URL:            https://vencord.dev/

%ifarch aarch64
%define tarball_name vesktop-%{version}-arm64.tar.gz
%else
%define tarball_name vesktop-%{version}.tar.gz
%endif

Source0:        https://github.com/Vencord/Vesktop/releases/download/v%{version}/%{tarball_name}
Source1:        https://raw.githubusercontent.com/Vencord/Vesktop/v%{version}/build/icon.svg

ExclusiveArch:  x86_64 aarch64

BuildRequires:  tar
Requires:       libappindicator-gtk3
Requires:       libnotify
Requires:       nss
Requires:       libdrm
Requires:       libxcb
Requires:       libXcomposite

# Prevent rpmbuild from stripping binaries and modifying the prebuilt electron apps
%global __os_install_post %{nil}
%global debug_package %{nil}
%define _build_id_links none

%description
Vesktop is a custom Discord desktop app.
This package repackages the pre-compiled tar.gz release from GitHub to integrate better with system package managers and updates.

%prep
%setup -c -T
tar xf %{SOURCE0} --strip-components=1

%build
# Pre-compiled binaries, no build steps required

%install
rm -rf $RPM_BUILD_ROOT

# Create directories
mkdir -p $RPM_BUILD_ROOT/opt/vesktop
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/applications
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/icons/hicolor/scalable/apps

# Copy all files
cp -a * $RPM_BUILD_ROOT/opt/vesktop/

# Fix permissions on chrome-sandbox (required for electron apps to run with proper sandbox)
chmod 4755 $RPM_BUILD_ROOT/opt/vesktop/chrome-sandbox || true

# Create symlink
ln -sf /opt/vesktop/vesktop $RPM_BUILD_ROOT/%{_bindir}/vesktop

# Desktop file
cat <<EOF > $RPM_BUILD_ROOT/%{_datadir}/applications/vesktop.desktop
[Desktop Entry]
Name=Vesktop
GenericName=Internet Messenger
Comment=Vesktop is a custom Discord desktop app
Type=Application
Categories=Network;InstantMessaging;Chat;
Keywords=discord;vencord;electron;chat;
MimeType=x-scheme-handler/discord;
StartupWMClass=vesktop
Exec=/opt/vesktop/vesktop %U
Icon=vesktop
EOF

# Install icon
install -m 644 %{SOURCE1} $RPM_BUILD_ROOT/%{_datadir}/icons/hicolor/scalable/apps/vesktop.svg

%files
/opt/vesktop
%{_bindir}/vesktop
%{_datadir}/applications/vesktop.desktop
%{_datadir}/icons/hicolor/scalable/apps/vesktop.svg

%changelog
%autochangelog
