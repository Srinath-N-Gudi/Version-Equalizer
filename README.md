# 🔄 VersionEqualizer

**A powerful desktop application to synchronize software versions across different systems**

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

## 📋 Overview

VersionEqualizer helps you match two versions of the same software across different PCs. When one system has a different software version from another, this application enables you to convert one version to match the other based on your selection.

### 🎯 Key Benefits
- **Version Synchronization**: Ensure identical software versions across multiple systems
- **Automated File Management**: Intelligently identify files that need copying or moving
- **Safe Operations**: Creates backups of extra files before making changes
- **User-Friendly Interface**: Beautiful dark theme with intuitive navigation
- **Progress Tracking**: Real-time progress updates for all operations

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- PySide6 library

### Quick Setup
```bash
# Install required dependency
pip install PySide6

# Run the application
python version_equalizer.py
```

## 🎮 How to Use

### 🏠 Main Interface
The application opens with two main options:
- **🔍 Checker**: Analyze and compare software versions
- **🔄 Match**: Apply changes to synchronize versions

---

## 🔍 CHECKER Section

### Step 1: Generate "To Version" Data
This creates a snapshot of your target software version (the version you want to match).

1. Click **"Checker"** from the home page
2. In the **"To Version"** panel:
   - Click **"Select Folder"**
   - Choose the folder containing your target software version
   - Wait for the scanning process to complete
   - Save the generated JSON file when prompted (e.g., `to_version.json`)

**What it does**: Recursively scans all files, calculates MD5 hashes, and creates a complete inventory.

### Step 2: Analyze "From Version"
This analyzes your current software version (the version you want to update).

1. In the **"From Version"** panel:
   - Click **"Load JSON File"** and select the `to_version.json` file
   - Click **"Select Folder"** and choose your current software folder
   - Wait for the scanning process to complete

### Step 3: Compare Versions
1. Click **"Proceed to Check"** button
2. The application will compare both versions and identify:
   - **Files to copy**: Missing files or files with different content
   - **Files to move**: Extra files that don't exist in the target version
3. Save the generated `convert.json` file when prompted

**Output**: A conversion plan showing exactly what needs to be changed.

---

## 🔄 MATCH Section

### Option 1: 📦 Prepare (For the "To Version" User)
Creates a ZIP package with all necessary files for updating.

1. Click **"Match"** from the home page
2. In the **"Prepare"** panel:
   - Click **"Select convert.json"** and choose your conversion file
   - Click **"Select To Version Folder"** and choose the target software folder
   - Click **"Create ZIP Package"**
3. Send the generated ZIP file to the person with the "From Version"

**What it does**: Packages all files marked for copying into a convenient ZIP archive.

### Option 2: ⚖️ Equalize (For the "From Version" User)
Applies the changes to match the target version.

1. In the **"Equalize"** panel:
   - Click **"Select convert.json"** and choose the conversion file
   - Click **"Select ZIP File"** and choose the received ZIP package
   - Click **"Select From Version Folder"** and choose your current software folder
   - Click **"Start Equalization"**

**What it does**:
- Extracts new/updated files from the ZIP to your software folder
- Moves extra files to `ExtraFiles_VersionEqualizer/` folder (safely backing them up)
- Your software version now matches the target version!

---

## 📁 File Operations Explained

### 🔄 Copy Operations
Files that are:
- Missing in your current version
- Different from the target version (different hash)

**Action**: These files are copied from the ZIP package to your software folder.

### 📦 Move Operations
Files that:
- Exist in your current version
- Don't exist in the target version

**Action**: These files are moved to `ExtraFiles_VersionEqualizer/` folder inside your software directory. This ensures nothing is permanently deleted.

---

## 🎨 Features

### Beautiful Dark Theme
- Modern dark interface that's easy on the eyes
- Gradient accent colors and smooth animations
- Professional typography and spacing

### Smart File Handling
- **UTF-8 Encoding Support**: Handles international file names correctly
- **MD5 Hashing**: Fast and reliable file comparison
- **Relative Paths**: Maintains proper directory structure
- **Error Recovery**: Continues processing even if individual files fail

### Progress Tracking
- Real-time progress bars for long operations
- Status updates showing current file being processed
- Estimated completion times

### Safety Features
- **Non-destructive**: Extra files are moved, not deleted
- **Backup Creation**: Original files are preserved in ExtraFiles folder
- **Validation**: Confirms operations before execution

---

## 📊 Example Workflow

### Scenario
You have **Software v1.0** on PC-A and **Software v2.0** on PC-B. You want PC-A to match PC-B.

### Process
1. **On PC-B** (has v2.0 - target version):
   - Use **Checker → To Version** to scan Software v2.0
   - Save `v2_snapshot.json`

2. **On PC-A** (has v1.0 - needs updating):
   - Use **Checker → From Version** with `v2_snapshot.json`
   - Scan your v1.0 folder
   - Generate `convert.json`

3. **On PC-B**:
   - Use **Match → Prepare** with `convert.json`
   - Create ZIP package and send to PC-A

4. **On PC-A**:
   - Use **Match → Equalize** with ZIP and `convert.json`
   - Your software is now v2.0!

---

## ⚠️ Important Notes

### File Safety
- Always backup your software before using VersionEqualizer
- Extra files are moved to `ExtraFiles_VersionEqualizer/` - check this folder before deleting
- The application preserves original file permissions and timestamps

### Performance
- Scanning large directories may take time
- MD5 calculation is performed on all files for accuracy
- Progress bars show real-time status

### Compatibility
- Works with any software or file collection
- Supports all file types and sizes
- Handles deeply nested directory structures

---

## 🐛 Troubleshooting

### Common Issues

**"ImportError: cannot import name 'QSignal'"**
- Solution: Make sure you have PySide6 installed: `pip install PySide6`

**"Permission denied" errors**
- Solution: Run as administrator or ensure you have write permissions
- Check that files aren't currently in use by other applications

**Scanning takes too long**
- This is normal for large software installations
- The application shows progress - let it complete
- Consider excluding unnecessary folders if possible

**ZIP file too large**
- Large updates may create big ZIP files
- Use file compression tools if needed for transfer
- Consider transferring over local network instead of internet

---

## 🔧 Technical Details

### File Hashing
- Uses MD5 algorithm for speed and reliability
- Processes files in 4KB chunks for memory efficiency
- Handles binary and text files equally

### Directory Structure
```
Your Software Folder/
├── [Updated files from ZIP]
├── [Existing unchanged files]
└── ExtraFiles_VersionEqualizer/
    └── [Moved extra files with original structure]
```

### Supported Formats
- **JSON files**: UTF-8 encoded with proper formatting
- **ZIP archives**: Standard ZIP compression
- **All file types**: No restrictions on file formats or sizes

---

## 💡 Tips for Best Results

1. **Close the software** before running VersionEqualizer
2. **Scan clean installations** for best accuracy
3. **Use descriptive names** for JSON files (e.g., `software_v2.1_snapshot.json`)
4. **Keep conversion files** for future reference
5. **Test on a copy first** if dealing with critical software

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure all prerequisites are installed
3. Verify file permissions and available disk space
4. Review any error messages for specific guidance

---

**🎉 Enjoy seamless software version synchronization with VersionEqualizer!**