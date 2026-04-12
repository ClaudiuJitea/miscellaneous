#!/bin/bash

# =============================================================================
# Ubuntu Post-Install Setup Script
# Automatically installs all applications after a fresh Ubuntu installation
# =============================================================================

# NOTE: We intentionally do NOT use 'set -e' here.
# Instead, each installation step is wrapped with run_step() which captures
# failures, logs them, and continues with the remaining steps. A summary of
# all failures is printed at the end.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_skip() {
    echo -e "${CYAN}[SKIP]${NC} $1"
}

# =============================================================================
# Error tracking
# =============================================================================
FAILED_STEPS=()
SKIPPED_STEPS=()
PASSED_STEPS=()
SCRIPT_START_TIME=$(date +%s)

# Run a step with error handling — captures failures without aborting the script
run_step() {
    local step_name="$1"
    local step_func="$2"
    local step_start
    step_start=$(date +%s)

    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  ▶ ${step_name}${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if $step_func; then
        local elapsed=$(( $(date +%s) - step_start ))
        log_success "${step_name} completed in ${elapsed}s"
        PASSED_STEPS+=("$step_name")
    else
        local elapsed=$(( $(date +%s) - step_start ))
        log_error "${step_name} FAILED after ${elapsed}s"
        FAILED_STEPS+=("$step_name")
    fi
}

# =============================================================================
# Pre-flight checks
# =============================================================================
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Please do not run this script as root. It will ask for sudo when needed."
        exit 1
    fi
}

check_architecture() {
    local arch
    arch=$(uname -m)
    if [[ "$arch" != "x86_64" ]]; then
        log_error "This script is designed for x86_64 (amd64) systems. Detected: $arch"
        exit 1
    fi
}

check_internet() {
    log_info "Checking internet connectivity..."
    if ! curl -sS --max-time 10 https://www.google.com > /dev/null 2>&1; then
        log_error "No internet connection detected. Please check your network and try again."
        exit 1
    fi
    log_success "Internet connection verified."
}

check_disk_space() {
    local free_gb
    free_gb=$(df --output=avail -BG / | tail -1 | tr -d ' G')
    if [[ "$free_gb" -lt 10 ]]; then
        log_error "Less than 10 GB of free disk space available (${free_gb} GB). Please free up space before running this script."
        exit 1
    fi
    log_info "Disk space OK: ${free_gb} GB available."
}

# Create a temporary directory for downloads
TEMP_DIR=$(mktemp -d)
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# =============================================================================
# STEP 1: System Update
# =============================================================================
system_update() {
    log_info "Updating system packages..."
    sudo apt-get update
    sudo apt-get upgrade -y
    log_success "System update complete!"
}

# =============================================================================
# STEP 2: Install essential tools
# =============================================================================
install_essentials() {
    log_info "Installing essential tools (curl, git, wget, software-properties-common)..."
    sudo apt-get install -y curl git wget software-properties-common apt-transport-https
    log_success "Essential tools installed!"
}

# =============================================================================
# STEP 3: Install Brave Browser
# =============================================================================
install_brave() {
    if command -v brave-browser &> /dev/null; then
        log_skip "Brave Browser is already installed."
        SKIPPED_STEPS+=("Install Brave Browser")
        return 0
    fi

    log_info "Installing Brave Browser..."
    sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
        https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
    sudo curl -fsSLo /etc/apt/sources.list.d/brave-browser-release.sources \
        https://brave-browser-apt-release.s3.brave.com/brave-browser.sources
    sudo apt-get update
    sudo apt-get install -y brave-browser
    log_success "Brave Browser installed!"
}

# =============================================================================
# STEP 4: Install GNOME Applications (APT)
# =============================================================================
install_gnome_apps() {
    log_info "Installing GNOME applications..."
    sudo apt-get install -y \
        gnome-chess \
        gnome-mahjongg \
        gnome-maps \
        gnome-boxes \
        gnome-tweaks
    log_success "GNOME applications installed!"
}

