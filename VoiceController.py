import speech_recognition as sr
import threading
import queue
import time

class VoiceController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # Audio Tuning: Faster response time and accurate recognition
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 400 # Fixed threshold to prevent picking up static
        self.recognizer.pause_threshold = 0.6  # Give slightly more time between words so commands aren't cut off
        self.recognizer.non_speaking_duration = 0.3 # Reduce non-speaking audio padding
        
        self.latest_voice_confidence = 0.0
        self.command_queue = queue.Queue()
        self.is_running = False
        self.thread = None
        self.microphone = None
        self.initialized = False

    def initialize(self):
        """Initialize microphone and adjust for ambient noise."""
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print("VoiceController: Adjusting for ambient noise. Please wait 1 second...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2.5)
                print("VoiceController: Ready! Speak clearly into the microphone.")
            self.initialized = True
            return True
        except Exception as e:
            print(f"VoiceController Initialization Error: {e}")
            self.initialized = False
            return False

    def start_listening(self):
        if not self.initialized:
            print("VoiceController: Cannot start listening without initialization.")
            return

        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)

    def _listen_loop(self):
        print("VoiceController: Microphone is now continuously listening (Google AI)...")
        try:
            # Open microphone once to prevent flickering
            with self.microphone as source:
                while self.is_running:
                    try:
                        # timeout=0.5: Don't get stuck waiting if no one is talking
                        # phrase_time_limit=2.5: Never record more than 2.5 seconds to speed up response time.
                        audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=3.0)
                        
                        # Process audio instantly in background so mic keeps listening
                        threading.Thread(target=self._recognize_audio, args=(audio,), daemon=True).start()
                    except sr.WaitTimeoutError:
                        continue
        except Exception as e:
            print(f"Voice loop error: {e}")
            time.sleep(1)

    def _recognize_audio(self, audio):
        try:
            # Route to Google Cloud for 99% accuracy
            # show_all=True gives us a dictionary with confidence scores
            result = self.recognizer.recognize_google(audio, show_all=True)
            
            if result and 'alternative' in result:
                best_match = result['alternative'][0]
                command = best_match['transcript'].lower()
                confidence = best_match.get('confidence', 0.99) # Default to 99% if Google didn't supply it
                
                print(f"Google Recognized: {command} (Confidence: {confidence*100:.1f}%)")
                self.latest_voice_confidence = confidence
                
                self._parse_and_queue_command(command)
        except sr.UnknownValueError:
            pass # Background noise, not words
        except sr.RequestError as e:
            print(f"Google Voice API Network Error: {e}")

    def _parse_and_queue_command(self, text):
        # Strict matching since Google reads you perfectly
        
        # 1. CORE MOUSE & KEYBOARD
        if "left click" in text or text == "click":
            self.command_queue.put(("left_click", None))
        elif "right click" in text:
            self.command_queue.put(("right_click", None))
        elif "scroll up" in text:
            self.command_queue.put(("scroll_up", None))
        elif "scroll down" in text:
            self.command_queue.put(("scroll_down", None))
        elif "screenshot" in text or "screen shot" in text:
            self.command_queue.put(("screenshot", None))
        elif "zoom in" in text:
            self.command_queue.put(("zoom_in", None))
        elif "zoom out" in text:
            self.command_queue.put(("zoom_out", None))
            
        # 2. MEDIA & SYSTEM CONTROLS
        elif "volume up" in text:
            self.command_queue.put(("volume_up", None))
        elif "volume down" in text:
            self.command_queue.put(("volume_down", None))
        elif "play" in text or "pause" in text:
            self.command_queue.put(("play_pause", None))
        elif "brightness up" in text:
            self.command_queue.put(("brightness_up", None))
        elif "brightness down" in text:
            self.command_queue.put(("brightness_down", None))
            
        # 3. MOUSE MOVEMENT
        elif text == "up" or "move up" in text:
            self.command_queue.put(("move_up", None))
        elif text == "down" or "move down" in text:
            self.command_queue.put(("move_down", None))
        elif text == "left" or "move left" in text:
            self.command_queue.put(("move_left", None))
        elif text == "right" or "move right" in text:
            self.command_queue.put(("move_right", None))
            
        # 4. WINDOWS & OS CONTROL (NEW)
        elif "desktop" in text or "minimize all" in text:
            self.command_queue.put(("desktop", None))
        elif "mini" in text or "minimize" in text:
            self.command_queue.put(("minimize", None))
        elif "maxi" in text or "maximize" in text:
            self.command_queue.put(("maximize", None))
        elif "new window" in text or "open new window" in text:
            self.command_queue.put(("new_window", None))
        elif "new tab" in text or "open new tab" in text:
            self.command_queue.put(("new_tab", None))
        elif "switch window" in text or "next window" in text or "go to next window" in text or "alt tab" in text:
            self.command_queue.put(("next_window", None))
        elif "previous window" in text or "go to previous window" in text:
            self.command_queue.put(("previous_window", None))
        elif "next tab" in text or "go to next tab" in text:
            self.command_queue.put(("next_tab", None))
        elif "previous tab" in text or "go to previous tab" in text:
            self.command_queue.put(("previous_tab", None))
        elif text.startswith("close") or "close window" in text or "close app" in text:
            self.command_queue.put(("close_window", None))
        elif "double click" in text:
            self.command_queue.put(("double_click", None))
        elif "open chrome" in text or "open browser" in text:
            self.command_queue.put(("open_app", "chrome"))
        elif "open notepad" in text:
            self.command_queue.put(("open_app", "notepad"))
        elif "open calculator" in text:
            self.command_queue.put(("open_app", "calc"))
        elif "open settings" in text:
            self.command_queue.put(("open_app", "ms-settings:"))
        elif text.startswith("open file ") and "explorer" not in text:
            filename = text.replace("open file ", "", 1).strip()
            self.command_queue.put(("open_named_file", filename))
        elif text.startswith("open folder "):
            foldername = text.replace("open folder ", "", 1).strip()
            self.command_queue.put(("open_folder", foldername))
        elif "open file" in text or "open explorer" in text:
            self.command_queue.put(("open_app", "explorer"))
        elif "open vs code" in text or "open visual studio code" in text:
            self.command_queue.put(("open_app", "code"))
        elif "open word" in text or "open microsoft word" in text:
            self.command_queue.put(("open_app", "winword"))
        elif "open whatsapp chat" in text:
            name = text.replace("open whatsapp chat", "", 1).strip()
            self.command_queue.put(("whatsapp_chat", name))
        elif "open whatsapp" in text:
            self.command_queue.put(("open_app", "whatsapp:"))
        elif "open youtube" in text:
            self.command_queue.put(("open_url", "https://www.youtube.com"))
        elif text.startswith("open "):
            # Catch-all for "open [anything]"
            app_name = text.replace("open ", "", 1).strip()
            self.command_queue.put(("open_app", app_name))
            
        # 5. TYPING & SEARCHING (NEW)
        elif text.startswith("type "):
            content = text.replace("type ", "", 1)
            self.command_queue.put(("type_text", content))
        elif text.startswith("search ") or text.startswith("search for "):
            query = text.replace("search for ", "", 1).replace("search ", "", 1)
            self.command_queue.put(("search_web", query))
        elif text == "enter" or text == "hit enter" or text == "press enter":
            self.command_queue.put(("press_key", "enter"))
        elif text == "backspace" or text == "clear" or text == "clear that" or "backs" in text or "dark space" in text or "blank space" in text or "back space" in text:
            self.command_queue.put(("press_key", "backspace"))
        elif text == "delete" or text == "erase":
            self.command_queue.put(("press_key", "delete"))
        elif "space" in text and "back" not in text and "dark" not in text and "blank" not in text:
            # We already handle backspace above. This is for normal space.
            self.command_queue.put(("press_key", "space"))
        elif "face" in text or "base" in text or "page" in text or "pays" in text:
            self.command_queue.put(("press_key", "space"))
        elif text == "save" or text == "save file":
            self.command_queue.put(("save", None))
        elif text == "select all" or text == "select everything":
            self.command_queue.put(("select_all", None))
        elif text == "open search bar" or text == "find" or text == "search this page":
            self.command_queue.put(("find", None))
        elif "copy" in text or "poppy" in text or "coffee" in text:
            self.command_queue.put(("copy", None))
        elif "paste" in text or "taste" in text or "pace" in text or "based" in text or "test" in text or "best" in text or "waste" in text or "fast" in text or "past" in text or "pest" in text:
            self.command_queue.put(("paste", None))
        elif text == "cut" or text == "cut text":
            self.command_queue.put(("cut", None))
        elif text == "undo" or text == "undo that" or text == "pandu":
            self.command_queue.put(("undo", None))
        elif text == "redo" or text == "redo that" or text == "red":
            self.command_queue.put(("redo", None))
        elif text == "refresh" or text == "reload" or text == "refresh page":
            self.command_queue.put(("refresh", None))
            
        # 6. POWER STATE (NEW)
        elif text == "shutdown computer" or text == "shut down computer":
            self.command_queue.put(("shutdown", None))
        elif text == "restart computer":
            self.command_queue.put(("restart", None))

        # 7. EXIT PROJECT
        elif "terminate" in text or "quit" in text or "exit" in text:
            self.command_queue.put(("quit", None))

    def get_latest_command(self):
        """Returns the latest command tuple from the queue..."""
        try:
            command = None
            while not self.command_queue.empty():
                command = self.command_queue.get_nowait()
            return command
        except queue.Empty:
            return None
