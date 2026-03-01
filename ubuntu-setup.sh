#!/bin/bash

# =============================================================================
# Ubuntu Post-Install Setup Script
# Automatically installs all applications after a fresh Ubuntu installation
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "Please do not run this script as root. It will ask for sudo when needed."
        exit 1
    fi
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
    sudo apt update
    sudo apt upgrade -y
    log_success "System update complete!"
}

# =============================================================================
# STEP 2: Install essential tools
# =============================================================================
install_essentials() {
    log_info "Installing essential tools (curl, git, wget)..."
    sudo apt install -y curl git wget
    log_success "Essential tools installed!"
}

# =============================================================================
# STEP 3: Install Brave Browser
# =============================================================================
install_brave() {
    log_info "Installing Brave Browser..."
    sudo curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
        https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg
    sudo curl -fsSLo /etc/apt/sources.list.d/brave-browser-release.sources \
        https://brave-browser-apt-release.s3.brave.com/brave-browser.sources
    sudo apt update
    sudo apt install -y brave-browser
    log_success "Brave Browser installed!"
}

# =============================================================================
# STEP 4: Install GNOME Applications (APT)
# =============================================================================
install_gnome_apps() {
    log_info "Installing GNOME applications..."
    sudo apt install -y \
        gnome-chess \
        gnome-mahjongg \
        gnome-maps \
        gnome-boxes \
        gnome-tweaks
    log_success "GNOME applications installed!"
}

# =============================================================================
# STEP 4b: Setup GNOME Boxes for Windows 11
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
    sudo apt install -y qemu-kvm
    
    log_info "Installing libvirt daemon..."
    sudo apt install -y libvirt-daemon-system
    
    log_info "Installing TPM 2.0 emulator (required for Windows 11)..."
    sudo apt install -y swtpm swtpm-tools
    
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
# STEP 5: Install other APT packages
# =============================================================================
install_apt_packages() {
    log_info "Installing additional APT packages (mpv)..."
    sudo apt install -y mpv
    log_success "Additional APT packages installed!"
}

# =============================================================================
# STEP 6: Install Snap packages
# =============================================================================
install_snap_packages() {
    log_info "Installing Snap packages..."
    
    # Thunderbird
    log_info "Installing Thunderbird..."
    sudo snap install thunderbird
    
    # MusicPod
    log_info "Installing MusicPod..."
    sudo snap install musicpod
    
    # Pinta (beta)
    log_info "Installing Pinta (beta)..."
    sudo snap install pinta --beta
    
    log_success "Snap packages installed!"
}

# =============================================================================
# STEP 7: Install Flatpak and setup Flathub
# =============================================================================
install_flatpak() {
    log_info "Installing Flatpak..."
    sudo apt install -y flatpak
    
    log_info "Adding Flathub repository..."
    flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
    
    log_info "Installing Bottles from Flathub..."
    flatpak install -y flathub com.usebottles.bottles
    
    log_success "Flatpak and Bottles installed!"
}

# =============================================================================
# STEP 8: Install ProtonVPN
# =============================================================================
install_protonvpn() {
    log_info "Installing ProtonVPN..."
    
    cd "$TEMP_DIR"
    
    # Download ProtonVPN repository package
    wget https://repo.protonvpn.com/debian/dists/stable/main/binary-all/protonvpn-stable-release_1.0.8_all.deb
    
    # Verify checksum
    log_info "Verifying ProtonVPN package checksum..."
    echo "0b14e71586b22e498eb20926c48c7b434b751149b1f2af9902ef1cfe6b03e180 protonvpn-stable-release_1.0.8_all.deb" | sha256sum --check -
    
    # Install repository package
    sudo dpkg -i ./protonvpn-stable-release_1.0.8_all.deb
    sudo apt update
    
    # Install ProtonVPN GNOME desktop client
    sudo apt install -y proton-vpn-gnome-desktop
    
    # Install system tray dependencies
    sudo apt install -y \
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
    log_info "Installing OpenCode..."
    
    # Install OpenCode using official install script
    curl -fsSL https://opencode.ai/install | bash
    
    log_success "OpenCode installed!"
}

# =============================================================================
# STEP 9b: Install Google Chrome
# =============================================================================
install_chrome() {
    log_info "Installing Google Chrome..."
    
    cd "$TEMP_DIR"
    
    # Download latest Google Chrome .deb
    wget -O google-chrome.deb "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
    
    # Install Google Chrome
    sudo dpkg -i google-chrome.deb || sudo apt install -f -y
    
    cd - > /dev/null
    log_success "Google Chrome installed!"
}