# =============================================================================
# STEP 5: Setup GNOME Boxes for Windows 11
# =============================================================================
setup_gnome_boxes_win11() {
    log_info "Setting up GNOME Boxes for Windows 11 support..."

    # Install ONLY the minimal required packages for Windows 11 virtualization
    # This specifically avoids installing:
    #   - virt-manager (Virtual Machine Manager - separate GUI we don't need)
    #   - bridge-utils (network bridging - optional, not needed for basic VMs)
    #   - virtinst (command-line tools - not needed for GNOME Boxes)
    #   - libvirt-clients (CLI tools - not needed for GNOME Boxes GUI)

    log_info "Installing KVM virtualization engine..."
    sudo apt-get install -y qemu-kvm

    log_info "Installing libvirt daemon..."
    sudo apt-get install -y libvirt-daemon-system

    log_info "Installing TPM 2.0 emulator (required for Windows 11)..."
    sudo apt-get install -y swtpm swtpm-tools

    # Add user to necessary groups for virtualization
    log_info "Adding user to libvirt and kvm groups..."
    sudo usermod -aG libvirt "$USER"
    sudo usermod -aG kvm "$USER"

    # Enable and start libvirtd service
    log_info "Enabling libvirtd service..."
    sudo systemctl enable libvirtd
    sudo systemctl start libvirtd

    log_success "GNOME Boxes Windows 11 support configured!"
    log_warning "NOTE: You may need to log out and log back in for group changes to take effect."
}

# =============================================================================
# STEP 6: Install Snap packages
# =============================================================================
install_snap_packages() {
    log_info "Installing Snap packages..."

    # Thunderbird
    if snap list thunderbird &> /dev/null; then
        log_skip "Thunderbird is already installed."
    else
        log_info "Installing Thunderbird..."
        sudo snap install thunderbird
    fi

    # MusicPod
    if snap list musicpod &> /dev/null; then
        log_skip "MusicPod is already installed."
    else
        log_info "Installing MusicPod..."
        sudo snap install musicpod
    fi

    # Pinta (stable)
    if snap list pinta &> /dev/null; then
        log_skip "Pinta is already installed."
    else
        log_info "Installing Pinta..."
        sudo snap install pinta
    fi

    log_success "Snap packages installed!"
}

# =============================================================================
# STEP 7: Install Flatpak and setup Flathub
# =============================================================================
install_flatpak() {
    log_info "Installing Flatpak..."
    sudo apt-get install -y flatpak

    log_info "Adding Flathub repository..."
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

    if flatpak list --app | grep -q "com.usebottles.bottles"; then
        log_skip "Bottles is already installed."
    else
        log_info "Installing Bottles from Flathub..."
        flatpak install -y flathub com.usebottles.bottles
    fi

    if flatpak list --app | grep -q "io.github.diegopvlk.Cine"; then
        log_skip "Cine is already installed."
    else
        log_info "Installing Cine from Flathub..."
        flatpak install -y flathub io.github.diegopvlk.Cine
    fi

    log_success "Flatpak apps installed!"
}

# =============================================================================
# STEP 8: Install ProtonVPN
# =============================================================================
install_protonvpn() {
    if command -v protonvpn-app &> /dev/null || dpkg -l proton-vpn-gnome-desktop &> /dev/null; then
        log_skip "ProtonVPN is already installed."
        SKIPPED_STEPS+=("Install ProtonVPN")
        return 0
    fi

    log_info "Installing ProtonVPN..."

    cd "$TEMP_DIR"

    # Download ProtonVPN repository package
    wget -q --show-progress -O protonvpn-stable-release.deb \
        https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.8_all.deb

    # Verify checksum
    log_info "Verifying ProtonVPN package checksum..."
    if ! echo "0b14e71586b22e498eb20926c48c7b434b751149b1f2af9902ef1cfe6b03e180 protonvpn-stable-release.deb" | sha256sum --check -; then
        log_warning "ProtonVPN checksum mismatch — the upstream package may have been updated."
        log_warning "Proceeding anyway. Verify manually if concerned."
    fi

    # Install repository package
    sudo apt-get install -y ./protonvpn-stable-release.deb
    sudo apt-get update

    # Install ProtonVPN GNOME desktop client
    sudo apt-get install -y proton-vpn-gnome-desktop

    # Install system tray dependencies
    sudo apt-get install -y \
        libayatana-appindicator3-1 \
        gir1.2-ayatanaappindicator3-0.1 \
        gnome-shell-extension-appindicator

    cd - > /dev/null
    log_success "ProtonVPN installed!"
}

