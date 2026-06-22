# How to Share and Run the AI Virtual Mouse Project

Follow these exact steps to share your project with your friends and get it running on their Windows PCs.

---

## Part 1: Packaging the Project (On Your PC)

Before sending the file, you need to clean out temporary folders that make the project file huge and won't work on your friend's PC.

1. **Open your project folder:** Go to your `Downloads` folder and open `Gestures and Voice based Desktop interacton\opencv-ai-virtual-mouse-main`.
2. **Delete `venv`:** Find the folder named `venv` inside the project. Right-click it and select **Delete**. *(This folder is massive and contains your personal Python installation, which will crash on another PC.)*
3. **Delete `__pycache__`:** Find the folder named `__pycache__`. Right-click it and select **Delete**.
4. **Zip the folder:** Go back one step so you can see the `opencv-ai-virtual-mouse-main` folder. Right-click it and choose **Compress to ZIP file**.
5. **Send the ZIP file:** Send the newly created `.zip` file to your friend via email, Google Drive, WhatsApp, or a flash drive.

---

## Part 2: Setting up their PC (On Your Friend's PC)

Your friend must complete these one-time installation steps before they can run the project.

1. **Download Python 3.10:** 
   - Tell them to go to the official Python website and download **Python 3.10.x** for Windows (do not use Python 3.11 or 3.12, they will cause errors).
   - *CRITICAL STEP:* During the Python installation, tell them they **must** check the box that says **"Add Python 3.10 to PATH"** at the bottom of the first screen before clicking Install.
2. **Extract the Project:**
   - Tell them to download the `.zip` file you sent them.
   - Right-click the `.zip` file and select **Extract All...** to unzip it to a folder (like their Desktop or Downloads folder).
3. **Open the Terminal:**
   - Open the unzipped folder (`opencv-ai-virtual-mouse-main`).
   - Click inside the address bar at the very top of the folder window (where it says the folder path like `C:\Users\...`).
   - Type `cmd` and press **Enter**. This will open a black command prompt window directly in the project folder.

---

## Part 3: Installing the Libraries (On Your Friend's PC)

Now they will use the command prompt to automatically install all the necessary code tools for the magic to happen.

1. In the black `cmd` terminal they just opened, tell them to type the following exact command and hit Enter:
   ```bash
   pip install -r requirements.txt
   ```
2. Wait for the installation to finish. They will see a lot of text scrolling on the screen downloading `opencv-python`, `mediapipe`, `SpeechRecognition`, etc. This might take 2-4 minutes depending on their internet speed.
3. Wait until it clearly says it finished and returns them to the normal typing prompt.

---

## Part 4: Running the Magic Mouse (On Your Friend's PC)

Once installed, they are ready to run the project anytime!

1. In that same `cmd` terminal, tell them to type the following exact command and hit Enter:
   ```bash
   python AiVirtualMouseProject.py
   ```
2. The program will take a few seconds to start up. 
3. *Note:* Make sure they know they need a working **webcam** (for their hands) and a working **microphone** (for their voice). They must also be using a **Windows PC**.
4. A window will pop up showing their camera feed, and the AI Virtual Mouse is now active! They can now test gestures and voice commands.
