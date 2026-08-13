"""Build host-installable RecallForge skill and plugin release archives."""
from __future__ import annotations
import hashlib, shutil, tarfile, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent; VERSION="2.2.0"; DIST=ROOT/"dist"
SKILL=ROOT/"skill"/"recallforge"; PLUGIN=ROOT/"recallforge-plugin"
def sync_plugin_skill():
    target = PLUGIN/"skills"/"recallforge"
    if target.exists(): shutil.rmtree(target)
    shutil.copytree(SKILL, target)
    assets = PLUGIN/"assets"
    assets.mkdir(exist_ok=True)
    shutil.copy2(SKILL/"assets"/"recallforge-mark.svg", assets/"recallforge-mark.svg")
    shutil.copy2(SKILL/"assets"/"recallforge-banner.svg", assets/"recallforge-banner.svg")
def archive(source: Path, out: Path, prefix: str=""):
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(source.rglob("*")):
            if p.is_file(): z.write(p, f"{prefix}{p.relative_to(source).as_posix()}")
def normalized_tarinfo(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
    """Make the distributable reproducible across local build times."""
    tarinfo.mtime = 0
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = ""
    return tarinfo

def main():
    sync_plugin_skill()
    DIST.mkdir(exist_ok=True)
    for p in DIST.iterdir(): p.unlink()
    skill_zip=DIST/f"recallforge-skill-v{VERSION}.zip"; plugin_zip=DIST/f"recallforge-plugin-v{VERSION}.zip"; tar=DIST/f"recallforge-skill-v{VERSION}.tar.gz"
    archive(SKILL,skill_zip,"recallforge/")
    with zipfile.ZipFile(skill_zip,"a",zipfile.ZIP_DEFLATED) as z:
        for name in ("install.ps1", "install.sh"):
            z.write(ROOT/"scripts"/name, f"scripts/{name}")
    archive(PLUGIN,plugin_zip)
    # gzip's timestamp is also normalized so SHA256SUMS is stable on rebuild.
    import gzip
    with tar.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w") as tf:
            tf.add(SKILL, arcname="recallforge", filter=normalized_tarinfo)
    lines=[]
    for p in (skill_zip,plugin_zip,tar): lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
    (DIST/"SHA256SUMS.txt").write_text("\n".join(lines)+"\n",encoding="utf-8")
    import subprocess,sys
    subprocess.run([sys.executable,"scripts/validate_skill.py"],cwd=ROOT,check=True)
    print("Release artifacts written to",DIST)
if __name__=="__main__": main()