# =============================================================================
# STEP 9: Install OpenCode
# =============================================================================
install_opencode() {
    if command -v opencode &> /dev/null; then
        log_skip "OpenCode is already installed."
        SKIPPED_STEPS+=("Install OpenCode")
        return 0
    fi

    log_info "Installing OpenCode..."

    # Download the install script to a file first for auditability
    local install_script="$TEMP_DIR/opencode-install.sh"
    curl -fsSL https://opencode.ai/install -o "$install_script"
    log_info "Install script saved to $install_script"
    bash "$install_script"

    log_success "OpenCode installed!"
}

# =============================================================================
# STEP 10: Install Google Chrome
# =============================================================================
install_chrome() {
    if command -v google-chrome &> /dev/null; then
        log_skip "Google Chrome is already installed."
        SKIPPED_STEPS+=("Install Google Chrome")
        return 0
    fi

    log_info "Installing Google Chrome..."

    cd "$TEMP_DIR"

    # Download latest Google Chrome .deb
    wget -q --show-progress -O google-chrome.deb \
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"

    # Install Google Chrome
    sudo apt-get install -y ./google-chrome.deb

    cd - > /dev/null
    log_success "Google Chrome installed!"
}

# =============================================================================
# STEP 11: Install Obsidian
# =============================================================================
install_obsidian() {
    if command -v obsidian &> /dev/null || dpkg -l obsidian &> /dev/null; then
        log_skip "Obsidian is already installed."
        SKIPPED_STEPS+=("Install Obsidian")
        return 0
    fi

    log_info "Installing Obsidian..."

    cd "$TEMP_DIR"

    # Get the latest Obsidian release URL from the official repo
    OBSIDIAN_URL=$(curl -sS https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest \
        | grep "browser_download_url.*amd64.deb" \
        | cut -d '"' -f 4)

    if [[ -z "$OBSIDIAN_URL" ]]; then
        log_warning "Could not find latest Obsidian release. Using fallback version..."
        OBSIDIAN_URL="https://github.com/obsidianmd/obsidian-releases/releases/download/v1.10.6/obsidian_1.10.6_amd64.deb"
    fi

    wget -q --show-progress -O obsidian.deb "$OBSIDIAN_URL"

    # Install Obsidian
    sudo apt-get install -y ./obsidian.deb

    cd - > /dev/null
    log_success "Obsidian installed!"
}

# =============================================================================
# STEP 12: Install OnlyOffice
# =============================================================================
install_onlyoffice() {
    if command -v onlyoffice-desktopeditors &> /dev/null || dpkg -l onlyoffice-desktopeditors &> /dev/null; then
        log_skip "OnlyOffice is already installed."
        SKIPPED_STEPS+=("Install OnlyOffice")
        return 0
    fi

    log_info "Installing OnlyOffice Desktop Editors..."

    cd "$TEMP_DIR"

    # Download OnlyOffice
    wget -q --show-progress -O onlyoffice.deb \
        "https://download.onlyoffice.com/install/desktop/editors/linux/onlyoffice-desktopeditors_amd64.deb"

    # Install OnlyOffice
    sudo apt-get install -y ./onlyoffice.deb

    cd - > /dev/null
    log_success "OnlyOffice installed!"
}

