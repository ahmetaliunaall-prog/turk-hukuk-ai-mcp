import sys
from mcp.server.mcpserver import MCPServer
from .adapters import TOOLS
from .transport import lifespan

def make_server(module='all'):
    app=MCPServer('turk-hukuk-mcp' if module=='all' else 'turk-hukuk-'+module,version='0.2.0',lifespan=lifespan)
    for name,fn in TOOLS.items():
        if module=='ictihat' and name not in ('ictihat_ara','karar_getir'): continue
        if module=='mevzuat' and name in ('ictihat_ara','karar_getir'): continue
        app.tool()(fn)
    return app

if __name__=='__main__':
    make_server(sys.argv[1] if len(sys.argv)>1 else 'all').run(transport='stdio')
