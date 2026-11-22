# Dolidob podcast lip sync: LatentSync 1.5 (ByteDance, Apache-2.0) on Kaggle's two T4 GPUs.
# Pushed by .github/workflows/episode.yml with RAW_URL replaced by the folder that holds jobs.json and the job files.
import json, os, subprocess, sys, time, urllib.request
def run(c):
    print("+", c, flush=True); t = time.time()
    r = subprocess.run(c, shell=True)
    print(f"  exit {r.returncode} in {time.time()-t:.0f}s", flush=True)
    if r.returncode: sys.exit(r.returncode)
RAW = "RAW_URL"
W = "/kaggle/working"
os.makedirs(f"{W}/in", exist_ok=True)
jobs = json.loads(urllib.request.urlopen(f"{RAW}/jobs.json").read())
for j in jobs:
    for ext in ("mp4", "wav"):
        urllib.request.urlretrieve(f"{RAW}/{j['name']}.{ext}", f"{W}/in/{j['name']}.{ext}")
os.makedirs("/kaggle/tmp", exist_ok=True); os.chdir("/kaggle/tmp")
run("git clone -q --depth 1 https://github.com/bytedance/LatentSync.git")
os.chdir("LatentSync")
PY = "/kaggle/tmp/env/bin/python"  # LatentSync pins packages for Python 3.10
run("pip install -q uv && uv venv -q -p 3.10 /kaggle/tmp/env")
run(f"uv pip install -q --python {PY} -r requirements.txt 2>&1 | tail -5")
run(f"uv pip install -q --python {PY} huggingface_hub && {PY} -c \"from huggingface_hub import hf_hub_download as d; [d('ByteDance/LatentSync-1.5', f, local_dir='checkpoints') for f in ['whisper/tiny.pt','latentsync_unet.pt']]\"")
# One copy of the code per GPU: LatentSync writes to a temp/ folder in the working directory.
run("cp -r /kaggle/tmp/LatentSync /kaggle/tmp/LatentSync2")
order = sorted(jobs, key=lambda j: -os.path.getsize(f"{W}/in/{j['name']}.wav"))
procs = []
for gpu, (q, d) in enumerate([(order[0::2], "/kaggle/tmp/LatentSync"), (order[1::2], "/kaggle/tmp/LatentSync2")]):
    cmds = " ; ".join(
        f"{PY} -m scripts.inference --unet_config_path configs/unet/stage2.yaml --inference_ckpt_path checkpoints/latentsync_unet.pt "
        f"--inference_steps 20 --guidance_scale 1.5 --video_path {W}/in/{j['name']}.mp4 --audio_path {W}/in/{j['name']}.wav "
        f"--video_out_path {W}/{j['name']}.mp4 > {W}/in/{j['name']}.log 2>&1 && echo done {j['name']}" for j in q)
    procs.append(subprocess.Popen(f"cd {d} && CUDA_VISIBLE_DEVICES={gpu} bash -c '{cmds}'", shell=True))
    time.sleep(60 if gpu == 0 else 0)  # let the first process fetch the auxiliary models first
for p in procs: p.wait()
missing = [j["name"] for j in jobs if not os.path.exists(f"{W}/{j['name']}.mp4")]
for n in missing:  # retry failures one by one on GPU 0
    run(f"cd /kaggle/tmp/LatentSync && CUDA_VISIBLE_DEVICES=0 {PY} -m scripts.inference --unet_config_path configs/unet/stage2.yaml "
        f"--inference_ckpt_path checkpoints/latentsync_unet.pt --inference_steps 20 --guidance_scale 1.5 --video_path {W}/in/{n}.mp4 "
        f"--audio_path {W}/in/{n}.wav --video_out_path {W}/{n}.mp4")
run(f"rm -rf {W}/in; ls -la {W}")
