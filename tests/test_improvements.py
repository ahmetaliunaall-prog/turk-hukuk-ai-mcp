import unittest,asyncio,json,time
from unittest.mock import patch,AsyncMock
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from legal_mcp.planning import normalize,similarity,fallback,queries,alternate_court
from legal_mcp.cache import MemoryCache,SOURCE_CACHE
from legal_mcp.evidence import Evidence,accepted_claims,rank
from legal_mcp.access import generate_key,hash_key,valid_format,RateLimiter,validate_access,AccessError
from legal_mcp.orchestrator import research

class Improvements(unittest.TestCase):
    def test_turkish_normalize(self):self.assertEqual(normalize('ıİşŞğĞüÜöÖçÇ I'),'iissgguuoocc i')
    def test_fuzzy_candidate(self):self.assertGreater(similarity('objektif performans','OBJEKTİF performansı'),.8)
    def test_exact_quote_still_strict(self):
        e=Evidence('x','ictihat','t','https://emsal.uyap.gov.tr/x','İşçinin savunmasının alınması fesih araştırmasında incelenmelidir.');e.verify()
        self.assertEqual(accepted_claims({'bulgular':[{'kaynak_id':'x','alinti':normalize(e.text)}]},[e]),[])
    def test_query_family(self):
        q=queries(fallback('İŞE İADE davasında geçersiz fesih'))
        self.assertIn('işe iade',q);self.assertIn('geçersiz fesih',q);self.assertEqual(len(q),5)
    def test_fallback_personal_text_never_query(self):
        p=fallback('Davacı Ahmet Özel için kira tahliye 12345678901 araştır')
        self.assertNotIn('Ahmet',str(queries(p)));self.assertNotIn('12345678901',str(queries(p)))
    def test_wrong_court_fallback(self):self.assertEqual(alternate_court(fallback('işe iade'), 'idari'),'adli')
    def test_cache_expiry_and_copy(self):
        c=MemoryCache(ttl=.01,max_entries=1);c.put('q',{'x':[1]});r=c.get('q');r['x'].append(2);self.assertEqual(c.get('q')['x'],[1]);time.sleep(.02);self.assertIsNone(c.get('q'))
    def test_cache_bound(self):
        c=MemoryCache(max_entries=1);c.put('a',1);c.put('b',2);self.assertIsNone(c.get('a'))
    def test_key_length_hash_uniqueness(self):
        keys={generate_key() for _ in range(1000)};self.assertEqual(len(keys),1000)
        for k in keys:self.assertTrue(valid_format(k));self.assertEqual(len(k),12);self.assertEqual(len(hash_key(k)),64);self.assertNotEqual(k,hash_key(k))
    def test_invalid_key_rejected(self):
        with self.assertRaises(AccessError):validate_access('bad','invalid-test')
    def test_rate_limit(self):
        r=RateLimiter(limit=2);self.assertTrue(r.allow('x'));self.assertTrue(r.allow('x'));self.assertFalse(r.allow('x'));self.assertTrue(r.allow('y'))
    def test_inactive_expired_revoked_rejected_remote(self):
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return b'{"valid":false}'
        for state in ['inactive','expired','revoked']:
            with patch('legal_mcp.access.settings',return_value={'supabase_url':'https://x.supabase.co','publishable_key':'sb_publishable_test'}),patch('urllib.request.urlopen',return_value=Response()):
                with self.assertRaises(AccessError):validate_access('Abc123Def456',state)
    def test_key_gate_and_build(self):
        root=Path(__file__).resolve().parents[1]
        self.assertIn('accessGate',(root/'frontend/index.html').read_text(encoding='utf-8'))
        self.assertIn('X-Access-Key',(root/'frontend/app.js').read_text(encoding='utf-8'))
        self.assertIn('publish = "frontend"',(root/'netlify.toml').read_text(encoding='utf-8'))
    def test_rls_static_configuration(self):
        root=Path(__file__).resolve().parents[1]
        sql=(root/'supabase/migrations/202609280001_thaimcp_access.sql').read_text(encoding='utf-8')
        self.assertEqual(sql.count('enable row level security'),3);self.assertIn('from public,anon,authenticated',sql)
        self.assertNotIn('security definer',sql.lower());self.assertNotIn('key_hash\',key_hash',sql)

class Parallel(unittest.IsolatedAsyncioTestCase):
    async def test_parallel_cache_fallback_duplicate(self):
        SOURCE_CACHE.clear();active=0;peak=0;calls=[]
        class Session:
            async def list_tools(self):return SimpleNamespace(tools=[SimpleNamespace(name=n) for n in ['ictihat_ara','karar_getir','search_mevzuat','get_mevzuat_article_tree','get_mevzuat_article_content']])
        @asynccontextmanager
        async def connect():yield Session()
        async def call(session,name,args):
            nonlocal active,peak
            active+=1;peak=max(peak,active);calls.append((name,json.dumps(args,sort_keys=True)))
            await asyncio.sleep(.05);active-=1
            if name=='ictihat_ara':return {'sonuclar':[{'id':str(i),'mahkeme':'Yargıtay 9. Hukuk','atif':'İşe iade savunma'} for i in range(8)]}
            if name=='karar_getir':return {'kaynak':'https://emsal.uyap.gov.tr/x','metin':'Objektif performans kriterleri ve savunma fesih araştırmasında incelenir. '*3}
            if name=='search_mevzuat':return {'documents':[{'mevzuat_id':'law','mevzuat_no':4857,'mevzuat_adi':'İş Kanunu'}]}
            if name=='get_mevzuat_article_tree':return [{'madde_id':'article','madde_no':19,'title':'Savunma','children':[]}]
            return {'markdown_content':'Fesih ve savunma koşulları için kanun metni incelenir. '*3}
        with patch('legal_mcp.orchestrator.connect',connect),patch('legal_mcp.orchestrator.call',call),patch('legal_mcp.orchestrator.analyze',side_effect=TimeoutError),patch('legal_mcp.orchestrator.chat',side_effect=TimeoutError):
            r=await research('İşe iade performans savunma');count=len(calls);r2=await research('İşe iade performans savunma')
        self.assertGreater(peak,1);self.assertLessEqual(peak,3);self.assertEqual(len(calls),len(set(calls)));self.assertEqual(len(calls),count)
        self.assertTrue(r['metrics']['qwen_fallback']);self.assertGreater(r2['metrics']['cache_hits'],0)
        self.assertTrue(r['claims']);self.assertTrue(all(e['verified'] for e in r['sources']));SOURCE_CACHE.clear()

if __name__=='__main__':unittest.main()
