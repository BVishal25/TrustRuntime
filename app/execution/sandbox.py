from __future__ import annotations
import asyncio, tempfile, pathlib, subprocess, time, json, shutil
from app.core.config import get_settings
from app.verification.verifier import Verifier

class DockerSandbox:
    def __init__(self): self.s=get_settings(); self.verifier=Verifier()
    async def run_python(self,code:str)->dict:
        static=self.verifier.static_python(code)
        if not static.passed: return {"status":"blocked","verification":static.model_dump()}
        with tempfile.TemporaryDirectory(prefix="trustruntime-") as td:
            p=pathlib.Path(td)/"main.py"; p.write_text(code,encoding="utf-8")
            cmd=["docker","run","--rm","--network","none","--cpus","0.5","--memory",f"{self.s.sandbox_memory_mb}m","--pids-limit","64","-v",f"{td}:/work:ro","python:3.12-slim","python","/work/main.py"]
            start=time.perf_counter()
            try:
                proc=await asyncio.create_subprocess_exec(*cmd,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
                out,err=await asyncio.wait_for(proc.communicate(),timeout=self.s.sandbox_timeout_seconds)
                return {"status":"success" if proc.returncode==0 else "failed","returncode":proc.returncode,"stdout":out.decode(errors="replace"),"stderr":err.decode(errors="replace"),"duration_ms":(time.perf_counter()-start)*1000}
            except FileNotFoundError: return {"status":"unavailable","error":"Docker is not installed or not on PATH"}
            except asyncio.TimeoutError:
                try: proc.kill()
                except Exception: pass
                return {"status":"timeout","duration_ms":(time.perf_counter()-start)*1000}
