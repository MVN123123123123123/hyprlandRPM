# Odysseus — self-hosted AI workspace
# https://github.com/pewdiepie-archdaemon/odysseus
#
# This is a web application (FastAPI + uvicorn), not a traditional Python
# library.  It has no pyproject-based packaging, so we bundle it to /opt
# with a self-contained virtualenv and a systemd service.

%global         commit          41a928f21bb2907f696dcbb6173b72b62c5a3ae2
%global         shortcommit     %(c=%{commit}; echo ${c:0:7})
%global         date            20260603

%global         appdir          %{_prefix}/lib/odysseus

Name:           odysseus
Version:        1.0.0^%{date}git%{shortcommit}
Release:        3%{?dist}
Summary:        Self-hosted AI workspace

License:        MIT
URL:            https://github.com/pewdiepie-archdaemon/odysseus
Source0:        %{url}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
BuildRequires:  python3-pip
BuildRequires:  systemd-rpm-macros

Requires:       python3 >= 3.11
Requires:       python3-pip
Requires:       tmux
Requires(pre):  shadow-utils

%description
A self-hosted AI workspace — the self-hosted version of the UI experience
you get from ChatGPT and Claude. Running on your own hardware, with your
own data — local-first, privacy-first.

Features include chat with any local model or API, an autonomous agent
with MCP and tool support, a hardware-aware model Cookbook, deep research
reports, model comparison, a document editor, persistent memory and skills,
email triage, notes and tasks, and a CalDAV-syncing calendar.

%prep
%autosetup -n %{name}-%{commit} -p1

%build
# Nothing to compile — pure Python web application

%install
# -- application tree ---------------------------------------------------
install -d %{buildroot}%{appdir}

# Copy the application source
cp -a app.py setup.py requirements.txt requirements-optional.txt \
      .env.example \
      %{buildroot}%{appdir}/

for d in core companion config docker docs licenses mcp_servers \
         routes scripts services src static tests; do
    [ -d "$d" ] && cp -a "$d" %{buildroot}%{appdir}/
done

# -- writable data dir (StateDirectory managed by systemd) --------------
install -d %{buildroot}%{_sharedstatedir}/odysseus

# -- config --------------------------------------------------------------
install -d %{buildroot}%{_sysconfdir}/odysseus
install -Dpm0644 .env.example %{buildroot}%{_sysconfdir}/odysseus/env
# Symlink so the app picks up .env from its working directory
ln -sf %{_sysconfdir}/odysseus/env %{buildroot}%{appdir}/.env

# -- CLI wrapper ---------------------------------------------------------
install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/odysseus << 'WRAPPER'
#!/usr/bin/bash
PORT=${ODYSSEUS_PORT:-7000}
HOST=${ODYSSEUS_HOST:-127.0.0.1}
URL="http://${HOST}:${PORT}"

usage() {
    echo "Usage: odysseus [start|stop|restart|status|log]"
    echo
    echo "  start    Start Odysseus (opens browser)"
    echo "  stop     Stop Odysseus"
    echo "  restart  Restart Odysseus"
    echo "  status   Show service status"
    echo "  log      Follow the live log"
    echo
    echo "  Running without arguments starts the service."
}

case "${1:-start}" in
    start)
        sudo systemctl start odysseus.service
        echo "Odysseus starting at ${URL}"
        # Give uvicorn a moment to bind
        sleep 2
        xdg-open "${URL}" 2>/dev/null || echo "Open ${URL} in your browser."
        ;;
    stop)
        sudo systemctl stop odysseus.service
        echo "Odysseus stopped."
        ;;
    restart)
        sudo systemctl restart odysseus.service
        echo "Odysseus restarted at ${URL}"
        ;;
    status)
        systemctl status odysseus.service
        ;;
    log|logs)
        journalctl -u odysseus.service -f
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        echo "Unknown command: $1"
        usage
        exit 1
        ;;
