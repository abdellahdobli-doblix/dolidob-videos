// Builds assets/voice.mp3 (26 s) from short narration lines placed at fixed times.
// Uses ElevenLabs text-to-speech when ELEVENLABS_API_KEY is set; otherwise writes silence,
// so the render never breaks because of the voice.
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";

const TOTAL = 26;
const v = JSON.parse(process.env.PAYLOAD || "{}");
const key = process.env.ELEVENLABS_API_KEY || "";
const voiceId = process.env.ELEVENLABS_VOICE_ID || "XrExE9yKIg1WjnnlVkGX";
const model = process.env.ELEVENLABS_MODEL || "eleven_multilingual_v2";

const spoken = (n) => (n >= 10000 ? Math.round(n / 1000) + " thousand dollars" : Math.round(n / 10) * 10 + " dollars");
const name = v.stateName || "this state";
const lines = [
  [0, `In ${name}, a ${spoken(v.income)} salary leaves you with only ${spoken(v.net)}.`],
  [5, `Federal income tax takes about ${spoken(v.fed)}.`],
  [8, `Social Security and Medicare take ${spoken(v.fica)}.`],
  [11, v.noStateTax ? "And there is no state income tax on wages." : `${name} income tax takes ${spoken(v.stateTax)}.`],
  [15, `That is about ${spoken(v.net / 12)} a month.`],
  [19, "Remember, this is an estimate, not tax advice."],
  [23, "Try it with your own numbers at dolidob dot com."],
];

mkdirSync("assets", { recursive: true });
mkdirSync("tmp", { recursive: true });

function silence() {
  execFileSync("ffmpeg", ["-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", String(TOTAL), "-q:a", "9", "assets/voice.mp3"], { stdio: "inherit" });
}

if (!key) {
  console.log("No ELEVENLABS_API_KEY: writing a silent voice track.");
  silence();
  process.exit(0);
}

const parts = [];
for (let i = 0; i < lines.length; i++) {
  const [at, text] = lines[i];
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?output_format=mp3_44100_128`, {
    method: "POST",
    headers: { "xi-api-key": key, "Content-Type": "application/json", Accept: "audio/mpeg" },
    body: JSON.stringify({ text, model_id: model, voice_settings: { stability: 0.75, similarity_boost: 0.75 } }),
  });
  if (!res.ok) {
    console.error(`ElevenLabs error ${res.status} on line ${i}: ${(await res.text()).slice(0, 300)}`);
    console.error("Falling back to a silent voice track.");
    silence();
    process.exit(0);
  }
  const file = `tmp/seg${i}.mp3`;
  writeFileSync(file, Buffer.from(await res.arrayBuffer()));
  parts.push({ file, at });
}

const args = ["-y"];
parts.forEach((p) => args.push("-i", p.file));
const filters = parts.map((p, i) => `[${i}:a]aresample=44100,aformat=channel_layouts=stereo,adelay=${p.at * 1000}|${p.at * 1000}[a${i}]`);
const mix = parts.map((_, i) => `[a${i}]`).join("") + `amix=inputs=${parts.length}:normalize=0,apad=whole_dur=${TOTAL},atrim=0:${TOTAL}[out]`;
args.push("-filter_complex", filters.concat(mix).join(";"), "-map", "[out]", "-q:a", "2", "assets/voice.mp3");
execFileSync("ffmpeg", args, { stdio: "inherit" });
console.log("Voice track ready.");
