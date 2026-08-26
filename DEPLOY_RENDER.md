# IVC Chapter 1 Sim — Render Deployment

This package is ready to deploy as a Render Python web service.

## What is production-ready in v13

- Gunicorn production server
- Render Blueprint (`render.yaml`)
- HTTPS/proxy awareness
- Secure-cookie mode when `SIM_PRODUCTION=1`
- `/healthz` health check
- OpenAI key is read only from an environment variable
- `SIM_SECRET_KEY` is read from an environment variable
- OpenAI multi-turn continuity uses `previous_response_id`, so the full conversation is not stuffed into the browser session cookie
- Visible transcript is mirrored to browser localStorage so an accidental page refresh does not immediately erase the student's visible work
- Student input length limits and safer public error messages

## Render environment secrets

Render must have:

- `OPENAI_API_KEY` — your current OpenAI API project key
- `SIM_SECRET_KEY` — Render can generate this automatically from `render.yaml`

Never put your OpenAI API key in GitHub, Canvas HTML, JavaScript, or the repository.

## Deployment settings

The included `render.yaml` uses:

Build:
`pip install -r requirements.txt`

Start:
`gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 8 --timeout 120`

Health check:
`/healthz`

## Important prototype limitation

v13 is suitable for the hosting/Canvas connection test. The final student release still needs the end-of-Sim completion logic, submission packet/export, grading-state tracking, and durable recovery strategy. Those are deliberately not faked in this build.
