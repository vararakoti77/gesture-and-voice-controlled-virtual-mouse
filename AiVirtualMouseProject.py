import cv2
import numpy as np
import HandTrackingModule as htm
import time
import autopy
import math
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CoInitialize, CoUninitialize, CLSCTX_ALL
import pyautogui
import os 
import threading
import webbrowser
from VoiceController import VoiceController
import screen_brightness_control as sbc

##########################
wCam, hCam = 640, 480
frameR = 100  # Frame Reduction
smoothening = 7
#########################

# Initialize volume control
try:
    CoInitialize()
    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    volume = cast(interface, POINTER(IAudioEndpointVolume))
    volRange = volume.GetVolumeRange()
    minVol = volRange[0]
    maxVol = volRange[1]
    volume_control_available = True
except Exception as e:
    print(f"Warning: Volume control not available: {e}")
    volume_control_available = False
    minVol = -65.25
    maxVol = 0.0
    volume = None

pTime = 0
plocX, plocY = 0, 0
clocX, clocY = 0, 0

# Additional variables for new features
click_count = 0
last_click_time = 0
drag_mode = False
prev_y = 0
scroll_sensitivity = 10
pinch_click_enabled = True
last_pinch_time = 0
gesture_cooldown = 0.3  # Cooldown between gestures
last_gesture_time = 0
zoom_initial_distance = 0
zoom_mode = False
brightness_mode = False
initial_brightness = 50
swipe_start_x = 0
swipe_threshold = 150
palm_history = []
screenshot_taken = False
last_voice_command = ""
last_voice_command_time = 0
last_voice_confidence = 0.0

# UI Toggle state
gestures_enabled = True
voice_enabled = True

def on_mouse_click(event, x, y, flags, param):
    global gestures_enabled, voice_enabled
    if event == cv2.EVENT_LBUTTONDOWN:
        # Check if click is inside GESTURE toggle button (top right area)
        if wCam - 260 <= x <= wCam - 140 and 10 <= y <= 40:
            gestures_enabled = not gestures_enabled
            print(f"Gestures Enabled: {gestures_enabled}")
        # Check if click is inside VOICE toggle button
        elif wCam - 130 <= x <= wCam - 10 and 10 <= y <= 40:
            voice_enabled = not voice_enabled
            print(f"Voice Enabled: {voice_enabled}")

cap = None
for i in range(3):  # Try camera indices 0, 1, 2
    print(f"Trying camera index {i}...")
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, test_frame = cap.read()
        if ret and test_frame is not None:
            print(f"Camera found at index {i}")
            break
        cap.release()
    cap = None

if cap is None:
    print("Error: No camera found!")
    exit()

print("Camera initialized successfully")

# Create screenshots folder if it doesn't exist
screenshots_folder = "screenshots"
if not os.path.exists(screenshots_folder):
    os.makedirs(screenshots_folder)
    print(f"Created folder: {screenshots_folder}")

cap.set(3, wCam)
cap.set(4, hCam)
detector = htm.handDetector(maxHands=1)
wScr, hScr = autopy.screen.size()
print(f"Screen size: {wScr} x {hScr}")

# Initialize Voice Controller in background
vc = VoiceController()
vc_thread = threading.Thread(target=vc.initialize, daemon=True)
vc_thread.start()

