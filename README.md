# dolidob-videos

HyperFrames project that renders the "What $X takes home in <state>" YouTube Shorts (1080x1920).

- `index.html`: the video (HTML + GSAP), driven by variables.
- `scripts/make_voice.mjs`: narration from ElevenLabs (silent fallback).
- `.github/workflows/render.yml`: run by n8n through `workflow_dispatch`, uploads `video.mp4` as an artifact.

Secrets: `ELEVENLABS_API_KEY` (repository secret). Optional variable: `ELEVENLABS_VOICE_ID`.
