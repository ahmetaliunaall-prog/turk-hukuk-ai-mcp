import unittest,threading,json,urllib.request,urllib.error
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from local_ai.web import Handler,TOKEN

class Web(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.port=cls.server.server_port
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls): cls.server.shutdown();cls.server.server_close()
    def req(self,path,headers=None,data=None):
        hs={'Host':'127.0.0.1:8765'};hs.update(headers or {})
        return urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{self.port}'+path,headers=hs,data=data),timeout=5)
    def test_ui_serves(self):
        with self.req('/') as r: self.assertIn('Araştırma sorusu',r.read().decode())
    def test_wrong_host(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.req('/',{'Host':'evil.com'})
        self.assertEqual(c.exception.code,403)
    def test_no_token(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.req('/api/research',{'Origin':'http://127.0.0.1:8765'},b'{}')
        self.assertEqual(c.exception.code,403)
    def test_cross_origin_session_denied(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.req('/session.js',{'Origin':'https://evil.com'})
        self.assertEqual(c.exception.code,403)
    def test_private_network_preflight_is_origin_bound(self):
        headers={'Host':'127.0.0.1:8765','Origin':'http://127.0.0.1:8765','Access-Control-Request-Private-Network':'true'}
        req=urllib.request.Request(f'http://127.0.0.1:{self.port}/api/research',headers=headers,method='OPTIONS')
        with urllib.request.urlopen(req,timeout=5) as r:
            self.assertEqual(r.status,204)
            self.assertEqual(r.headers['Access-Control-Allow-Origin'],headers['Origin'])
            self.assertEqual(r.headers['Access-Control-Allow-Private-Network'],'true')
        headers['Origin']='https://evil.com'
        req=urllib.request.Request(f'http://127.0.0.1:{self.port}/api/research',headers=headers,method='OPTIONS')
        with self.assertRaises(urllib.error.HTTPError) as c:urllib.request.urlopen(req,timeout=5)
        self.assertEqual(c.exception.code,403)
    def test_valid_local_flow(self):
        async def fake(*args):return {'answer':'test','sources':[]}
        with patch('local_ai.web.research',side_effect=fake):
            with self.req('/api/research',{'Origin':'http://127.0.0.1:8765','X-Local-Token':TOKEN,'Content-Type':'application/json'},json.dumps({'text':'Objektif performans kriterleri nelerdir?'}).encode()) as r:
                self.assertEqual(json.load(r)['answer'],'test')