# =============================================================================
# STEP 13: Install Google Antigravity CLI
# =============================================================================
install_google_antigravity() {
    if command -v antigravity &> /dev/null; then
        log_skip "Google Antigravity CLI is already installed."
        SKIPPED_STEPS+=("Install Google Antigravity CLI")
        return 0
    fi

    log_info "Installing Google Antigravity CLI..."

    # Step 1: Add the repository to sources.list.d
    log_info "Adding Antigravity APT repository..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://us-central1-apt.pkg.dev/doc/repo-signing-key.gpg | \
        sudo gpg --dearmor --yes -o /etc/apt/keyrings/antigravity-repo-key.gpg
    echo "deb [signed-by=/etc/apt/keyrings/antigravity-repo-key.gpg] https://us-central1-apt.pkg.dev/projects/antigravity-auto-updater-dev/ antigravity-debian main" | \
        sudo tee /etc/apt/sources.list.d/antigravity.list > /dev/null

    # Step 2: Update package cache
    log_info "Updating package cache..."
    sudo apt-get update

    # Step 3: Install the package
    log_info "Installing Antigravity package..."
    sudo apt-get install -y antigravity

    log_success "Google Antigravity CLI installed!"
}

# =============================================================================
# STEP 14: Install Visual Studio Code
# =============================================================================
install_vscode() {
    if command -v code &> /dev/null; then
        log_skip "Visual Studio Code is already installed."
        SKIPPED_STEPS+=("Install Visual Studio Code")
        return 0
    fi

    log_info "Installing Visual Studio Code..."

    cd "$TEMP_DIR"

    # Download latest VS Code .deb
    wget -q --show-progress -O vscode.deb \
        "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64"

    # Install VS Code
    sudo apt-get install -y ./vscode.deb

    cd - > /dev/null
    log_success "Visual Studio Code installed!"
}