esac
WRAPPER
chmod 755 %{buildroot}%{_bindir}/odysseus

# -- systemd service ----------------------------------------------------
install -d %{buildroot}%{_unitdir}
cat > %{buildroot}%{_unitdir}/odysseus.service << 'EOF'
[Unit]
Description=Odysseus — self-hosted AI workspace
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=odysseus
Group=odysseus
WorkingDirectory=%{appdir}

# Run first-time setup (skips if already done, non-interactive)
ExecStartPre=%{_sharedstatedir}/odysseus/venv/bin/python %{appdir}/setup.py

ExecStart=%{_sharedstatedir}/odysseus/venv/bin/python -m uvicorn app:app \
    --host 127.0.0.1 --port 7000

Restart=on-failure
RestartSec=5

ReadWritePaths=%{_sharedstatedir}/odysseus %{appdir}
EnvironmentFile=-%{_sysconfdir}/odysseus/env

# Data lives under /var/lib/odysseus
Environment=HOME=%{_sharedstatedir}/odysseus
Environment=DATABASE_URL=sqlite:///%{_sharedstatedir}/odysseus/data/app.db
Environment=ODYSSEUS_SKIP_ADMIN_PROMPT=1

[Install]
WantedBy=multi-user.target
EOF

# -- sysusers.d ----------------------------------------------------------
install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/odysseus.conf << 'EOF'
u odysseus - "Odysseus AI Workspace" %{_sharedstatedir}/odysseus -
EOF

# -- tmpfiles.d (ensure data dir ownership) ------------------------------
install -d %{buildroot}%{_tmpfilesdir}
cat > %{buildroot}%{_tmpfilesdir}/odysseus.conf << 'EOF'
d %{_sharedstatedir}/odysseus 0750 odysseus odysseus -
d %{_sharedstatedir}/odysseus/data 0750 odysseus odysseus -
d %{_sharedstatedir}/odysseus/logs 0750 odysseus odysseus -
d %{_sharedstatedir}/odysseus/venv 0750 odysseus odysseus -
EOF

%pre
%sysusers_create_compat %{_sysusersdir}/odysseus.conf

%post
%systemd_post odysseus.service
%tmpfiles_create %{_tmpfilesdir}/odysseus.conf

# Symlink the writable data dir into the app tree so the app finds it
ln -sf %{_sharedstatedir}/odysseus/data %{appdir}/data 2>/dev/null || :
ln -sf %{_sharedstatedir}/odysseus/logs %{appdir}/logs 2>/dev/null || :

# Create virtualenv and install Python deps (one-time, on first install)
if [ ! -f %{_sharedstatedir}/odysseus/venv/bin/python ]; then
    python3 -m venv %{_sharedstatedir}/odysseus/venv
    %{_sharedstatedir}/odysseus/venv/bin/pip install --no-cache-dir \
        -r %{appdir}/requirements.txt
fi
# Ensure the odysseus user owns and can execute everything in the venv
chown -R odysseus:odysseus %{_sharedstatedir}/odysseus
chmod -R u+rwX,g+rX,o+rX %{_sharedstatedir}/odysseus/venv

%preun
%systemd_preun odysseus.service

%postun
%systemd_postun_with_restart odysseus.service

%files
%license LICENSE
%doc README.md CONTRIBUTING.md ROADMAP.md SECURITY.md THREAT_MODEL.md ACKNOWLEDGMENTS.md

# CLI wrapper
%{_bindir}/odysseus

# Application
%{appdir}/

# Config
%dir %{_sysconfdir}/odysseus
%config(noreplace) %{_sysconfdir}/odysseus/env

# Systemd
%{_unitdir}/odysseus.service
%{_sysusersdir}/odysseus.conf
%{_tmpfilesdir}/odysseus.conf

# State directory
%dir %attr(0750,odysseus,odysseus) %{_sharedstatedir}/odysseus

%changelog
%autochangelog
