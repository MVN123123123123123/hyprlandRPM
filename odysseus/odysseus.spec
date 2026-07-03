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

%global         commit          8c943226f8159811fb2a0592a5475dd14c67c1e1
%global         shortcommit     %(c=%{commit}; echo ${c:0:7})

%global         odysseus_home   %{_sharedstatedir}/odysseus
%global         appdir          %{odysseus_home}/app

Name:           odysseus
Version:        1.1.4^git%{shortcommit}
Release:        202607030252%{?dist}
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
Requires:       acl
Requires(pre):  shadow-utils
# Pre-compiled system packages to avoid compilation on newer Python versions
Requires:       python3-lxml
Requires:       python3-cryptography
Requires:       python3-bcrypt
Requires:       python3-numpy

%description
pewdipie fav opensource ai workspace.
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

# Symlinks for persistent runtime directories
ln -sf ../data %{buildroot}%{appdir}/data
ln -sf ../logs %{buildroot}%{appdir}/logs
ln -sf ../cache %{buildroot}%{appdir}/cache

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
    echo "Usage: odysseus [start|stop|restart|status|log|reset-password|setup-workspace|remove-workspace|clear-data]"
    echo
    echo "  start                       Start Odysseus (opens browser once ready)"
    echo "  stop                        Stop Odysseus"
    echo "  restart                     Restart Odysseus"
    echo "  status                      Show service status"
    echo "  log                         Follow the live log"
    echo "  reset-password              Reset the admin password"
    echo "  setup-workspace <path>      Grant the AI model read+write access to a directory"
    echo "  remove-workspace <path>     Revoke AI model access from a directory"
    echo "  clear-data                  Delete all downloaded models, cache, and uploads"
    echo
    echo "  On first start, you will be prompted to set an admin password."
    echo "  Running without arguments starts the service."
}