# Create and position the window
cv2.namedWindow("AI Virtual Mouse", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("AI Virtual Mouse", on_mouse_click)
cv2.resizeWindow("AI Virtual Mouse", wCam, hCam)
# Position window on the right side of screen
window_x = int(wScr - wCam - 50)  # 50 pixels from right edge
window_y = 50  # 50 pixels from top
cv2.moveWindow("AI Virtual Mouse", window_x, window_y)
# Keep window on top
cv2.setWindowProperty("AI Virtual Mouse", cv2.WND_PROP_TOPMOST, 1)

def is_cooldown_over(last_time, cooldown=0.3):
    """Check if cooldown period is over"""
    return time.time() - last_time > cooldown

def draw_ai_assistant_hud(img, mode, gesture, voice_cmd, voice_conf):
    """Draw a unified, semi-transparent HUD containing AI Assistant information and toggle buttons"""
    overlay = img.copy()
    
    # 1. Main HUD Box (Top Left)
    cv2.rectangle(overlay, (10, 10), (350, 130), (0, 0, 0), -1)
    
    # Text in Main HUD
    cv2.putText(overlay, f"Mode: {mode if mode else 'IDLE'}", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(overlay, f"Gesture: {gesture if gesture else 'None'}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    cv2.putText(overlay, f"Voice: {voice_cmd if voice_cmd else 'Listening...'}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    cv2.putText(overlay, f"Confidence: {int(voice_conf * 100)}%" if voice_conf else "Confidence: --%", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    
    # 2. Toggle Buttons (Top Right)
    global gestures_enabled, voice_enabled
    
    # Gesture Button
    g_color = (0, 200, 0) if gestures_enabled else (0, 0, 200)
    g_text = "GESTURE: ON" if gestures_enabled else "GESTURE: OFF"
    cv2.rectangle(overlay, (wCam - 260, 10), (wCam - 140, 40), g_color, -1)
    cv2.putText(overlay, g_text, (wCam - 250, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # Voice Button
    v_color = (0, 200, 0) if voice_enabled else (0, 0, 200)
    v_text = "VOICE: ON" if voice_enabled else "VOICE: OFF"
    cv2.rectangle(overlay, (wCam - 130, 10), (wCam - 10, 40), v_color, -1)
    cv2.putText(overlay, v_text, (wCam - 120, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # Apply transparency
    img = cv2.addWeighted(overlay, 0.7, img, 0.3, 0)
    return img

while True:
    # 1. Find hand Landmarks
    success, img = cap.read()
    
    # Check if frame is captured successfully
    if not success or img is None:
        print("Failed to capture frame from camera")
        continue
    
    img = cv2.flip(img, 1)  # Flip for mirror effect
    img = detector.findHands(img)
    lmList, bbox = detector.findPosition(img)

    current_mode = "IDLE"
    current_gesture = ""

    # 2. Get finger positions
    if gestures_enabled and len(lmList) != 0:
        x1, y1 = lmList[8][1:]  # Index finger tip
        x2, y2 = lmList[12][1:]  # Middle finger tip
        x3, y3 = lmList[16][1:]  # Ring finger tip
        x4, y4 = lmList[20][1:]  # Pinky finger tip
        x_thumb, y_thumb = lmList[4][1:]  # Thumb tip

        # 3. Check which fingers are up
        fingers = detector.fingersUp()
        
        # Get palm center for advanced gestures
        palm_center = detector.getPalmCenter()
        
        current_time = time.time()

        # ============ GESTURE DETECTION ============
        
        # GESTURE 1: PINCH TO CLICK (Thumb + Index Pinch)
        if detector.isPinching(threshold=40, finger_tip_id=8) and is_cooldown_over(last_pinch_time, 0.4):
            current_mode = "PINCH CLICK"
            current_gesture = "Thumb + Index Pinch"
            cv2.circle(img, (x_thumb, y_thumb), 20, (0, 255, 0), cv2.FILLED)
            autopy.mouse.click()
            last_pinch_time = current_time
            time.sleep(0.2)
        
        # GESTURE 2: MOUSE MOVEMENT - Only Index Finger Up
        elif fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0 and fingers[0] == 0:
            current_mode = "MOUSE MOVE"
            current_gesture = "1 Finger (Index)"
            
            # Convert Coordinates
            x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
            y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))
            
            # Smoothen Values
            clocX = plocX + (x3 - plocX) / smoothening
            clocY = plocY + (y3 - plocY) / smoothening

            # Move Mouse
            autopy.mouse.move(clocX, clocY)
            cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            plocX, plocY = clocX, clocY

        # GESTURE 3: LEFT CLICK or DRAG - Index and Middle Fingers Up
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0 and fingers[0] == 0:
            length, img, lineInfo = detector.findDistance(8, 12, img)
            
            if length < 40 and is_cooldown_over(last_click_time, 0.4):
                # Close together = Click
                current_mode = "LEFT CLICK"
                current_gesture = "2 Fingers Pinched"
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                autopy.mouse.click()
                last_click_time = current_time
                time.sleep(0.2)
            else:
                # Far apart = Select/Drag mode
                current_mode = "SELECTION MODE"
                current_gesture = "2 Fingers (Index, Middle)"
                if not drag_mode:
                    drag_mode = True
                    autopy.mouse.toggle(autopy.mouse.Button.LEFT, True)
                
                # Move while selecting
                x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))
                clocX = plocX + (x3 - plocX) / smoothening
                clocY = plocY + (y3 - plocY) / smoothening
                autopy.mouse.move(clocX, clocY)
                plocX, plocY = clocX, clocY

        # GESTURE 4: RIGHT CLICK - Index, Middle, and Ring Fingers Up
        elif fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
            current_mode = "RIGHT CLICK"
            current_gesture = "3 Fingers"
            
            length, img, lineInfo = detector.findDistance(8, 16, img)
            
            if length < 50 and is_cooldown_over(last_click_time, 0.5):
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 0, 255), cv2.FILLED)
                autopy.mouse.click(autopy.mouse.Button.RIGHT)
                last_click_time = current_time
                time.sleep(0.3)

        # GESTURE 5a: SCROLL UP - Middle + Ring fingers up
        elif fingers[1] == 0 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0 and fingers[0] == 0:
            current_mode = "SCROLL UP"
            current_gesture = "Middle + Ring Fingers"
            pyautogui.scroll(80)
            time.sleep(0.05)

        # GESTURE 5b: SCROLL DOWN - Ring + Pinky fingers up
        elif fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 1 and fingers[4] == 1 and fingers[0] == 0:
            current_mode = "SCROLL DOWN"
            current_gesture = "Ring + Pinky Fingers"
            pyautogui.scroll(-80)
            time.sleep(0.05)

        # GESTURE 6: VOLUME CONTROL - Thumb and Pinky Up
        elif fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 1:
            if volume_control_available and volume is not None:
                current_mode = "VOLUME CONTROL"
                current_gesture = "Thumb + Pinky (Shaka)"
                
                length, img, lineInfo = detector.findDistance(4, 20, img)
                
                # Convert distance to volume
                vol = np.interp(length, [50, 200], [minVol, maxVol])
                volBar = np.interp(length, [50, 200], [400, 150])
                volPer = np.interp(length, [50, 200], [0, 100])
                
                volume.SetMasterVolumeLevel(vol, None)
                
                # Draw volume bar
                cv2.rectangle(img, (50, 150), (85, 400), (255, 0, 0), 3)
                cv2.rectangle(img, (50, int(volBar)), (85, 400), (255, 0, 0), cv2.FILLED)
                cv2.putText(img, f'{int(volPer)}%', (40, 450), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 3)

        # GESTURE 8: SCREENSHOT - All Five Fingers Up (Palm Open)
        elif detector.isPalmOpen() and is_cooldown_over(last_gesture_time, 1.5):
            current_mode = "SCREENSHOT"
            current_gesture = "Open Palm"
            screenshot_path = os.path.join(screenshots_folder, f'screenshot_{int(time.time())}.png')
            pyautogui.screenshot(screenshot_path)
            last_gesture_time = current_time
            time.sleep(0.5)

        # GESTURE 9: ZOOM - Thumb, Index, Middle Up (Spread Thumb & Middle)
        elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
            length, img, lineInfo = detector.findDistance(4, 12, img)  # Distance between thumb and middle
            
            current_mode = "ZOOM MODE"
            current_gesture = "3 Fingers Up (Spread)"
            cv2.circle(img, (lineInfo[4], lineInfo[5]), 12, (255, 255, 0), cv2.FILLED)
            
            if zoom_initial_distance == 0:
                zoom_initial_distance = length
            else:
                delta = length - zoom_initial_distance
                # Show distance for feedback
                cv2.putText(img, f"Spread: {int(length)}", (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                if abs(delta) > 12:  # Very sensitive threshold
                    if delta > 0:
                        pyautogui.hotkey('ctrl', '=')
                    else:
                        pyautogui.hotkey('ctrl', '-')
                    zoom_initial_distance = length
                    time.sleep(0.12)

        # GESTURE 10: PAUSE/PLAY - Index, Middle, Ring, Pinky Up (Four fingers)
        elif fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
            if is_cooldown_over(last_gesture_time, 1.0):
                current_mode = "PLAY/PAUSE"
                current_gesture = "4 Fingers Up"
                pyautogui.press('playpause')
                last_gesture_time = current_time
                time.sleep(0.3)

        # GESTURE 10: BRIGHTNESS CONTROL - Thumb and Ring Finger
        elif fingers[0] == 1 and fingers[1] == 0 and fingers[2] == 0 and fingers[3] == 1 and fingers[4] == 0:
            current_mode = "BRIGHTNESS"
            current_gesture = "Thumb + Ring Pinch"
            
            current_distance = detector.getPinchDistance(finger_tip_id=16)
            brightness_val = np.interp(current_distance, [30, 200], [0, 100])
            
            cv2.putText(img, f"Brightness: {int(brightness_val)}%", (50, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 200, 255), 2)
            
            # Draw brightness bar
            cv2.rectangle(img, (500, 150), (535, 400), (100, 100, 100), 3)
            bright_bar = np.interp(brightness_val, [0, 100], [400, 150])
            cv2.rectangle(img, (500, int(bright_bar)), (535, 400), (100, 200, 255), cv2.FILLED)

        # Stop dragging when no drag gesture
        elif drag_mode:
            drag_mode = False
            autopy.mouse.toggle(autopy.mouse.Button.LEFT, False)

        # Reset zoom when gesture changes
        else:
            zoom_initial_distance = 0
            prev_y = 0
            
    # Handle Voice Commands (outside if len(lmList) to allow voice commands when hand is not visible or visible)
    if vc.initialized and not vc.is_running:
        vc.start_listening()
        
    voice_command_tuple = vc.get_latest_command() if voice_enabled else ()
    if voice_command_tuple:
        # voice_command_tuple is now (command_string, optional_argument)
        voice_command = voice_command_tuple[0]
        cmd_arg = voice_command_tuple[1]
        
        print(f"Executing voice command: {voice_command} with args: {cmd_arg}")
        last_voice_command = voice_command if not cmd_arg else f"{voice_command} {cmd_arg}"
        last_voice_command_time = time.time()
        
        # 1. CORE MOUSE/UI
        if voice_command == "left_click":
            autopy.mouse.click()
        elif voice_command == "right_click":
            autopy.mouse.click(autopy.mouse.Button.RIGHT)
        elif voice_command == "scroll_up":
            pyautogui.scroll(120)
        elif voice_command == "scroll_down":
            pyautogui.scroll(-120)
        elif voice_command == "screenshot":
            screenshot_path = os.path.join(screenshots_folder, f'screenshot_{int(time.time())}.png')
            pyautogui.screenshot(screenshot_path)
        elif voice_command == "zoom_in":
            pyautogui.hotkey('ctrl', '=')
        elif voice_command == "zoom_out":
            pyautogui.hotkey('ctrl', '-')
            
        # 2. MEDIA & SETTINGS
        elif voice_command == "play_pause":
            pyautogui.press('playpause')
        elif voice_command == "volume_up" and volume_control_available and volume is not None:
            try:
                current_vol = volume.GetMasterVolumeLevel()
                volume.SetMasterVolumeLevel(min(current_vol + 5.0, maxVol), None)
            except:
                pass
        elif voice_command == "volume_down" and volume_control_available and volume is not None:
            try:
                current_vol = volume.GetMasterVolumeLevel()
                volume.SetMasterVolumeLevel(max(current_vol - 5.0, minVol), None)
            except:
                pass
        elif voice_command == "brightness_up":
            try:
                current_brightness = sbc.get_brightness(display=0)[0]
                sbc.set_brightness(min(current_brightness + 10, 100), display=0)
            except:
                pass
        elif voice_command == "brightness_down":
            try:
                current_brightness = sbc.get_brightness(display=0)[0]
                sbc.set_brightness(max(current_brightness - 10, 0), display=0)
            except:
                pass
                
        # 3. MOVEMENT
        elif voice_command == "move_up":
            pyautogui.move(0, -40)
        elif voice_command == "move_down":
            pyautogui.move(0, 40)
        elif voice_command == "move_left":
            pyautogui.move(-40, 0)
        elif voice_command == "move_right":
            pyautogui.move(40, 0)
            
        # 4. WINDOWS OS & APP LAUNCHING
        elif voice_command == "desktop":
            pyautogui.hotkey('win', 'd')
        elif voice_command == "minimize":
            pyautogui.hotkey('win', 'down')
        elif voice_command == "maximize":
            pyautogui.hotkey('win', 'up')
        elif voice_command == "new_window":
            pyautogui.hotkey('ctrl', 'n')
        elif voice_command == "new_tab":
            pyautogui.hotkey('ctrl', 't')
        elif voice_command == "next_window":
            pyautogui.hotkey('alt', 'tab')
        elif voice_command == "previous_window":
            pyautogui.hotkey('alt', 'shift', 'tab')
        elif voice_command == "switch_window":
            pyautogui.hotkey('alt', 'tab')
        elif voice_command == "next_tab":
            pyautogui.hotkey('ctrl', 'tab')
        elif voice_command == "previous_tab":
            pyautogui.hotkey('ctrl', 'shift', 'tab')
        elif voice_command == "close_window":
            pyautogui.hotkey('alt', 'f4')
        elif voice_command == "double_click":
            pyautogui.doubleClick()
        elif voice_command == "open_app":
            def search_and_open_app(name):
                pyautogui.press('win')
                time.sleep(0.5)
                pyautogui.write(name)
                time.sleep(1.0)
                pyautogui.press('enter')
            threading.Thread(target=search_and_open_app, args=(cmd_arg,), daemon=True).start()
            
        elif voice_command == "open_named_file" and cmd_arg:
            def search_and_open_direct_file(name):
                user_dirs = [
                    os.path.expanduser("~/Desktop"),
                    os.path.expanduser("~/Documents"),
                    os.path.expanduser("~/Downloads"),
                    os.path.expanduser("~/Pictures")
                ]
                
                target_name = name.lower()
                found_path = None
                
                for d in user_dirs:
                    if not os.path.exists(d): continue
                    for root, dirs, files in os.walk(d):
                        for file in files:
                            file_base = os.path.splitext(file)[0].lower()
                            if target_name in file_base or target_name == file.lower():
                                found_path = os.path.join(root, file)
                                break
                        if found_path: break
                    if found_path: break
                        
                if found_path:
                    try:
                        os.startfile(found_path)
                    except Exception as e:
                        print(f"Error opening file: {e}")
                else:
                    # Gracefully fail instead of using the Start Menu which triggers a Bing Web Search
                    os.system(f'mshta vbscript:Execute("msgbox ""Could not find any file named: {name}"",0,""AI Virtual Mouse"":close")')
                    
            threading.Thread(target=search_and_open_direct_file, args=(cmd_arg,), daemon=True).start()

        elif voice_command == "open_folder" and cmd_arg:
            def search_and_open_direct_folder(name):
                user_dirs = [
                    os.path.expanduser("~/Desktop"),
                    os.path.expanduser("~/Documents"),
                    os.path.expanduser("~/Downloads"),
                    os.path.expanduser("~/Pictures")
                ]
                
                target_name = name.lower()
                found_path = None
                
                for d in user_dirs:
                    if not os.path.exists(d): continue
                    for root, dirs, files in os.walk(d):
                        for dir_name in dirs:
                            if target_name in dir_name.lower() or target_name == dir_name.lower():
                                found_path = os.path.join(root, dir_name)
                                break
                        if found_path: break
                    if found_path: break
                        
                if found_path:
                    try:
                        import subprocess
                        subprocess.Popen(f'explorer "{found_path}"')
                    except Exception as e:
                        print(f"Error opening folder: {e}")
                else:
                    # Gracefully fail instead of using the Start Menu which triggers a Bing Web Search
                    os.system(f'mshta vbscript:Execute("msgbox ""Could not find any folder named: {name}"",0,""AI Virtual Mouse"":close")')
                    
            threading.Thread(target=search_and_open_direct_folder, args=(cmd_arg,), daemon=True).start()
            
        elif voice_command == "whatsapp_chat" and cmd_arg:
            def search_wa_chat(name):
                os.system("start whatsapp:")
                time.sleep(1.5)
                pyautogui.hotkey('ctrl', 'f')
                time.sleep(0.5)
                pyautogui.write(name)
                time.sleep(1.0)
                pyautogui.press('enter')
            threading.Thread(target=search_wa_chat, args=(cmd_arg,), daemon=True).start()
            
        elif voice_command == "open_url" and cmd_arg:
            webbrowser.open(cmd_arg)
            
        # 5. TYPING & WEB SEARCHING
        elif voice_command == "type_text" and cmd_arg:
            pyautogui.write(cmd_arg)
        elif voice_command == "search_web" and cmd_arg:
            webbrowser.open(f"https://www.google.com/search?q={cmd_arg}")
        elif voice_command == "press_key" and cmd_arg:
            if cmd_arg in ["enter", "backspace", "space", "delete"]:
                pyautogui.press(cmd_arg)
            else:
                pyautogui.press(cmd_arg) # Fallback to hit exactly what was sent
            
        # 5b. EDITING & TEXT MANIPULATION
        elif voice_command == "save":
            pyautogui.keyDown('ctrl')
            pyautogui.press('s')
            pyautogui.keyUp('ctrl')
        elif voice_command == "select_all":
            pyautogui.keyDown('ctrl')
            pyautogui.press('a')
            pyautogui.keyUp('ctrl')
        elif voice_command == "find":
            pyautogui.keyDown('ctrl')
            pyautogui.press('f')
            pyautogui.keyUp('ctrl')
        elif voice_command == "copy":
            pyautogui.keyDown('ctrl')
            pyautogui.press('c')
            pyautogui.keyUp('ctrl')
        elif voice_command == "paste":
            pyautogui.keyDown('ctrl')
            pyautogui.press('v')
            pyautogui.keyUp('ctrl')
        elif voice_command == "cut":
            pyautogui.keyDown('ctrl')
            pyautogui.press('x')
            pyautogui.keyUp('ctrl')
        elif voice_command == "undo":
            pyautogui.keyDown('ctrl')
            pyautogui.press('z')
            pyautogui.keyUp('ctrl')
        elif voice_command == "redo":
            pyautogui.keyDown('ctrl')
            pyautogui.press('y')
            pyautogui.keyUp('ctrl')
        elif voice_command == "refresh":
            pyautogui.press('f5')
            
        # 6. CRITICAL POWER
        elif voice_command == "shutdown":
            os.system("shutdown /s /t 5")
        elif voice_command == "restart":
            os.system("shutdown /r /t 5")
            
        # 7. EXIT
        elif voice_command == "quit":  
            break


    # 12. Frame Rate
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)

    # 13. Instructions
    cv2.putText(img, "Press 'q' to quit", (20, hCam - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    # Window status indicator
    img = draw_ai_assistant_hud(img, current_mode, current_gesture, last_voice_command, vc.latest_voice_confidence if hasattr(vc, 'latest_voice_confidence') else 0.0)
    cv2.putText(img, "📌 ALWAYS ON TOP", (wCam - 200, hCam - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 14. Display
    cv2.imshow("AI Virtual Mouse", img)
    
    # Keep window visible and on top (always)
    cv2.setWindowProperty("AI Virtual Mouse", cv2.WND_PROP_TOPMOST, 1)
    
    # Press 'q' to quit
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

# Clean up
if vc.initialized:
    vc.stop_listening()
cap.release()
cv2.destroyAllWindows()
CoUninitialize()