from flask import Flask, render_template, request, jsonify, session, send_file
from openai import OpenAI
import os
import json
import random
from io import BytesIO
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

from config.chapter2 import (
    CHAPTER, CORE_CAST, GUESTS, QUESTION_POOL, TEXTBOOK_KNOWLEDGE, BASE_INSTRUCTIONS
)
from config.guest_audio import GUEST_AUDIO

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

IS_PRODUCTION = os.environ.get("SIM_PRODUCTION", "0") == "1"
SIM_SECRET_KEY = os.environ.get("SIM_SECRET_KEY", "dev-only-change-me")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

app.secret_key = SIM_SECRET_KEY
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
    MAX_CONTENT_LENGTH=12 * 1024 * 1024,
)

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("ivc-sim")

if IS_PRODUCTION and SIM_SECRET_KEY == "dev-only-change-me":
    logger.warning("SIM_SECRET_KEY is using the development fallback. Set a strong secret before student use.")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not set. OpenAI-powered routes will fail until it is configured.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")
TTS_MODEL = os.environ.get("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
TRANSCRIBE_MODEL = os.environ.get("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")

CORE_AUDIO = {
    "Prof. Epps": {
        "voice": "onyx",
        "instructions": (
            "Warm, confident American male college professor in his late 60s with a slightly deep voice. "
            "Relaxed live coffee-table conversation, expressive pauses, varied pacing, occasional dry humor, never narration."
        ),
    },
    "Sophia": {"voice": "marin", "instructions": "Young American woman in college. Thoughtful, friendly, warm, contemporary and naturally expressive."},
    "Ethan": {"voice": "ash", "instructions": "Young American male college student. Friendly, curious, intelligent, easygoing, lightly self-deprecating."},
    "Carlos": {"voice": "cedar", "instructions": "Young Hispanic male from Mexicali. Fluent English with a subtle northern Mexican/Baja California accent. Relaxed, warm, contemporary. Never British or caricatured."},
    "Aaliyah": {"voice": "coral", "instructions": "Young Black American woman in college. Warm, confident, thoughtful, socially aware, direct when appropriate, natural and contemporary."},
    "Freja": {"voice": "marin", "instructions": "Young Swedish woman speaking fluent English with a light natural Swedish accent. Friendly, curious, socially conscious. Never exaggerated."},
}
CHARACTER_AUDIO = {**CORE_AUDIO, **GUEST_AUDIO}
ALLOWED_VOICES = {"alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse", "marin", "cedar"}

VOICE_PREVIEW_TEXT = {
    "Prof. Epps": "All right, everybody. Congress. Five hundred thirty-five ambitious people and somehow the furniture survives.",
    "Sophia": "Congress looks simple in a diagram until you ask who actually controls the agenda.",
    "Ethan": "So if Congress was designed to be slow, how do we know when slow turns into broken?",
    "Carlos": "I want to know what all these rules mean for regular people waiting for something to actually get done.",
    "Aaliyah": "Representation sounds good, but I want to know whose voices actually make it into the room.",
    "Freja": "The Senate is fascinating to me because equal states and equal citizens are not quite the same thing.",
    "James Madison": "A representative government must contend with faction without surrendering liberty to its cure.",
    "Henry Clay": "A legislature that cannot bargain will soon discover that principle alone does not keep a union together.",
    "Lyndon B. Johnson": "You can give the finest speech in Washington, but if you haven't counted the votes, you haven't done the job.",
    "Shirley Chisholm": "Representation means more than being allowed into the room. It means having the independence to speak once you are there.",
    "John McCain": "Party matters, but there are moments when the institution and your own judgment have to matter more.",
}

SIM_INSTRUCTIONS = BASE_INSTRUCTIONS + "\n\n" + TEXTBOOK_KNOWLEDGE


def require_openai():
    if client is None:
        return jsonify({"error": "The Sim server is not connected to OpenAI yet."}), 503
    return None


def build_question_plan():
    accessible = random.choice(QUESTION_POOL["accessible"])
    medium = random.sample(QUESTION_POOL["medium"], 2)
    challenging = random.choice(QUESTION_POOL["challenging"])
    plan = [
        {**accessible, "difficulty": "accessible"},
        {**medium[0], "difficulty": "medium"},
        {**medium[1], "difficulty": "medium"},
        {**challenging, "difficulty": "challenging"},
    ]
    # Keep the intended difficulty ramp, while the actual wording and speaker remain dynamic.
    return plan


def current_question_state():
    plan = session.get("question_plan") or []
    idx = int(session.get("question_index", 0))
    current = plan[idx] if idx < len(plan) else None
    nxt = plan[idx + 1] if idx + 1 < len(plan) else None
    return plan, idx, current, nxt


def guest_context_for(question):
    if not question:
        return "No new historical guest is required."
    names = question.get("guest_tags", [])[:3]
    chunks = []
    for name in names:
        spec = GUESTS.get(name)
        if not spec:
            continue
        chunks.append(
            f"{name}: era={spec['era']}; expertise={', '.join(spec['expertise'])}; speaking rule={spec['speech_style']}"
        )
    return "\n".join(chunks) or "No new historical guest is required."


def parse_sim_payload(response):
    raw = (response.output_text or "").strip()
    allowed = set(CORE_CAST) | set(GUESTS.keys()) | {"Professor Epps"}
    try:
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            raise ValueError("Payload must be an object.")
        turns = payload.get("turns", [])
        if not isinstance(turns, list):
            turns = []
        cleaned_turns = []
        for turn in turns:
            if not isinstance(turn, dict):
                continue
            speaker = str(turn.get("speaker", "Prof. Epps")).strip()
            text = str(turn.get("text", "")).strip()
            expression = str(turn.get("expression", "")).strip().lower()
            if not text:
                continue
            if speaker not in allowed:
                speaker = "Prof. Epps"
            if expression not in {"neutral", "smile", "amused", "skeptical", "thinking", "surprised"}:
                expression = ""
            cleaned_turns.append({"speaker": speaker, "text": text[:4000], "action": "", "expression": expression})
        if not cleaned_turns:
            raise ValueError("No valid turns returned.")
        qresult = str(payload.get("question_result", "in_progress")).strip().lower()
        if qresult not in {"not_started", "in_progress", "answered", "clarify", "skipped"}:
            qresult = "in_progress"
        return {"turns": cleaned_turns, "wait_for_student": bool(payload.get("wait_for_student", True)), "question_result": qresult}
    except Exception:
        return {
            "turns": [{"speaker": "Prof. Epps", "text": raw or "Give me one second. The room lost its train of thought.", "action": "", "expression": "thinking"}],
            "wait_for_student": True,
            "question_result": "in_progress",
        }


@app.get("/healthz")
def healthz():
    return jsonify({
        "status": "ok",
        "service": CHAPTER["service"],
        "chapter": CHAPTER["number"],
        "openai_configured": bool(OPENAI_API_KEY),
        "model": MODEL,
        "tts_model": TTS_MODEL,
        "transcribe_model": TRANSCRIBE_MODEL,
    })


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/start")
def api_start():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    origin = (data.get("origin") or "").strip()
    fact = (data.get("fact") or "").strip()
    if not name:
        return jsonify({"error": "Name is required."}), 400
    missing = require_openai()
    if missing:
        return missing

    name, origin, fact = name[:80], origin[:160], fact[:800]
    session.clear()
    session["student_name"] = name
    session["question_plan"] = build_question_plan()
    session["question_index"] = 0
    session["question_started"] = False
    session["question_results"] = []

    user_input = f'''
The real student has just entered the Chapter 2 discussion room and introduced themself:
Name: {name}
From: {origin or "not specified"}
Crazy fun fact: {fact or "not specified"}

Complete the social opening only.
- Prof. Epps reacts briefly and freshly to the student's fun fact.
- Sophia, Ethan, Carlos, Aaliyah, and Freja each introduce themselves naturally.
- Prof. Epps introduces himself last.
- Natural interjections are welcome; do not make it feel like roll call.
- Historical guests do NOT enter during this opening.
- Do not begin the graded Congress discussion yet.
- End at a natural point where {name} can respond again.
Set question_result to "not_started".
'''
    try:
        response = client.responses.create(model=MODEL, instructions=SIM_INSTRUCTIONS, input=user_input)
        session["previous_response_id"] = response.id
        return jsonify(parse_sim_payload(response))
    except Exception:
        logger.exception("OpenAI start request failed")
        return jsonify({"error": "The discussion room could not start just now. Please try again."}), 502


@app.post("/api/reply")
def api_reply():
    data = request.get_json(force=True)
    student_text = (data.get("text") or "").strip()
    if not student_text:
        return jsonify({"error": "Response is required."}), 400
    missing = require_openai()
    if missing:
        return missing

    student_text = student_text[:2500]
    name = session.get("student_name", "Student")
    previous_response_id = session.get("previous_response_id")
    if not previous_response_id:
        return jsonify({"error": "This discussion session has expired. Please restart the Sim from the beginning."}), 409

    plan, idx, current, nxt = current_question_state()
    if not current:
        # Defensive closure if the client somehow calls again after completion.
        return jsonify({
            "turns": [{"speaker": "Prof. Epps", "text": f"You're all set, {name}. The Chapter 2 Sim-Discussion is complete. Head back to Canvas for the remaining assignment instructions.", "action": "", "expression": "amused"}],
            "wait_for_student": False,
            "question_result": "answered",
            "complete": True,
        })

    started = bool(session.get("question_started", False))
    current_guests = guest_context_for(current)
    next_summary = nxt["target"] if nxt else "There is no next question; close the Sim after this target is completed or skipped."

    if not started:
        task_block = f'''
The social opening is complete. {name}'s latest line is social conversation, NOT an answer to a graded question.
Now transition naturally into the FIRST graded Congress discussion target.
CURRENT HIDDEN TARGET: {current['target']}
Appropriate historical guest options for this target:
{current_guests}
Introduce at most 1-2 guests now if their presence genuinely improves the exchange. A guest may simply join the conversation naturally; do not announce an internal rotation system.
Ask the target in fresh conversational wording appropriate to an accessible opening. Do not reveal difficulty or question number.
Set question_result to "in_progress".
'''
    else:
        task_block = f'''
CURRENT HIDDEN TARGET ID: {current['id']}
CURRENT HIDDEN TARGET: {current['target']}
CURRENT DIFFICULTY (never reveal): {current['difficulty']}
Appropriate historical guest options:
{current_guests}
NEXT TARGET SUMMARY (use only if current target becomes answered/skipped): {next_summary}

Evaluate {name}'s latest response ONLY against the current target.
- If it is a meaningful attempt that sufficiently engages the target, set question_result="answered". Briefly respond/synthesize, then if another target remains, transition naturally toward it and ask it without revealing question numbers or difficulty. You may rotate guests if the next topic warrants it.
- If the answer is thin but salvageable, set question_result="in_progress" and give one gentle, inviting push for a reason, example, distinction, consequence, or one more step of thought.
- If {name} asks for clarification or says the question is not understood, set question_result="clarify". Rephrase the SAME target more simply and give only neutral context, not the answer.
- If {name} explicitly says skip/pass/does not want to answer, set question_result="skipped". Accept immediately and without judgment. If another target remains, move naturally to it. Do not ask them to reconsider.
- If this is the fourth target and it becomes answered or skipped, close with a concise synthesis and say the Chapter 2 Sim-Discussion is complete and {name} should return to Canvas.
'''

    user_input = f'''
The student's name is {name}.
{name} just said:
{student_text}

{task_block}

Keep the room conversational. Prof. Epps does not automatically respond first. Historical guests, recurring classmates, and Prof. Epps may speak to each other. Usually give 2-4 short turns, then wait for {name}, except the final completion may close without another question.
'''

    try:
        response = client.responses.create(model=MODEL, instructions=SIM_INSTRUCTIONS, previous_response_id=previous_response_id, input=user_input)
        session["previous_response_id"] = response.id
        payload = parse_sim_payload(response)

        if not started:
            session["question_started"] = True
        else:
            result = payload.get("question_result")
            if result in {"answered", "skipped"}:
                results = session.get("question_results", [])
                results.append({"id": current["id"], "result": result, "difficulty": current["difficulty"]})
                session["question_results"] = results
                session["question_index"] = idx + 1
                session["question_started"] = True  # response may already have introduced the next target
                if idx + 1 >= len(plan):
                    payload["complete"] = True
                    payload["wait_for_student"] = False
            elif result == "clarify":
                session["question_started"] = True

        payload["progress"] = min(int(session.get("question_index", 0)), 4)
        # Hidden grading metadata is returned for the client to persist, but the UI does not display it.
        payload["grading_marker"] = {
            "question_id": current["id"],
            "difficulty": current["difficulty"],
            "result": payload.get("question_result"),
            "zero_if_skipped": payload.get("question_result") == "skipped",
        }
        return jsonify(payload)
    except Exception:
        logger.exception("OpenAI reply request failed")
        return jsonify({"error": "The room had trouble responding. Your typed response is still visible; please try again."}), 502


@app.post("/api/transcribe")
def api_transcribe():
    missing = require_openai()
    if missing:
        return missing
    audio = request.files.get("audio")
    if audio is None:
        return jsonify({"error": "No microphone recording was received."}), 400
    raw = audio.read()
    if not raw:
        return jsonify({"error": "The microphone recording was empty."}), 400
    if len(raw) > 10 * 1024 * 1024:
        return jsonify({"error": "That recording is too large. Please try a shorter response."}), 413
    filename = (audio.filename or "student-response.webm")[:120]
    mimetype = audio.mimetype or "audio/webm"
    try:
        transcript = client.audio.transcriptions.create(
            model=TRANSCRIBE_MODEL,
            file=(filename, raw, mimetype),
            language="en",
            prompt=(
                "American Government college discussion about Congress and representation. Preserve the student's wording. "
                "Expect terms such as Congress, House, Senate, representation, delegate, trustee, politico, redistricting, "
                "gerrymandering, committee, filibuster, oversight, appropriation, lobbying, polarization, and Constitution."
            ),
        )
        text = (getattr(transcript, "text", "") or "").strip()
        if not text:
            return jsonify({"error": "I couldn't make out enough speech to transcribe. Please try again."}), 422
        return jsonify({"text": text[:2500]})
    except Exception:
        logger.exception("Student speech transcription failed")
        return jsonify({"error": "The microphone recording could not be transcribed just now. You can still type your response."}), 502


@app.post("/api/speech")
def api_speech():
    missing = require_openai()
    if missing:
        return missing
    data = request.get_json(force=True)
    speaker = (data.get("speaker") or "Prof. Epps").strip()
    text = (data.get("text") or "").strip()
    requested_voice = (data.get("voice") or "").strip()
    preview = bool(data.get("preview"))
    if preview and not text:
        text = VOICE_PREVIEW_TEXT.get(speaker, "Welcome to the Sim-Discussion.")
    if not text:
        return jsonify({"error": "Text is required."}), 400
    text = text[:4000]
    profile = CHARACTER_AUDIO.get(speaker, {"voice": "alloy", "instructions": "Speak naturally and conversationally with clear expressive inflection."})
    voice = requested_voice if requested_voice in ALLOWED_VOICES else profile["voice"]
    try:
        speech = client.audio.speech.create(model=TTS_MODEL, voice=voice, input=text, instructions=profile["instructions"], response_format="mp3")
        return send_file(BytesIO(speech.read()), mimetype="audio/mpeg", as_attachment=False, download_name="sim-dialogue.mp3")
    except Exception:
        logger.exception("Speech generation failed")
        return jsonify({"error": "Speech generation failed. Text dialogue is still available."}), 502


@app.post("/api/reset")
def api_reset():
    session.clear()
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=not IS_PRODUCTION)