case "${1:-start}" in
    start)
        # -- First-run password setup ----------------------------------------
        # If auth.json doesn't exist yet, this is the very first launch.
        # Give the user the choice to set a permanent admin password now,
        # or let the system auto-generate one.
        #
        # NOTE: /var/lib/odysseus is 0750 odysseus:odysseus, so we must
        # use sudo to check whether auth.json exists.
        AUTH_JSON="/var/lib/odysseus/app/data/auth.json"
        ENV_FILE="/etc/odysseus/env"

        if ! sudo test -f "$AUTH_JSON" && [ -t 0 ]; then
            echo ""
            echo "=========================================================="
            echo "  Odysseus — First-Time Setup"
            echo "=========================================================="
            echo ""
            echo "  No admin account exists yet."
            echo "  Would you like to set a permanent admin password now?"
            echo ""
            read -r -p "  Set password now? [Y/n]: " SET_PW
            SET_PW="${SET_PW:-Y}"

            if [[ "$SET_PW" =~ ^[Yy]$ ]]; then
                while true; do
                    read -r -s -p "  Enter admin password: " ADMIN_PW
                    echo
                    if [ -z "$ADMIN_PW" ]; then
                        echo "  Password cannot be empty. Try again."
                        continue
                    fi
                    read -r -s -p "  Confirm admin password: " ADMIN_PW_CONFIRM
                    echo
                    if [ "$ADMIN_PW" != "$ADMIN_PW_CONFIRM" ]; then
                        echo "  Passwords do not match. Try again."
                        continue
                    fi
                    break
                done

                # Remove stale auth.json so setup.py recreates the admin
                sudo rm -f "$AUTH_JSON"

                # Write credentials to the env file so setup.py picks them up
                sudo sed -i '/^ODYSSEUS_ADMIN_USER=/d; /^ODYSSEUS_ADMIN_PASSWORD=/d' "$ENV_FILE"
                echo "ODYSSEUS_ADMIN_USER=admin" | sudo tee -a "$ENV_FILE" >/dev/null
                echo "ODYSSEUS_ADMIN_PASSWORD=${ADMIN_PW}" | sudo tee -a "$ENV_FILE" >/dev/null
                echo ""
                echo "  Password saved. Your admin credentials:"
                echo "    Username: admin"
                echo "    Password: (the one you just entered)"
                echo ""
                USER_SET_PASSWORD=1
            else
                echo ""
                echo "  OK — a temporary password will be auto-generated."
                echo "  It will be shown here after Odysseus starts."
                echo ""
                USER_SET_PASSWORD=0
            fi
        fi

        # -- Start the service -----------------------------------------------
        START_TIME=$(date +"%%Y-%%m-%%d %%H:%%M:%%S")
        sudo systemctl start odysseus.service
        echo -n "Waiting for Odysseus to start (first launch downloads AI models and may take up to a minute)..."
        for i in {1..60}; do
            # Use curl to check if the port is responding
            if curl -s -o /dev/null -I -w "%{http_code}" "$URL" 2>/dev/null | grep -E "200|302|401|403|404|301" >/dev/null; then
                echo " Ready!"
                
                # Show temporary password only if the user didn't set one
                if [ "${USER_SET_PASSWORD:-0}" != "1" ]; then
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
    reset-password)
        AUTH_JSON="/var/lib/odysseus/app/data/auth.json"
        ENV_FILE="/etc/odysseus/env"
        echo ""
        echo "========================================================="
        echo "  Odysseus — Reset Admin Password"
        echo "========================================================="
        echo ""
        while true; do
            read -r -s -p "  Enter new admin password: " ADMIN_PW
            echo
            if [ -z "$ADMIN_PW" ]; then
                echo "  Password cannot be empty. Try again."
                continue
            fi
            read -r -s -p "  Confirm new admin password: " ADMIN_PW_CONFIRM
            echo
            if [ "$ADMIN_PW" != "$ADMIN_PW_CONFIRM" ]; then
                echo "  Passwords do not match. Try again."
                continue
            fi
            break
        done

        # Remove existing auth.json so setup.py recreates the admin user
        # (always attempt — rm -f handles non-existence gracefully)
        sudo rm -f "$AUTH_JSON"

        # Write new credentials to env file
        sudo sed -i '/^ODYSSEUS_ADMIN_USER=/d; /^ODYSSEUS_ADMIN_PASSWORD=/d' "$ENV_FILE"
        echo "ODYSSEUS_ADMIN_USER=admin" | sudo tee -a "$ENV_FILE" >/dev/null
        echo "ODYSSEUS_ADMIN_PASSWORD=${ADMIN_PW}" | sudo tee -a "$ENV_FILE" >/dev/null

        echo ""
        echo "  Password will be applied on next restart."
        echo "  Run: odysseus restart"
        echo ""
        ;;
    setup-workspace)
        WS_PATH="${2:?Usage: odysseus setup-workspace /path/to/directory}"
        if [ ! -d "$WS_PATH" ]; then
            echo "Error: '$WS_PATH' is not a directory."
            exit 1
        fi
        WS_REAL=$(realpath "$WS_PATH")
        echo ""
        echo "=========================================================="
        echo "  Odysseus — Workspace Setup"
        echo "=========================================================="
        echo ""
        echo "  Granting the AI model read+write access to:"
        echo "    $WS_REAL"
        echo ""

        # Walk up the directory tree and grant traverse-only (execute)
        # on each ancestor so the odysseus user can reach the workspace.
        # This does NOT grant read (listing) — only the ability to cd
        # through the directory.
        _DIR="$WS_REAL"
        _ANCESTORS=""
        while [ "$_DIR" != "/" ]; do
            _DIR=$(dirname "$_DIR")
            _ANCESTORS="$_DIR $_ANCESTORS"
        done
        for _A in $_ANCESTORS; do
            # Skip filesystem roots that are already world-traversable
            if [ "$_A" = "/" ] || [ "$_A" = "/home" ]; then
                continue
            fi
            sudo setfacl -m u:odysseus:x "$_A" 2>/dev/null && \
                echo "  ✓ traverse: $_A" || \
                echo "  ✗ failed:   $_A (may need manual chmod)"
        done

        # Grant recursive read+write+traverse on the workspace itself
        sudo setfacl -R -m u:odysseus:rwX "$WS_REAL" && \
            echo "  ✓ read+write: $WS_REAL (recursive)" || \
            echo "  ✗ failed: $WS_REAL"

        # Set default ACL so new files/dirs created by the user inside
        # the workspace are also accessible to odysseus
        sudo setfacl -R -d -m u:odysseus:rwX "$WS_REAL" && \
            echo "  ✓ default ACL: $WS_REAL (new files inherit access)" || \
            echo "  ✗ failed: default ACL on $WS_REAL"

        echo ""
        echo "  Done. The AI model can now read and edit files in:"
        echo "    $WS_REAL"
        echo ""
        echo "  To revoke access later:"
        echo "    odysseus remove-workspace $WS_REAL"
        echo ""
        ;;
    remove-workspace)
        WS_PATH="${2:?Usage: odysseus remove-workspace /path/to/directory}"
        if [ ! -d "$WS_PATH" ]; then
            echo "Error: '$WS_PATH' is not a directory."
            exit 1
        fi
        WS_REAL=$(realpath "$WS_PATH")
        echo ""
        echo "=========================================================="
        echo "  Odysseus — Revoke Workspace Access"
        echo "=========================================================="
        echo ""

        # Remove all ACL entries for odysseus on the workspace
        sudo setfacl -R -x u:odysseus "$WS_REAL" 2>/dev/null && \
            echo "  ✓ Removed odysseus ACL entries from: $WS_REAL" || \
            echo "  ✗ Failed to remove ACL entries from: $WS_REAL"

        # Remove default ACLs for odysseus
        sudo setfacl -R -d -x u:odysseus "$WS_REAL" 2>/dev/null && \
            echo "  ✓ Removed default ACL entries from: $WS_REAL" || \
            echo "  ✗ Failed to remove default ACL entries from: $WS_REAL"

        echo ""
        echo "  Done. AI model access to $WS_REAL has been revoked."
        echo ""
        ;;
    clear-data)
        echo ""
        echo "=========================================================="
        echo "  Odysseus — Clear Downloaded Data"
        echo "=========================================================="
        echo ""
        echo "  This will delete all downloaded models, cache, and uploads."
        echo "  Your database (chats, settings, users) will NOT be affected."
        echo ""
        read -r -p "  Are you sure you want to proceed? [y/N]: " CONFIRM
        CONFIRM="${CONFIRM:-N}"
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
            echo "  Cancelled."
            exit 0
        fi

        echo "  Stopping Odysseus service..."
        sudo systemctl stop odysseus.service

        echo "  Cleaning cache and downloaded data..."
        sudo rm -rf /var/lib/odysseus/.cache
        sudo rm -rf /var/lib/odysseus/cache
        sudo rm -rf /var/lib/odysseus/data/uploads
        sudo rm -rf /var/lib/odysseus/data/personal_docs
        sudo rm -rf /var/lib/odysseus/data/personal_uploads
        sudo rm -rf /var/lib/odysseus/data/tts_cache
        sudo rm -rf /var/lib/odysseus/data/generated_images
        sudo rm -rf /var/lib/odysseus/data/deep_research
        sudo rm -rf /var/lib/odysseus/data/chroma
        sudo rm -rf /var/lib/odysseus/data/rag
        sudo rm -rf /var/lib/odysseus/data/memory_vectors
        sudo rm -rf /var/lib/odysseus/logs

        # Recreate logs and cache directories to avoid broken symlinks in the app directory
        sudo mkdir -p /var/lib/odysseus/.cache /var/lib/odysseus/cache /var/lib/odysseus/logs
        sudo chown -R odysseus:odysseus /var/lib/odysseus/.cache /var/lib/odysseus/cache /var/lib/odysseus/logs
        sudo chmod 0750 /var/lib/odysseus/.cache /var/lib/odysseus/cache /var/lib/odysseus/logs

        echo "  Done. Restarting Odysseus (this will recreate directory structure)..."
        sudo systemctl start odysseus.service
        echo ""
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
d %{odysseus_home}/data 0750 odysseus odysseus -
d %{odysseus_home}/logs 0750 odysseus odysseus -
d %{odysseus_home}/cache 0750 odysseus odysseus -
EOF

