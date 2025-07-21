# 🔒 GitHub Repository Rulesets

This directory contains pre-configured GitHub ruleset JSON files that you can import to automatically set up professional repository protection and quality control.

## 📋 **Available Rulesets**

### 1. **`simple-ruleset.json`** (Recommended for Start)
**Best for**: New repositories, solo developers, getting started
- ✅ Basic branch protection for `main` branch
- ✅ Requires pull requests with 1 approval
- ✅ Prevents force pushes and deletions
- ✅ Requires conversation resolution

### 2. **`audio-project-ruleset.json`** (Comprehensive)
**Best for**: Mature projects, team collaboration, production ready
- ✅ All basic protections
- ✅ Audio-specific file restrictions (prevents large audio files)
- ✅ Commit message conventions with emojis
- ✅ File size and path length limits
- ✅ Restricted file extensions

### 3. **`ruleset.json`** (Enterprise-Level)
**Best for**: Large teams, enterprise environments, strict governance
- ✅ Conventional commit patterns
- ✅ Email validation patterns
- ✅ Maximum file restrictions
- ✅ Advanced bypass controls

## 🚀 **How to Import Rulesets**

### **Method 1: GitHub Web Interface**
1. Go to your repository: `https://github.com/DineshPadhan/real-time-audio-safety-system`
2. Click **"Settings"** → **"Rules"** → **"Rulesets"**
3. Click **"New ruleset"** → **"Import a ruleset"**
4. Copy and paste the content of your chosen JSON file
5. Click **"Create"**

### **Method 2: GitHub CLI** (Advanced)
```bash
# Install GitHub CLI first: https://cli.github.com/
gh auth login
gh repo set-default DineshPadhan/real-time-audio-safety-system

# Import simple ruleset
gh api repos/DineshPadhan/real-time-audio-safety-system/rulesets \
  --method POST \
  --input .github/simple-ruleset.json
```

### **Method 3: REST API** (For Automation)
```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/DineshPadhan/real-time-audio-safety-system/rulesets \
  -d @.github/simple-ruleset.json
```

## 🎯 **Recommended Setup Progression**

### **Phase 1: Start Simple**
1. Import **`simple-ruleset.json`**
2. Test with a few pull requests
3. Ensure team is comfortable with the workflow

### **Phase 2: Add Quality Controls**
1. Upgrade to **`audio-project-ruleset.json`**
2. Train team on commit message conventions
3. Set up file size and type restrictions

### **Phase 3: Enterprise Ready**
1. Implement **`ruleset.json`** for full governance
2. Add status checks and CI/CD integration
3. Configure advanced bypass controls

## 🔧 **Customization Guide**

### **Commit Message Patterns**
Current pattern for audio projects:
```
🎧(headphone): Add connection verification system
🔧(config): Update audio device detection
🐛(bug): Fix PyAudio initialization error
✨(feature): Implement real-time FFT visualization
```

### **Supported Emoji Prefixes**
- 🎧 Audio/headphone related changes
- 🔧 Configuration and setup
- 🐛 Bug fixes  
- ✨ New features
- 📚 Documentation
- 🎯 Performance improvements
- ⚡ Optimization
- 🛡️ Safety and security
- 🔊 Audio processing
- 🎵 Audio file handling

### **File Restrictions Explained**
- **Audio files**: Prevented except `song.mp3` (sample file)
- **Build artifacts**: `.pyc`, `.exe`, `.dll` files blocked
- **Dependencies**: `node_modules`, `__pycache__`, `.venv` blocked
- **Temporary files**: `.tmp`, `.log`, backup files blocked

## 🛡️ **Security Features**

### **File Size Limits**
- Maximum file size: 50MB (audio-project) / 100MB (enterprise)
- Prevents accidental large file commits
- Keeps repository lightweight

### **Path Length Limits**
- Maximum path length: 255 characters
- Ensures cross-platform compatibility
- Prevents deep nesting issues

### **Email Validation**
- Ensures proper developer email formats
- Supports common providers (Gmail, Outlook, etc.)
- Maintains commit authenticity

## 📊 **Benefits of Using Rulesets**

### **Quality Assurance**
- ✅ Consistent code review process
- ✅ Standardized commit messages
- ✅ Prevented problematic files
- ✅ Maintained repository hygiene

### **Team Collaboration**
- ✅ Clear contribution guidelines
- ✅ Automated quality checks
- ✅ Reduced manual oversight
- ✅ Professional development workflow

### **Project Integrity**
- ✅ Protected main branch
- ✅ Prevented force pushes
- ✅ Required conversation resolution
- ✅ Maintained project history

## 🚨 **Troubleshooting**

### **Common Issues**
1. **Ruleset import fails**: Check JSON syntax with a validator
2. **Too restrictive**: Start with `simple-ruleset.json` first
3. **Commit messages rejected**: Follow the emoji pattern convention
4. **File upload blocked**: Check file size and extension restrictions

### **Bypass Options**
- Repository admins can bypass rules when necessary
- Emergency procedures maintain in documentation
- Temporary rule disabling for urgent fixes

## 🎯 **Next Steps**

1. **Import your chosen ruleset**
2. **Test with a practice pull request**
3. **Document team workflow**
4. **Set up status checks (CI/CD)**
5. **Configure notifications**

Your repository will now have enterprise-level protection and quality control! 🎧🔒
