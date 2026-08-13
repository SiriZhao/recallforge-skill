"""Build host-installable RecallForge skill and plugin release archives."""
from __future__ import annotations
import hashlib, shutil, tarfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; VERSION="2.1.0"; DIST=ROOT/"dist"
SKILL=ROOT/"skill"/"recallforge"; PLUGIN=ROOT/"recallforge-plugin"
def archive(source: Path, out: Path, prefix: str=""):
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(source.rglob("*")):
            if p.is_file(): z.write(p, f"{prefix}{p.relative_to(source).as_posix()}")
def main():
    DIST.mkdir(exist_ok=True)
    for p in DIST.iterdir(): p.unlink()
    skill_zip=DIST/f"recallforge-skill-v{VERSION}.zip"; plugin_zip=DIST/f"recallforge-plugin-v{VERSION}.zip"; tar=DIST/f"recallforge-skill-v{VERSION}.tar.gz"
    archive(SKILL,skill_zip,"recallforge/")
    with zipfile.ZipFile(skill_zip,"a",zipfile.ZIP_DEFLATED) as z:
        for name in ("install.ps1", "install.sh"):
            z.write(ROOT/"scripts"/name, f"scripts/{name}")
    archive(PLUGIN,plugin_zip)
    with tarfile.open(tar,"w:gz") as tf: tf.add(SKILL,arcname="recallforge")
    lines=[]
    for p in (skill_zip,plugin_zip,tar): lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (DIST/"SHA256SUMS.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    import subprocess,sys
    subprocess.run([sys.executable,"scripts/validate_skill.py"],cwd=ROOT,check=True)
    print("Release artifacts written to",DIST)
if __name__=="__main__": main()