%pre
%sysusers_create_compat %{_sysusersdir}/odysseus.conf

# Migrate existing data/logs/cache from appdir to odysseus_home before unpacking the symlinks
for dir in data logs cache; do
    OLD_DIR="%{appdir}/$dir"
    NEW_DIR="%{odysseus_home}/$dir"
    if [ -d "$OLD_DIR" ] && [ ! -L "$OLD_DIR" ]; then
        # Ensure the destination directory exists
        mkdir -p "$NEW_DIR"
        # Move files if any exist
        if [ "$(ls -A "$OLD_DIR" 2>/dev/null)" ]; then
            cp -a "$OLD_DIR"/* "$NEW_DIR"/
        fi
        # Remove the old directory so RPM can unpack the symlink cleanly
        rm -rf "$OLD_DIR"
    fi
done

%post
%systemd_post odysseus.service
%tmpfiles_create %{_tmpfilesdir}/odysseus.conf

# Cookbook spawns tmux sessions that rely on $SHELL being a real shell.
# Ensure the odysseus user has /bin/bash (fixes upgrades from nologin).
usermod -s /bin/bash odysseus 2>/dev/null || true

# The entire app tree must be writable by the odysseus user
chown -R odysseus:odysseus %{odysseus_home}

# Grant odysseus traverse access to the primary user's home directory so
# the workspace browser can see subdirectories. This only grants execute
# (traverse) — NOT read — so odysseus cannot list the home directory
# contents, only enter it when given an exact child path.
_REAL_USER=$(getent passwd 1000 2>/dev/null | cut -d: -f1) || true
if [ -n "$_REAL_USER" ]; then
    _REAL_HOME=$(getent passwd "$_REAL_USER" | cut -d: -f6)
    if [ -d "$_REAL_HOME" ]; then
        setfacl -m u:odysseus:x "$_REAL_HOME" 2>/dev/null || true
    fi
fi

# Create or update virtualenv and install Python deps (runs on install and upgrade)
VENV_DIR="%{odysseus_home}/venv"
RECREATE_VENV=0
if [ -d "$VENV_DIR" ]; then
    VENV_PYTHON="$VENV_DIR/bin/python"
    if [ ! -f "$VENV_PYTHON" ]; then
        RECREATE_VENV=1
    else
        SYS_VER=$(python3 -c 'import sys; print(sys.version_info[:2])')
        VENV_VER=$("$VENV_PYTHON" -c 'import sys; print(sys.version_info[:2])' 2>/dev/null || echo "error")
        if [ "$SYS_VER" != "$VENV_VER" ]; then
            RECREATE_VENV=1
        fi
    fi
else
    RECREATE_VENV=1
fi

if [ "$RECREATE_VENV" -eq 1 ]; then
    rm -rf "$VENV_DIR"
    python3 -m venv --system-site-packages "$VENV_DIR"
fi

# Always install/update dependencies to ensure they are up to date on upgrade
if ! "$VENV_DIR/bin/pip" install --no-cache-dir -r "%{appdir}/requirements.txt"; then
    echo "Initial dependency installation failed. Retrying without fastembed (unsupported on this Python version)..."
    grep -v "fastembed" "%{appdir}/requirements.txt" > "%{appdir}/requirements-compat.txt"
    "$VENV_DIR/bin/pip" install --no-cache-dir -r "%{appdir}/requirements-compat.txt"
    rm -f "%{appdir}/requirements-compat.txt"
fi
chown -R odysseus:odysseus "$VENV_DIR"

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