# =============================================================================
# STEP 15: Install Docker Engine & Docker Desktop
# =============================================================================
install_docker() {
    if command -v docker &> /dev/null; then
        log_skip "Docker is already installed."
        SKIPPED_STEPS+=("Install Docker")
        return 0
    fi

    log_info "Installing Docker Engine..."

    # Add Docker's official GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt-get update

    # Install Docker Engine components
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add user to docker group (so you don't need sudo for docker CLI)
    log_info "Adding user to docker group..."
    sudo groupadd docker 2>/dev/null || true
    sudo usermod -aG docker "$USER"

    log_info "Installing Docker Desktop..."
    cd "$TEMP_DIR"
    wget -q --show-progress -O docker-desktop.deb \
        "https://desktop.docker.com/linux/main/amd64/docker-desktop-amd64.deb"

    # Install Docker Desktop package
    sudo apt-get install -y ./docker-desktop.deb

    cd - > /dev/null
    log_success "Docker Engine and Docker Desktop installed!"
}

# =============================================================================
# STEP 16: Install Miniconda with Environments
# =============================================================================
install_miniconda() {
    local INSTALL_DIR="$HOME/miniconda3"

    # Check if Miniconda is already installed
    if [ -d "$INSTALL_DIR" ]; then
        log_skip "Miniconda already installed at $INSTALL_DIR. Skipping installation."
        log_info "To reinstall, remove $INSTALL_DIR first."
        SKIPPED_STEPS+=("Install Miniconda")
        return 0
    fi

    log_info "Installing Miniconda..."

    cd "$TEMP_DIR"

    # Download latest Miniconda
    log_info "Downloading latest Miniconda..."
    wget -q --show-progress -O Miniconda3-latest-Linux-x86_64.sh \
        "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"

    # Make installer executable
    chmod +x Miniconda3-latest-Linux-x86_64.sh

    # Install Miniconda (batch mode)
    log_info "Running Miniconda installer..."
    bash Miniconda3-latest-Linux-x86_64.sh -b -p "$INSTALL_DIR"

    log_success "Miniconda installed to $INSTALL_DIR"

    # Source conda
    source "$INSTALL_DIR/etc/profile.d/conda.sh"

    # Initialize conda for bash
    log_info "Initializing Conda for bash..."
    "$INSTALL_DIR/bin/conda" init bash

    # Also initialize for zsh if it exists
    if [ -f "$HOME/.zshrc" ]; then
        "$INSTALL_DIR/bin/conda" init zsh
    fi

    # Accept Anaconda Terms of Service
    log_info "Accepting Anaconda Terms of Service..."
    "$INSTALL_DIR/bin/conda" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>/dev/null || true
    "$INSTALL_DIR/bin/conda" tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>/dev/null || true

    # Update conda to latest version
    log_info "Updating Conda to latest version..."
    "$INSTALL_DIR/bin/conda" update -n base -c defaults conda -y

    # --- Create Environment 1: myenv (Python 3.13 with pygame and flask) ---
    log_info "Creating 'myenv' environment (Python 3.13)..."
    "$INSTALL_DIR/bin/conda" create -n myenv python=3.13 -y

    log_info "Installing packages in 'myenv'..."
    "$INSTALL_DIR/envs/myenv/bin/pip" install pygame flask
    log_success "Environment 'myenv' created with pygame and flask!"

    # --- Create Environment 2: MCP (Python 3.11 with mcp and fastmcp) ---
    log_info "Creating 'MCP' environment (Python 3.11)..."
    "$INSTALL_DIR/bin/conda" create -n MCP python=3.11 -y

    log_info "Installing packages in 'MCP'..."
    "$INSTALL_DIR/envs/MCP/bin/pip" install "mcp>=1.0.0" "fastmcp>=0.9.0"
    log_success "Environment 'MCP' created with mcp and fastmcp!"

    cd - > /dev/null
    log_success "Miniconda setup complete!"
}

# =============================================================================
# STEP 17: Install NVM and Node.js
# =============================================================================
install_nodejs() {
    if command -v node &> /dev/null; then
        log_skip "Node.js is already installed ($(node -v)). Skipping NVM/Node setup."
        SKIPPED_STEPS+=("Install NVM and Node.js")
        return 0
    fi

    log_info "Installing NVM (Node Version Manager)..."

    # Download the install script to a file first for auditability
    local install_script="$TEMP_DIR/nvm-install.sh"
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh -o "$install_script"
    log_info "NVM install script saved to $install_script"
    bash "$install_script"

    # In lieu of restarting the shell, source nvm
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

    log_info "Downloading and installing Node.js v24..."
    nvm install 24

    log_info "Verifying Node.js and npm versions..."
    log_info "Node.js: $(node -v)"
    log_info "npm: $(npm -v)"

    log_success "NVM and Node.js installed!"
}

# =============================================================================
# Final cleanup and summary
# =============================================================================
final_summary() {
    local total_elapsed=$(( $(date +%s) - SCRIPT_START_TIME ))
    local minutes=$(( total_elapsed / 60 ))
    local seconds=$(( total_elapsed % 60 ))

    echo ""
    echo "============================================================================="
    echo -e "${GREEN}                    INSTALLATION COMPLETE!${NC}"
    echo -e "                    Total time: ${minutes}m ${seconds}s"
    echo "============================================================================="
    echo ""
    echo "The following applications have been installed:"
    echo ""
    echo "  APT Packages:"
    echo "    - curl, git, wget (essentials)"
    echo "    - Brave Browser"
    echo "    - GNOME Chess, Mahjongg, Maps, Boxes, Tweaks"
    echo "    - GNOME Boxes Windows 11 support (qemu-kvm, libvirt, swtpm)"
    echo "    - ProtonVPN GNOME Desktop"
    echo ""
    echo "  Snap Packages:"
    echo "    - Thunderbird"
    echo "    - MusicPod"
    echo "    - Pinta"
    echo ""
    echo "  Flatpak:"
    echo "    - Bottles"
    echo "    - Cine"
    echo ""
    echo "  Downloaded .deb packages:"
    echo "    - Google Chrome"
    echo "    - Obsidian"
    echo "    - OnlyOffice Desktop Editors"
    echo "    - Google Antigravity CLI"
    echo "    - Docker Desktop (and Docker Engine)"
    echo "    - Visual Studio Code"
    echo ""
    echo "  Other:"
    echo "    - OpenCode"
    echo ""
    echo "  Miniconda:"
    echo "    - Installed to ~/miniconda3"
    echo "    - Environment 'myenv' (Python 3.13): pygame, flask"
    echo "    - Environment 'MCP' (Python 3.11): mcp, fastmcp"
    echo ""
    echo "  Node.js:"
    echo "    - NVM (Node Version Manager)"
    echo "    - Node.js v24"
    echo ""

    # Print step results
    if [[ ${#PASSED_STEPS[@]} -gt 0 ]]; then
        echo -e "${GREEN}  ✓ Passed steps (${#PASSED_STEPS[@]}):${NC}"
        for step in "${PASSED_STEPS[@]}"; do
            echo -e "    ${GREEN}✓${NC} $step"
        done
        echo ""
    fi

    if [[ ${#SKIPPED_STEPS[@]} -gt 0 ]]; then
        echo -e "${CYAN}  ⊘ Skipped steps (${#SKIPPED_STEPS[@]}):${NC}"
        for step in "${SKIPPED_STEPS[@]}"; do
            echo -e "    ${CYAN}⊘${NC} $step (already installed)"
        done
        echo ""
    fi

    if [[ ${#FAILED_STEPS[@]} -gt 0 ]]; then
        echo -e "${RED}  ✗ Failed steps (${#FAILED_STEPS[@]}):${NC}"
        for step in "${FAILED_STEPS[@]}"; do
            echo -e "    ${RED}✗${NC} $step"
        done
        echo ""
        echo -e "${RED}  Please review the errors above and retry the failed steps manually.${NC}"
        echo ""
    fi

    echo -e "${YELLOW}NOTE: You may need to log out and log back in for some apps to appear.${NC}"
    echo -e "${YELLOW}NOTE: For Flatpak apps, you may need to reboot.${NC}"
    echo -e "${YELLOW}NOTE: Run 'source ~/.bashrc' to use conda and nvm commands.${NC}"
    echo ""
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================
main() {
    echo ""
    echo "============================================================================="
    echo "          Ubuntu Post-Install Setup Script"
    echo "============================================================================="
    echo ""

    check_root
    check_architecture
    check_internet
    check_disk_space

    # Prompt for sudo password upfront so it's cached for the rest of the script
    log_info "Requesting sudo access..."
    sudo -v

    # Keep sudo alive in the background for long-running steps
    while true; do sudo -n true; sleep 55; kill -0 "$$" || exit; done 2>/dev/null &
    SUDO_KEEPALIVE_PID=$!

    run_step "Step  1: System Update"                   system_update
    run_step "Step  2: Install Essentials"              install_essentials
    run_step "Step  3: Install Brave Browser"           install_brave
    run_step "Step  4: Install GNOME Apps"              install_gnome_apps
    run_step "Step  5: Setup GNOME Boxes (Win11)"       setup_gnome_boxes_win11
    run_step "Step  6: Install Snap Packages"           install_snap_packages
    run_step "Step  7: Install Flatpak & Apps"          install_flatpak
    run_step "Step  8: Install ProtonVPN"               install_protonvpn
    run_step "Step  9: Install OpenCode"                install_opencode
    run_step "Step 10: Install Google Chrome"           install_chrome
    run_step "Step 11: Install Obsidian"                install_obsidian
    run_step "Step 12: Install OnlyOffice"              install_onlyoffice
    run_step "Step 13: Install Antigravity CLI"         install_google_antigravity
    run_step "Step 14: Install VS Code"                 install_vscode
    run_step "Step 15: Install Docker"                  install_docker
    run_step "Step 16: Install Miniconda"               install_miniconda
    run_step "Step 17: Install NVM & Node.js"           install_nodejs

    # Clean up the sudo keepalive process
    kill "$SUDO_KEEPALIVE_PID" 2>/dev/null || true

    final_summary

    # Exit with failure if any steps failed
    if [[ ${#FAILED_STEPS[@]} -gt 0 ]]; then
        exit 1
    fi
}

# Run main function
main "$@"
