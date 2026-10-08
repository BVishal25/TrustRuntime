import time, uuid
class RunMetrics:
    def __init__(self): self.run_id=uuid.uuid4().hex; self.started=time.perf_counter(); self.data={"attempts":0,"tool_calls":0,"tokens_estimate":0,"events":0}
    def inc(self,key,n=1): self.data[key]=self.data.get(key,0)+n
    def finish(self): self.data["latency_ms"]=(time.perf_counter()-self.started)*1000; return self.data
