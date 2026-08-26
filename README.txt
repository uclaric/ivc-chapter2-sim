CHAPTER 1 SIM-DISCUSSION v4 — LOCAL AI PROTOTYPE

WHAT THIS IS
------------
A local Flask web app that keeps your OpenAI API key on the server side.
The browser never receives the key.

FILES
-----
app.py
requirements.txt
templates/index.html
static/chapter1_room.png

WINDOWS QUICK START
-------------------
1. Install Python 3 if it is not already installed.

2. Open PowerShell in this folder.

3. Install the required packages:
   py -m pip install -r requirements.txt

4. Create an OpenAI API key in the OpenAI API platform.
   IMPORTANT: Never paste your API key into ChatGPT, Canvas, HTML, or JavaScript.

5. In the SAME PowerShell window, set the key temporarily:
   $env:OPENAI_API_KEY="PASTE_YOUR_KEY_HERE"

6. Optional: choose a model if needed:
   $env:OPENAI_MODEL="gpt-5.5"

7. Start the Sim server:
   py app.py

8. In Firefox/Chrome open:
   http://127.0.0.1:5000

9. Leave the PowerShell window open while testing.

STOPPING THE SERVER
-------------------
Press Ctrl+C in PowerShell.

SECURITY
--------
This is a LOCAL prototype only.
Do not publish it to the internet as-is.
Before deployment we will add proper secrets management, authentication,
session storage, logging controls, Canvas/LTI integration, and transcript handling.


V5 INTERFACE CHANGES
--------------------
- Room image stays visually anchored while the transcript scrolls independently.
- Student response controls stay fixed at the bottom of the dialogue panel.
- Drag the gold divider left/right to resize the room versus dialogue area.
- Room defaults to about 70% of the desktop width.
- Use + / - to adjust room zoom.
- Reset view returns to the recommended room width and zoom.
- Smaller screens stack automatically.


V6 INPUT CHANGE
---------------
- Enter/Return sends the student's response.
- Shift+Enter inserts a new line.
- The Send button remains available for mouse/touch and accessibility.


V7 OPENING ENGINE CHANGES
-------------------------
- Launch button is now LET'S PLAY!
- Dialogue varies from student to student; personalities/tasks remain consistent.
- Prof. Epps humor is more relaxed, contemporary, spontaneous, and may use mild language naturally.
- Prof. Epps always reacts specifically to the student's fun fact.
- No visible stage directions such as "grins" or "laughs".
- Sophia, Ethan, and Carlos each give a real brief introduction.
- Prof. Epps introduces himself last.
- Natural banter/interjections may occur between introductions.
- Not everyone reacts to the same fun fact.
- Opening continues until the social task is complete rather than stopping at an arbitrary turn count.
- Politics & Citizenship does not begin until introductions are complete.


V8 ACCESSIBILITY CHANGES
------------------------
- Conversation transcript uses an ARIA live log for screen readers.
- Skip links allow keyboard users to jump directly to conversation or response box.
- The room/conversation divider is keyboard accessible:
  Arrow Left/Right adjusts size, Home/End jumps to limits.
- Focus Conversation enlarges the dialogue panel without removing the room permanently.
- Optional browser-based read-aloud mode is available.
- Replay Last and Pause Audio controls are available.
- Auto-read is OFF by default so it does not conflict with a student's screen reader.
- Input fields have screen-reader instructions.
- Visible focus indicators were strengthened.
- All core functionality remains usable without relying on the room image.
- Browser speech voices are only a prototype. Production character-specific audio will use a dedicated TTS layer.


V9 ROOM-FIT CHANGE
------------------
- The room is now rendered as a real image using object-fit: contain.
- The full cast remains visible at the default zoom even when the room panel is resized.
- Black letterboxing may appear when the image and panel aspect ratios differ.
- "Fit full room" restores the complete image without changing the divider position.
- Zoom controls still work; zooming in intentionally crops edges.


V10 OPENAI CHARACTER AUDIO
--------------------------
- Replaces the robotic browser speechSynthesis prototype with server-side OpenAI text-to-speech.
- Character audio is OFF by default so screen-reader users are not forced into competing audio.
- Prototype character voices:
    Prof. Epps -> onyx
    Sophia     -> nova
    Ethan      -> echo
    Carlos     -> fable
- Replay Last and Pause Audio remain available.
- Audio is queued so multiple Sim turns play in order instead of speaking over one another.
- Uses tts-1-hd by default for higher-quality speech.
- These are distinct synthetic voices, NOT voice clones.


V11 EXPRESSIVE CHARACTER AUDIO
------------------------------
- Speech model changed from tts-1-hd to gpt-4o-mini-tts.
- Each character now receives delivery instructions in addition to a distinct voice.
- Prof. Epps: warm, relaxed, contemporary American male professor; expressive humor/sarcasm.
- Sophia: young American woman; thoughtful, warm, intelligent, conversational.
- Ethan: young American man; curious, easygoing, intelligent, lightly self-deprecating.
- Carlos: young bilingual Hispanic male from Mexicali; fluent English with a natural moderate Baja/northern Mexican accent.
- Carlos must never sound British or use an exaggerated/stereotypical accent.
- These remain synthetic character voices, not voice clones.


