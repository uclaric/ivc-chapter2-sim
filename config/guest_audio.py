from .chapter2 import GUESTS

GUEST_AUDIO = {
    name: {
        "voice": spec["voice"],
        "instructions": (
            spec["speech_style"] + " Speak as a historically grounded guest in a relaxed college seminar. "
            "Never claim to be a voice clone or exact impersonation."
        ),
    }
    for name, spec in GUESTS.items()
}
