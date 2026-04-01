Name:           bibata-cursor-theme
Version:        2.0.7
Release:        1%{?dist}
Summary:        Material Based Cursor Theme

License:        GPL-3.0-or-later
URL:            https://github.com/ful1e5/Bibata_Cursor
Source0:        %{url}/archive/v%{version}/Bibata_Cursor-%{version}.tar.gz
Source1:        %{url}/releases/download/v%{version}/bitmaps.zip

BuildArch:      noarch

BuildRequires:  python3 >= 3.14
BuildRequires:  python3-pip
BuildRequires:  bsdtar

%description
Material Based Cursor Theme. 
%prep

%autosetup -n Bibata_Cursor-%{version}
bsdtar xvf %{SOURCE1}
rm -rf themes bin

%build
_version="v%{version}"

_get_config_path() {
  local key="${1}"
  local cfg_path="configs"

  if [[ $key == *"Right"* ]]; then
    cfg_path="${cfg_path}/right"
  else
    cfg_path="${cfg_path}/normal"
  fi

  echo $cfg_path
}

_with_version() {
  local comment="${1}"
  echo "$comment ($_version)."
}

declare -A names
names["Bibata-Modern-Amber"]=$(_with_version "Yellowish and rounded edge Bibata")
names["Bibata-Modern-Amber-Right"]=$(_with_version "Yellowish and rounded edge right-hand Bibata")
names["Bibata-Modern-Classic"]=$(_with_version "Black and rounded edge Bibata")
names["Bibata-Modern-Classic-Right"]=$(_with_version "Black and rounded edge right-hand Bibata")
names["Bibata-Modern-Ice"]=$(_with_version "White and rounded edge Bibata")
names["Bibata-Modern-Ice-Right"]=$(_with_version "White and rounded edge right-hand Bibata")
names["Bibata-Original-Amber"]=$(_with_version "Yellowish and sharp edge Bibata")
names["Bibata-Original-Amber-Right"]=$(_with_version "Yellowish and sharp edge right-hand Bibata")
names["Bibata-Original-Classic"]=$(_with_version "Black and sharp edge Bibata")
names["Bibata-Original-Classic-Right"]=$(_with_version "Black and sharp edge right-hand Bibata")
names["Bibata-Original-Ice"]=$(_with_version "White and sharp edge Bibata")
names["Bibata-Original-Ice-Right"]=$(_with_version "White and sharp edge right-hand Bibata")

for key in "${!names[@]}"; do
  comment="${names[$key]}"
  cfg_path=$(_get_config_path "$key")
  ctgen "$cfg_path/x.build.toml" -p x11 -d "bitmaps/$key" -n "$key" -c "$comment XCursors"
done

%install
install -d %{buildroot}%{_datadir}/icons
cp -r themes/Bibata-* %{buildroot}%{_datadir}/icons/

%files
%license LICENSE
%{_datadir}/icons/Bibata-*/

%changelog
%autochangelog
