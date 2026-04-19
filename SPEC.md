1. Project Overview
This project controls Spotify playback based on use movement and gestures. 

2. Technical Stack
- Language: Python 3.10+
- Vision: OpenCV, MediaPipe
- API: Spotipy (Spotify Web API)
- UI: CustomTkinter (or standard Tkinter)
- Concurrency: Threading (to prevent UI/Camera lag during API calls)

3. Architecture
project/
├── main.py                 # Application entry point & Global State
├── config.py               # API Credentials & Constants
├── ui/
│   ├── selection_screen.py # Mode selection logic
│   └── camera_view.py      # OpenCV feed integration into UI
├── perception/
│   ├── engine.py           # Base MediaPipe wrapper
│   ├── hands.py            # Gesture logic (Conductor Mode)
│   ├── pose.py             # Posture logic (Focus Mode)
│   └── face.py             # Emotion logic (Emotion Mode)
├── modes/
│   ├── conductor_mode.py   # Maps gestures -> Spotify actions
│   ├── focus_mode.py       # Maps posture -> Playlists
│   └── emotion_mode.py     # Maps emotions -> Playlists
└── spotify/
    └── controller.py       # Spotipy wrapper with error handling

4. Functional Requirements

Phase 1: Spotify Integration (spotify/controller.py)
- Implement a SpotifyController class with these methods: next_track(), previous_track(), toggle_play(), adjust_volume(pct), play_playlist(playlist_id)
- Handle SpotifyException when no active device is found

Phase 2: Perception Layer (perception/)
- Detect palm orientation and finger pinches
- Detect concentration and presence / absence from the camera view
- Detect happy, sad, etc. using MediaPipe Face Mesh or Blendshapes
- Create a toggle to ensure only the model required by the active mode is consuming CPU/GPU resources

Phase 3: Mode Logic (modes/)
- Conductor:
    - Pinch = Play/Pause
    - Swipe Left/Right = Skip/Previous
    - Point Up/Down = volume 
- Focus:
    - Head down = focus playlist 
    - Upright = energetic playlist
    - Gone from view = pause playlist 
- Emotion:
    - Sad = moody playlist 
    - Happy = upbeat playlist 

Phase 4: UI & Main Loop (main.py)
- A splash screen for mode selection between the 3 modes ^ 
- A camera view window that displays the MediaPipe landmark overlays
- When "M" is pressed go back to this mode selection screen

5. Important Stuff
- Latency: Spotify API calls must run in a background thread to prevent the Camera UI from freezing
- There is already an .env and a gotignore file for SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, and SPOTIPY_REDIRECT_URI

6. Execution Instructions for the Agent (AI helped with this)
- Setup: Create the virtual environment and install mediapipe, opencv-python, spotipy, and python-dotenv
- Mocking: If Spotify credentials are not provided initially, create a mock_controller.py that prints actions to the console so the vision logic can be tested
- Iterative Build: Start with perception/hands.py, then spotify/controller.py, then integrate them in main.py