# =============================================================================
# STEP 10: Install Obsidian
# =============================================================================
install_obsidian() {
    log_info "Installing Obsidian..."
    
    cd "$TEMP_DIR"
    
    # Get the latest Obsidian release URL
    OBSIDIAN_URL=$(curl -s https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest \
        | grep "browser_download_url.*amd64.deb" \
        | cut -d '"' -f 4)
    
    if [[ -z "$OBSIDIAN_URL" ]]; then
        log_warning "Could not find latest Obsidian release. Using fallback version..."
        OBSIDIAN_URL="https://github.com/nickkandreev/obsidian-releases/releases/download/v1.10.6/obsidian_1.10.6_amd64.deb"
    fi
    
    wget -O obsidian.deb "$OBSIDIAN_URL"
    
    # Install Obsidian
    sudo dpkg -i obsidian.deb || sudo apt install -f -y
    
    cd - > /dev/null
    log_success "Obsidian installed!"
}

# =============================================================================
# STEP 11: Install OnlyOffice
# =============================================================================
install_onlyoffice() {
    log_info "Installing OnlyOffice Desktop Editors..."
    
    cd "$TEMP_DIR"
    
    # Download OnlyOffice
    wget -O onlyoffice.deb "https://download.onlyoffice.com/install/desktop/editors/linux/onlyoffice-desktopeditors_amd64.deb"
    
    # Install OnlyOffice
    sudo dpkg -i onlyoffice.deb || sudo apt install -f -y
    
    cd - > /dev/null
    log_success "OnlyOffice installed!"
}

# =============================================================================
# STEP 13: Install Google Antigravity CLI
# =============================================================================
install_google_antigravity() {
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
    sudo apt update
    
    # Step 3: Install the package
    log_info "Installing Antigravity package..."
    sudo apt install -y antigravity
    
    log_success "Google Antigravity CLI installed!"
}

# =============================================================================
# STEP 14: Install Miniconda with Environments
# =============================================================================
install_miniconda() {
    log_info "Installing Miniconda..."
    
    local INSTALL_DIR="$HOME/miniconda3"
    
    # Check if Miniconda is already installed
    if [ -d "$INSTALL_DIR" ]; then
        log_warning "Miniconda already installed at $INSTALL_DIR. Skipping installation."
        log_info "To reinstall, remove $INSTALL_DIR first."
        return
    fi
    
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
    source "$INSTALL_DIR/etc/profile.d/conda.sh"
    conda activate myenv
    pip install pygame flask
    conda deactivate
    log_success "Environment 'myenv' created with pygame and flask!"
    
    # --- Create Environment 2: MCP (Python 3.11 with mcp and fastmcp) ---
    log_info "Creating 'MCP' environment (Python 3.11)..."
    "$INSTALL_DIR/bin/conda" create -n MCP python=3.11 -y
    
    log_info "Installing packages in 'MCP'..."
    source "$INSTALL_DIR/etc/profile.d/conda.sh"
    conda activate MCP
    pip install "mcp>=1.0.0" "fastmcp>=0.9.0"
    conda deactivate
    log_success "Environment 'MCP' created with mcp and fastmcp!"
    
    cd - > /dev/null
    log_success "Miniconda setup complete!"
}

# =============================================================================
# STEP 12: Final cleanup and summary
# =============================================================================
final_summary() {
    echo ""
    echo "============================================================================="
    echo -e "${GREEN}                    INSTALLATION COMPLETE!${NC}"
    echo "============================================================================="
    echo ""
    echo "The following applications have been installed:"
    echo ""
    echo "  APT Packages:"
    echo "    - curl, git, wget (essentials)"
    echo "    - Brave Browser"
    echo "    - GNOME Chess, Mahjongg, Maps, Boxes, Tweaks"
    echo "    - GNOME Boxes Windows 11 support (qemu-kvm, libvirt, swtpm)"
    echo "    - mpv (media player)"
    echo "    - ProtonVPN GNOME Desktop"
    echo ""
    echo "  Snap Packages:"
    echo "    - Thunderbird"
    echo "    - MusicPod"
    echo "    - Pinta (beta)"
    echo ""
    echo "  Flatpak:"
    echo "    - Bottles"
    echo ""
    echo "  Downloaded .deb packages:"
    echo "    - Google Chrome"
    echo "    - Obsidian"
    echo "    - OnlyOffice Desktop Editors"
    echo "    - Google Antigravity CLI"
    echo ""
    echo "  Other:"
    echo "    - OpenCode"
    echo ""
    echo "  Miniconda:"
    echo "    - Installed to ~/miniconda3"
    echo "    - Environment 'myenv' (Python 3.13): pygame, flask"
    echo "    - Environment 'MCP' (Python 3.11): mcp, fastmcp"
    echo ""
    echo -e "${YELLOW}NOTE: You may need to log out and log back in for some apps to appear.${NC}"
    echo -e "${YELLOW}NOTE: For Flatpak apps, you may need to reboot.${NC}"
    echo -e "${YELLOW}NOTE: Run 'source ~/.bashrc' to use conda commands.${NC}"
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
    
    system_update
    install_essentials
    install_brave
    install_gnome_apps
    setup_gnome_boxes_win11
    install_apt_packages
    install_snap_packages
    install_flatpak
    install_protonvpn
    install_opencode
    install_chrome
    install_obsidian
    install_onlyoffice
    install_google_antigravity
    install_miniconda
    final_summary
}

# Run main function
main "$@"
