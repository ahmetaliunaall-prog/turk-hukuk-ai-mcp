from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
import sys,json
from .adapters import ROOT

@asynccontextmanager
async def connect(module='all'):
    params=StdioServerParameters(command=sys.executable,args=['-m','legal_mcp.server',module],cwd=str(ROOT))
    async with stdio_client(params) as (reader,writer):
        async with ClientSession(reader,writer,read_timeout_seconds=60) as session:
            await session.initialize()
            yield session

async def call(session,name,args):
    result=await session.call_tool(name,args)
    if result.is_error: raise RuntimeError('MCP araç hatası: '+name)
    if result.structured_content is not None:
        data=result.structured_content
        return data.get('result',data)
    text=''.join(c.text for c in result.content if getattr(c,'type','')=='text')
    return json.loads(text)
