"""Vendor payload/parser koduna dokunmadan bağlantı havuzu ve ölçüm."""
import httpx,threading,time,asyncio,weakref,atexit
from contextlib import asynccontextmanager

class PooledHTTP:
    def __init__(self):
        self.client=httpx.Client(limits=httpx.Limits(max_connections=3,max_keepalive_connections=3),timeout=httpx.Timeout(12,connect=4),follow_redirects=False)
        self.gates={};self.guard=threading.Lock()
    def send(self,method,url,**kw):
        host=httpx.URL(url).host
        with self.guard:gate=self.gates.setdefault(host,{'lock':threading.Lock(),'last':0,'sem':threading.BoundedSemaphore(1)})
        with gate['sem']:
            with gate['lock']:
                delay=2.2-(time.monotonic()-gate['last'])
                if delay>0:time.sleep(delay)
                gate['last']=time.monotonic()
            kw['timeout']=httpx.Timeout(12,connect=4)
            response=self.client.request(method,url,**kw)
            if response.status_code==429:
                with gate['lock']:gate['last']=time.monotonic()+10
            return response
    def post(self,url,**kw):return self.send('POST',url,**kw)
    def get(self,url,**kw):return self.send('GET',url,**kw)

CASE_HTTP=PooledHTTP()
atexit.register(CASE_HTTP.client.close)
LOOPS=weakref.WeakKeyDictionary()
def law_client(factory):
    loop=asyncio.get_running_loop()
    if loop not in LOOPS:LOOPS[loop]=factory(timeout=12)
    return LOOPS[loop]
async def close_clients():
    c=LOOPS.pop(asyncio.get_running_loop(),None)
    if c:await c.close()
@asynccontextmanager
async def lifespan(server):
    try:yield {}
    finally:await close_clients()
