AI Tools + How I Used Them:
- Github Copilot = read my SPEC.md and do the majority of the new implementations
- Gemini = consultations on small QOF changes (e.g. visual appearance) and debugging
- Cursor = to replace Copilot when I ran out of my monthly usage :c

Major Prompts:
- Read SPEC.md in this project. Implement the project exactly as specified. Create all necessary files, components, and navigation. Make sure that appropriate data is persistent. Ask any clarifying questions you need before making changes to the code.
- Help me brainstorm how to make the following changes to the code. Form a numbered plan of how you would change the project to make those improvements.
    1) Instead of conductor mode and study mode, break the 2 modes into personal mode and staff mode where personal mode is for my use and staff mode is for work events like playing music while we grade coding exams. 
    2) For pausing / volume shifting / next or prev song from hand movements, add a standby state / active state to prevent oversensitivity to all hand movements. Have the code automatically in standby state until a clear 1.5 second wave is detected. Then after the wave, pause / volume up / volume down / skip to next / back to prev based on pinch / index points up / thumb points down / swipes right / swipes left.
    3) When skipping to prev / next song, have a smooth transition instead of a sudden one.
- i've added too many features to this project and now it doesnt work. none of the hand signals are accurately tracked. scale back this project to the basics - 2 modes (personal and staff) that both have "conductor" abilities (pointing for volume, swiping for skips, pinching for pause/start). staff mode also has the voice controls. that's it (no emotion detection or switching between playlists etc.) delete unnecessary files to make it cleaner but make a list of everything you kept / changed / deleted and why
- analyze the code carefully and figure out why the coloured backgrounds arent working. give your reponse in written text and explain how you would fix it