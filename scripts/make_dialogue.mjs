// Builds the audio and timing for a two-voice "podcast" Short (run inside podcast/).
// Reads script.json, speaks each line with its speaker's ElevenLabs voice, measures each clip,
// places the lines one after another, and writes:
//   assets/voice.mp3  narration mixed with the soft music bed
//   timing.js         window.TIMING = { total, lines: [{ speaker, text, start, end, card }] }
// and sets the composition length in index.html. Without ELEVENLABS_API_KEY it estimates the
// timing from word counts and writes silence, so a render never breaks because of the voice.
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync, existsSync, copyFileSync } from "node:fs";

const script = JSON.parse(readFileSync("script.json", "utf8"));
const key = process.env.ELEVENLABS_API_KEY || "";
const model = process.env.ELEVENLABS_MODEL || "eleven_multilingual_v2";
const GAP = 0.3; // pause between lines, seconds
const LEAD = 0.4; // silence before the first line
const TAIL = 1.6; // hold after the last line
mkdirSync("assets", { recursive: true });
mkdirSync("tmp", { recursive: true });

const probe = (file) => Number(execFileSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", file]).toString().trim());

// Lip sync: when the voice is loud enough the mouth is open. Returns [open, close] pairs in seconds
// from the start of the clip, measured on 40 ms windows of the actual speech.
function mouthFrom(file) {
  const pcm = execFileSync("ffmpeg", ["-v", "error", "-i", file, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"], { maxBuffer: 64 * 1024 * 1024 });
  const samples = new Int16Array(pcm.buffer, pcm.byteOffset, Math.floor(pcm.length / 2));
  const win = 640; // 40 ms at 16 kHz
  const rms = [];
  for (let i = 0; i + win <= samples.length; i += win) {
    let sum = 0;
    for (let j = i; j < i + win; j++) sum += samples[j] * samples[j];
    rms.push(Math.sqrt(sum / win));
  }
  const peak = Math.max(1, ...rms);
  const on = rms.map((v, i) => {
    // open on loud windows, but close briefly on the dips between syllables
    const prev = rms[i - 1] ?? 0;
    return v > peak * 0.18 && !(v < prev * 0.6 && v < peak * 0.35);
  });
  const segs = [];
  for (let i = 0; i < on.length; i++) {
    if (!on[i]) continue;
    let j = i;
    while (j + 1 < on.length && on[j + 1]) j++;
    segs.push([i * 0.04, (j + 1) * 0.04]);
    i = j;
  }
  // keep each open or closed state on screen for at least ~2 frames
  const out = [];
  for (const s of segs) {
    if (s[1] - s[0] < 0.07) s[1] = s[0] + 0.07;
    const last = out[out.length - 1];
    if (last && s[0] - last[1] < 0.06) last[1] = Math.max(last[1], s[1]);
    else out.push(s);
  }
  return out.map(([a, b]) => [Math.round(a * 100) / 100, Math.round(b * 100) / 100]);
}

const clips = [];
for (let i = 0; i < script.lines.length; i++) {
  const line = script.lines[i];
  const file = `tmp/line${i}.mp3`;
  let ok = false;
  if (key) {
    const voice = script.voices[line.speaker];
    const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice}?output_format=mp3_44100_128`, {
      method: "POST",
      headers: { "xi-api-key": key, "Content-Type": "application/json", Accept: "audio/mpeg" },
      body: JSON.stringify({ text: line.text, model_id: model, voice_settings: { stability: 0.55, similarity_boost: 0.75, style: 0.3 } }),
    });
    if (res.ok) {
      writeFileSync(file, Buffer.from(await res.arrayBuffer()));
      ok = true;
    } else {
      console.error(`ElevenLabs error ${res.status} on line ${i}: ${(await res.text()).slice(0, 300)}`);
    }
  }
  const dur = ok ? probe(file) : Math.max(1.6, line.text.split(/\s+/).length / 2.6);
  clips.push({ ...line, file: ok ? file : null, dur, mouth: ok ? mouthFrom(file) : [] });
}

let t = LEAD;
const lines = clips.map((c) => {
  const start = Math.round(t * 100) / 100;
  t += c.dur + GAP;
  return { speaker: c.speaker, text: c.text, card: c.card || null, start, end: Math.round((start + c.dur) * 100) / 100, mouth: c.mouth.map(([a, b]) => [Math.round((start + a) * 100) / 100, Math.round((start + b) * 100) / 100]), file: c.file };
});
const total = Math.ceil((t - GAP + TAIL) * 10) / 10;

const spoken = lines.filter((l) => l.file);
if (spoken.length === 0) {
  execFileSync("ffmpeg", ["-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", String(total), "-q:a", "9", "tmp/voice_only.mp3"], { stdio: "inherit" });
} else {
  const args = ["-y"];
  spoken.forEach((l) => args.push("-i", l.file));
  const filters = spoken.map((l, i) => {
    const ms = Math.round(l.start * 1000);
    return `[${i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay=${ms}|${ms}[a${i}]`;
  });
  const mix = spoken.map((_, i) => `[a${i}]`).join("") + `amix=inputs=${spoken.length}:normalize=0,apad=whole_dur=${total},atrim=0:${total}[out]`;
  args.push("-filter_complex", filters.concat(mix).join(";"), "-map", "[out]", "-q:a", "2", "tmp/voice_only.mp3");
  execFileSync("ffmpeg", args, { stdio: "inherit" });
}

const music = existsSync("../assets/music.mp3") ? "../assets/music.mp3" : null;
if (music) {
  execFileSync("ffmpeg", [
    "-y", "-i", "tmp/voice_only.mp3", "-stream_loop", "-1", "-i", music,
    "-filter_complex",
    `[1:a]aresample=44100,aformat=channel_layouts=stereo,volume=${process.env.MUSIC_GAIN || "1.6"}[m];[0:a][m]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95,atrim=0:${total}[out]`,
    "-map", "[out]", "-q:a", "2", "assets/voice.mp3",
  ], { stdio: "inherit" });
} else {
  copyFileSync("tmp/voice_only.mp3", "assets/voice.mp3");
}

writeFileSync("timing.js", `window.TIMING = ${JSON.stringify({ total, title: script.title, lines: lines.map(({ file, ...l }) => l) }, null, 1)};\n`);
const html = readFileSync("index.html", "utf8").replace(/data-duration="[\d.]+"/g, `data-duration="${total}"`);
writeFileSync("index.html", html);
console.log(`Dialogue ready: ${lines.length} lines, ${total} s, ${spoken.length} spoken.`);