V12 MASTER COHORT + VOICE PICKER
--------------------------------
- Uses the approved master room image with Prof. Epps, Sophia, Ethan, Carlos, Aaliyah, and Freja.
- Chapter 1 opening now introduces all five recurring students and Prof. Epps.
- Aaliyah and Freja are permanent recurring classmates, not later surprise arrivals.
- Voice Settings panel lets the user choose among 13 current built-in OpenAI speech voices per character.
- Every character has a Preview button.
- Selected voice is used for that character's generated dialogue while preserving character-specific delivery instructions.
- AI-generated voice disclosure is visible in Voice Settings.
- Marin and Cedar are identified as current OpenAI quality recommendations.


V12.1 VOICE PREVIEW FIX
-----------------------
- Fixed Preview buttons so an empty local text field no longer cancels the preview request.
- Preview now requests the character's server-side sample line and plays it.
- Added loading/error feedback for previews.


V12.2 PROF. EPPS VOICE TUNING
-----------------------------
- Prof. Epps default voice changed to Onyx after user audition.
- Delivery instructions strengthened for natural inflection, relaxed pacing, humor, sarcasm, and conversational warmth.
- Prof. Epps preview line now tests a genuinely humorous line rather than a neutral greeting.
- Voice remains synthetic and is not a clone of Prof. Epps' real voice.


V12.3 PROF. EPPS HUMOR DELIVERY
-------------------------------
- Keeps Onyx as the Prof. Epps baseline.
- Explicitly instructs the voice not to flatten after a punchline.
- Teasing/sarcastic lines may end with a small vocal smile, amused exhale, or brief natural chuckle when appropriate.
- Preview joke shortened into cleaner conversational beats for better timing.


V13 HOST-READY BUILD
--------------------
- Prepared for deployment to Render.
- Adds Gunicorn and Render Blueprint configuration.
- Adds /healthz endpoint.
- Uses SIM_SECRET_KEY and OPENAI_API_KEY from environment variables.
- Production mode enables secure session cookies.
- Multi-turn model continuity now uses the Responses API previous_response_id.
- Full model history is no longer stored in the Flask cookie session.
- Browser localStorage mirrors the visible transcript for accidental-refresh recovery.
- Public API errors no longer expose internal exception details.
- This is the hosting/Canvas-connection prototype. Final completion/export/grading persistence comes next.


V13.1 EMOTION + AUDIO PREFETCH
------------------------------
- Strengthens sparse, character-appropriate emoji/emotional punctuation.
- Emoji remain visible in the transcript but are removed from normal TTS input.
- TTS for all returned turns begins prefetching in parallel as soon as the model response arrives.
- Playback remains sequential so speakers stay in conversational order.
- Changing voice settings clears prefetched speech so the newly selected voice is used.


V13.2 STUDENT VOICE INPUT + FASTER FIRST AUDIO
-----------------------------------------------
- Adds optional student microphone input using browser MediaRecorder.
- Student speech is transcribed server-side with OpenAI gpt-4o-mini-transcribe.
- Transcribed speech is placed in the response box for review/editing before Send.
- Spoken responses are never submitted automatically.
- Adds a neutral Sim Help panel; Simon does not appear inside the Sim.
- Pre-generates a short Prof. Epps bridge when character audio is enabled, reducing perceived dead air after LET'S PLAY while the first dynamic response is generated.
- Preserves v13.1 character cadence and parallel TTS prefetch.
- Increases the Flask request limit to support short student audio recordings.


V13.4 TEXTBOOK-INTEGRATED CHAPTER 1
-----------------------------------
- Adds authoritative v29 textbook knowledge layer and whole-book chapter map.
- Chapter 1 uses textbook framing as primary authority while respecting future-chapter boundaries.
- Adds invisible four-theme progression/completion guidance.
- Adds Howdy/Hola quick setup check using typing or microphone.
- Preserves v13.2 microphone transcription, editable responses, character audio, cadence, and Help.
- Adds Prof. Epps occasional natural mild profanity rule.


V13.4.1 DYNAMIC THEME ENGINE
----------------------------
- Converts the four Chapter 1 requirements from fixed questions into four required thematic domains.
- Theme order varies according to the student's actual conversation.
- Questions and follow-ups are generated dynamically from textbook knowledge, prior dialogue, and character personalities.
- Different participants may introduce or deepen major themes; Prof. Epps does not control every transition.
- One exchange may satisfy or develop more than one theme when academically appropriate.
- Academic coverage remains consistent while wording, angle, examples, speaker, and conversational route vary.


V13.4.2 HOWDY/HOLA BUTTON FIX
-----------------------------
- Fixes the Quick Setup Continue handler so it focuses the actual name field.
- Continue is disabled until the student types or successfully transcribes a greeting.
- Successful microphone transcription automatically activates Continue.
- No changes to textbook knowledge, dynamic themes, TTS cadence, or main microphone workflow.


V13.4.3 JAVASCRIPT STARTUP FIX
------------------------------
- Removes a duplicate `const introCard` declaration introduced by the Howdy/Hola setup layer.
- The duplicate declaration caused the browser to stop parsing the entire script, leaving setup controls inactive.
- No changes to textbook knowledge, dynamic themes, microphone transcription, character audio, or discussion logic.
