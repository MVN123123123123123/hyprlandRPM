# Odysseus — self-hosted AI workspace
# https://github.com/pewdiepie-archdaemon/odysseus
#
# This is a web application (FastAPI + uvicorn), not a traditional Python
# library.  It has no pyproject-based packaging, so we install it under
# /var/lib/odysseus/app/ (writable by the odysseus user) with a
# self-contained virtualenv and a systemd service.
#
# The app writes cache/, data/, logs/ relative to its own source tree
# using Path(__file__), so the entire app tree must be writable.

%global         commit          563713c2c6a15e7d020997826bd97e71fac25138
%global         shortcommit     %(c=%{commit}; echo ${c:0:7})
%global         date            20260603

%global         odysseus_home   %{_sharedstatedir}/odysseus
%global         appdir          %{odysseus_home}/app

Name:           odysseus
Version:        1.0.0^%{date}git%{shortcommit}
Release:        %{?dist}
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
# -- application tree (under /var/lib/odysseus/app) ----------------------
install -d %{buildroot}%{appdir}

# Copy the application source
cp -a app.py setup.py requirements.txt requirements-optional.txt \
      .env.example \
      %{buildroot}%{appdir}/

for d in core companion config docker docs licenses mcp_servers \
         routes scripts services src static tests; do
    [ -d "$d" ] && cp -a "$d" %{buildroot}%{appdir}/
done

# -- config --------------------------------------------------------------
install -d %{buildroot}%{_sysconfdir}/odysseus
install -Dpm0644 .env.example %{buildroot}%{_sysconfdir}/odysseus/env
# Symlink so the app picks up .env from its working directory
ln -sf %{_sysconfdir}/odysseus/env %{buildroot}%{appdir}/.env

# -- CLI wrapper ---------------------------------------------------------
install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/odysseus << 'WRAPPER'
#!/usr/bin/bash
if [ -f /etc/odysseus/env ]; then
    # Source the env file but filter out comments
    eval "$(grep -v '^#' /etc/odysseus/env | xargs -d '\n')"
fi
PORT=${APP_PORT:-7000}
HOST=${APP_BIND:-0.0.0.0}

if [ "$HOST" = "0.0.0.0" ]; then
    BROWSER_HOST="127.0.0.1"
else
    BROWSER_HOST="$HOST"
fi
URL="http://${BROWSER_HOST}:${PORT}"

usage() {
    echo "Usage: odysseus [start|stop|restart|status|log]"
    echo
    echo "  start    Start Odysseus (opens browser once ready)"
    echo "  stop     Stop Odysseus"
    echo "  restart  Restart Odysseus"
    echo "  status   Show service status"
    echo "  log      Follow the live log"
    echo
    echo "  Running without arguments starts the service."
}

case "${1:-start}" in
    start)
        START_TIME=$(date +"%%Y-%%m-%%d %%H:%%M:%%S")
        sudo systemctl start odysseus.service
        echo -n "Waiting for Odysseus to start (first launch downloads AI models and may take up to a minute)..."
        for i in {1..60}; do
            # Use curl to check if the port is responding
            if curl -s -o /dev/null -I -w "%{http_code}" "$URL" 2>/dev/null | grep -E "200|302|401|403|404|301" >/dev/null; then
                echo " Ready!"
                
                # Retrieve temporary password if created in this run
                PASSWORD_LINE=$( (journalctl -u odysseus.service --since="$START_TIME" --no-pager 2>/dev/null || sudo journalctl -u odysseus.service --since="$START_TIME" --no-pager 2>/dev/null) | grep -o "Temporary password:.*" | head -n 1 )
                if [ -n "$PASSWORD_LINE" ]; then
                    echo ""
                    echo "=========================================================="
                    echo "  Odysseus Initial Admin Credentials"
                    echo "=========================================================="
                    echo "  Username: admin"
                    echo "  ${PASSWORD_LINE}"
                    echo "  (Please change your password immediately after logging in)"
                    echo "=========================================================="
                    echo ""
                fi
                
                xdg-open "${URL}" 2>/dev/null || echo "Open ${URL} in your browser."
                exit 0
            fi
            echo -n "."
            sleep 1
        done
        echo " Timeout waiting for service to bind. Please check logs with: odysseus log"
        ;;
    stop)
        sudo systemctl stop odysseus.service
        echo "Odysseus stopped."
        ;;
    restart)
        sudo systemctl restart odysseus.service
        echo "Odysseus restarted."
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
ExecStartPre=%{odysseus_home}/venv/bin/python %{appdir}/setup.py

ExecStart=%{odysseus_home}/venv/bin/python -m uvicorn app:app \
    --host ${APP_BIND} --port ${APP_PORT}

Restart=on-failure
RestartSec=5

ReadWritePaths=%{odysseus_home}
EnvironmentFile=-%{_sysconfdir}/odysseus/env

# Defaults
Environment=APP_BIND=0.0.0.0
Environment=APP_PORT=7000
Environment=HOME=%{odysseus_home}
Environment=DATABASE_URL=sqlite:///%{odysseus_home}/app/data/app.db
Environment=ODYSSEUS_SKIP_ADMIN_PROMPT=1

[Install]
WantedBy=multi-user.target
EOF

# -- sysusers.d ----------------------------------------------------------
install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/odysseus.conf << 'EOF'
u odysseus - "Odysseus AI Workspace" %{odysseus_home} /bin/bash
EOF

# -- tmpfiles.d (ensure dir ownership) ----------------------------------
install -d %{buildroot}%{_tmpfilesdir}
cat > %{buildroot}%{_tmpfilesdir}/odysseus.conf << 'EOF'
d %{odysseus_home} 0750 odysseus odysseus -
d %{odysseus_home}/venv 0750 odysseus odysseus -
EOF

%pre
%sysusers_create_compat %{_sysusersdir}/odysseus.conf

%post
%systemd_post odysseus.service
%tmpfiles_create %{_tmpfilesdir}/odysseus.conf

# Cookbook spawns tmux sessions that rely on $SHELL being a real shell.
# Ensure the odysseus user has /bin/bash (fixes upgrades from nologin).
usermod -s /bin/bash odysseus 2>/dev/null || true

# The entire app tree must be writable by the odysseus user
chown -R odysseus:odysseus %{odysseus_home}

# Create virtualenv and install Python deps (one-time, on first install)
if [ ! -f %{odysseus_home}/venv/bin/python ]; then
    python3 -m venv %{odysseus_home}/venv
    %{odysseus_home}/venv/bin/pip install --no-cache-dir \
        -r %{appdir}/requirements.txt
    chown -R odysseus:odysseus %{odysseus_home}/venv
fi

%preun
%systemd_preun odysseus.service

%postun
%systemd_postun_with_restart odysseus.service

%files
%license LICENSE
%doc README.md CONTRIBUTING.md ROADMAP.md SECURITY.md THREAT_MODEL.md ACKNOWLEDGMENTS.md

# CLI wrapper
%{_bindir}/odysseus

# Application + state (all under /var/lib/odysseus, owned by odysseus user)
%dir %attr(0750,odysseus,odysseus) %{odysseus_home}
%{appdir}/

# Config
%dir %{_sysconfdir}/odysseus
%config(noreplace) %{_sysconfdir}/odysseus/env

# Systemd
%{_unitdir}/odysseus.service
%{_sysusersdir}/odysseus.conf
%{_tmpfilesdir}/odysseus.conf

%changelog
%autochangelog
