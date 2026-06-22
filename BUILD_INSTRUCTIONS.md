# 🚀 Build Instructions - AI Virtual Mouse to .EXE

## Quick Start (Easiest Method)

1. **Double-click** `build_exe.bat`
2. Wait 5-10 minutes for the build to complete
3. Your .exe will be in: `dist\AiVirtualMouse\AiVirtualMouse.exe`

---

## Manual Build (Alternative)

If you prefer to build manually or if the batch file doesn't work:

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Clean Previous Builds (Optional)
```bash
rmdir /s /q build
rmdir /s /q dist
```

### Step 3: Build the Executable
```bash
pyinstaller --clean AiVirtualMouse.spec
```

### Step 4: Find Your Executable
Navigate to: `dist\AiVirtualMouse\AiVirtualMouse.exe`

---

## 📦 Distributing Your .EXE

### Option 1: Send the Entire Folder (Recommended)
1. Zip the entire `dist\AiVirtualMouse\` folder
2. Send it to anyone
3. They extract and run `AiVirtualMouse.exe`

**Folder Size:** ~400-800 MB (includes all dependencies)

### Option 2: Create a Single .EXE File (Advanced)
If you want a single file instead of a folder:

1. Open `AiVirtualMouse.spec`
2. Find the `EXE` section
3. Change `exclude_binaries=True` to `exclude_binaries=False`
4. Change the section from:
   ```python
   exe = EXE(
       pyz,
       a.scripts,
       [],
       exclude_binaries=True,
       ...
   ```
   to:
   ```python
   exe = EXE(
       pyz,
       a.scripts,
       a.binaries,
       a.zipfiles,
       a.datas,
       [],
       name='AiVirtualMouse',
       ...
   ```
5. Remove the entire `COLLECT` section at the bottom
6. Rebuild: `pyinstaller --clean AiVirtualMouse.spec`

**Note:** Single file is larger (~800MB-1GB) and slower to start, but easier to distribute.

---

## ✅ Testing Your .EXE

1. Navigate to `dist\AiVirtualMouse\`
2. Double-click `AiVirtualMouse.exe`
3. Allow camera access if prompted
4. The console window will show startup messages
5. Camera window should appear
6. Test hand tracking gestures

---

## 🐛 Troubleshooting

### Issue: "Failed to execute script"
- Make sure `hand_landmarker.task` file is in the project folder before building
- Rebuild with `--clean` flag

### Issue: Camera not working
- Test the original Python script first: `python AiVirtualMouseProject.py`
- Check Windows camera permissions
- Try running as Administrator

### Issue: "Module not found" error
- Install missing packages: `pip install -r requirements.txt`
- Rebuild the .exe

### Issue: Build takes forever
- This is normal! OpenCV and MediaPipe are large libraries
- First build: 5-10 minutes
- Subsequent builds: 2-5 minutes

### Issue: .exe is too large
- This is expected (400-800 MB)
- Consider using cloud storage (Google Drive, WeTransfer) for sharing

---

## 📋 What Gets Included in the .EXE

✅ Your Python code (compiled to bytecode - not readable)  
✅ HandTrackingModule.py (compiled - not readable)  
✅ hand_landmarker.task (AI model file)  
✅ OpenCV libraries  
✅ MediaPipe libraries  
✅ All dependencies (numpy, autopy, pycaw, etc.)  
✅ Python runtime  

🔒 **Your source code is NOT readable in the .exe**

---

## 💡 Tips for Recipients

When you send the .exe to someone:

1. **Include these instructions:**
   - Extract the ZIP file completely
   - Run `AiVirtualMouse.exe`
   - Allow camera access when prompted
   - Administrator rights may be needed for mouse control

2. **System Requirements:**
   - Windows 10/11
   - Webcam
   - 2GB+ free RAM
   - No Python installation required

3. **Antivirus Warning:**
   - Some antivirus software may flag the .exe (false positive)
   - This is common with PyInstaller executables
   - Add an exception if needed

---

## 🎯 Next Steps

After building successfully:
1. Test the .exe on your machine
2. Test on another PC (without Python) if possible
3. Zip the `dist\AiVirtualMouse\` folder
4. Send to your recipient

**Build Date:** Check the date on your dist folder after building
