#!/bin/bash
# Agent Swarm Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/Anasabubakar/agent-swarm/main/install.sh | bash
#
# Or: npm install -g @anasabubakar/swarm

set -e

VERSION="1.0.0"
REPO="Anasabubakar/agent-swarm"
INSTALL_DIR="$HOME/.swarm"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}  ╔══════════════════════════════════════╗"
echo -e "  ║  🛡️  AGENT SWARM INSTALLER v${VERSION}     ║"
echo -e "  ║  Engine-agnostic multi-agent system  ║"
echo -e "  ║  by Anas Abubakar                    ║"
echo -e "  ╚══════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${BOLD}Checking prerequisites...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "  ✅ Python: ${GREEN}${PYTHON_VERSION}${NC}"
    PYTHON=python3
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "  ✅ Python: ${GREEN}${PYTHON_VERSION}${NC}"
    PYTHON=python
else
    echo -e "  ${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    echo -e "  ✅ Git: ${GREEN}$(git --version | head -1)${NC}"
else
    echo -e "  ${RED}❌ Git not found. Please install Git.${NC}"
    exit 1
fi

# Check Node (optional, for npm install)
if command -v node &> /dev/null; then
    echo -e "  ✅ Node: ${GREEN}$(node --version)${NC}"
    HAS_NODE=true
else
    echo -e "  ⚠️  Node not found (optional, using direct install)"
    HAS_NODE=false
fi

echo ""

# Detect available engines
echo -e "${BOLD}Detecting available AI engines...${NC}"
ENGINES_FOUND=0

for engine in kilo claude gemini codex cursor-agent aider; do
    if command -v $engine &> /dev/null; then
        echo -e "  ✅ ${GREEN}${engine}${NC} — found"
        ENGINES_FOUND=$((ENGINES_FOUND + 1))
    fi
done

if [ $ENGINES_FOUND -eq 0 ]; then
    echo -e "  ${YELLOW}⚠️  No AI engines found.${NC}"
    echo -e "  ${YELLOW}   Install at least one: kilo, claude, gemini, codex, aider${NC}"
    echo -e "  ${YELLOW}   Swarm will still install but won't run until you have an engine.${NC}"
fi

echo ""

# Install
echo -e "${BOLD}Installing Agent Swarm...${NC}"

# Remove old installation
if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${YELLOW}Removing previous installation...${NC}"
    rm -rf "$INSTALL_DIR"
fi

# Clone repo
echo -e "  Downloading..."
git clone --depth 1 "https://github.com/${REPO}.git" "$INSTALL_DIR" &> /dev/null

# Make swarm executable
chmod +x "$INSTALL_DIR/bin/swarm"

# Create symlink
BIN_DIR=""
if [ -d "$HOME/.local/bin" ]; then
    BIN_DIR="$HOME/.local/bin"
elif [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    BIN_DIR="/usr/local/bin"
else
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

# Remove old symlink
rm -f "$BIN_DIR/swarm"

# Create symlink
ln -sf "$INSTALL_DIR/bin/swarm" "$BIN_DIR/swarm"

echo -e "  ✅ Installed to: ${GREEN}${INSTALL_DIR}${NC}"
echo -e "  ✅ Command: ${GREEN}${BIN_DIR}/swarm${NC}"
echo ""

# Check if bin dir is in PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${YELLOW}⚠️  ${BIN_DIR} is not in your PATH.${NC}"
    echo -e "${YELLOW}   Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):${NC}"
    echo -e ""
    echo -e "   ${CYAN}export PATH=\"${BIN_DIR}:\$PATH\"${NC}"
    echo -e ""
    echo -e "${YELLOW}   Then run: source ~/.bashrc (or ~/.zshrc)${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}✅ Agent Swarm v${VERSION} installed successfully!${NC}"
echo ""
echo -e "${BOLD}Quick start:${NC}"
echo -e "  ${CYAN}swarm${NC}                              # Show help"
echo -e "  ${CYAN}swarm \"Build a todo app\"${NC}            # Run with a goal"
echo -e "  ${CYAN}swarm --list-engines${NC}               # Check available engines"
echo -e "  ${CYAN}swarm --list-agents${NC}                # See all 245 agents"
echo ""
echo -e "${BOLD}Documentation:${NC} https://github.com/${REPO}"
echo ""
