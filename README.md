# Agent Swarm (Enhanced)

Agent Swarm is an engine-agnostic multi-agent orchestration system, now enhanced with the power and UI/UX of Claude Code.

## 🚀 Key Features
- **Engine-agnostic:** Works with any CLI agent (Claude, Gemini, Kilo, etc.).
- **245+ Specialized Agents:** Academic, Creative, Engineering, Management, and more.
- **Enhanced UI/UX:** Built with React/Ink for a beautiful, responsive CLI experience.
- **Smart Tools:** Includes Bash, File Editing, Grep, Glob, and more.
- **Parallel Orchestration:** Dispatch multiple agents simultaneously for complex goals.

## 📦 Installation
```bash
./install.sh
```
Or install via npm:
```bash
npm install -g @anas.abubakar/swarm
```

## 🛠 Usage
Launch the interactive CLI:
```bash
swarm
```
Run the multi-agent orchestrator:
```bash
swarm "Build a full-stack e-commerce site"
```
List available agents:
```bash
swarm --agents
```

## 🚢 Publishing to NPM
To publish your changes to npm:

1. **Login to npm:**
   ```bash
   npm login
   ```
2. **Update version:** (already updated to 4.0.0 in package.json)
3. **Publish:**
   ```bash
   npm publish --access public
   ```

## 📄 License
MIT
