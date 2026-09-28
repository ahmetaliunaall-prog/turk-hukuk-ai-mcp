import unittest,asyncio,json
from local_ai.ollama import Analysis
from legal_mcp.privacy import mask,public_query
from legal_mcp.evidence import Evidence,deduplicate,rank,accepted_claims,related_articles
from legal_mcp.server import make_server
from legal_mcp.client import connect,call

def analysis():
    return Analysis(dava_turu='İşe iade',hukuki_konu='fesih',alt_konu='performans düşüklüğü',hukuki_sorun='Objektif performans kriterleri ve savunma',anahtar_kavramlar=['objektif','savunma'],ilgili_mevzuat=[{'mevzuat_no':'4857','maddeler':[19]}],aranacak_icihat_kriterleri=['performans savunma','objektif kriterler'])

class Core(unittest.TestCase):
    def test_sensitive_mask(self):
        self.assertNotIn('12345678901',mask('TC 12345678901; ali@test.com; 0532 123 45 67'))
        self.assertNotIn('ali@test.com',mask('TC 12345678901; ali@test.com; 0532 123 45 67'))
        self.assertNotIn('0532',mask('0532 123 45 67'))
    def test_iban_address_party(self):
        s=mask('TR12 1234 1234 1234 1234 1234 12\nadres: X Sokak 2\ndavacı: Ali Veli')
        self.assertNotIn('Ali Veli',s);self.assertNotIn('X Sokak',s);self.assertNotIn('TR12',s)
    def test_public_boundary(self):
        with self.assertRaises(ValueError): public_query('ali@test.com performans')
        with self.assertRaises(ValueError): public_query('a'*181)
    def test_multiplan(self): self.assertEqual(len(analysis().aranacak_icihat_kriterleri),2)
    def test_duplicate(self):
        e=Evidence('x','ictihat','t','', '');self.assertEqual(len(deduplicate([e,e])),1)
    def test_source_boundary(self):
        e=Evidence('x','ictihat','t','https://emsal.uyap.gov.tr/getDokuman?id=x','Objektif performans kriterleri savunma hakkı. '*3)
        self.assertTrue(e.verify());self.assertEqual(len(e.digest),64)
        e.url='https://emsal.uyap.gov.tr.evil.com/x';self.assertFalse(e.verify())
    def test_empty_no_verification(self):
        self.assertFalse(Evidence('x','ictihat','t','https://emsal.uyap.gov.tr/x','').verify())
    def test_rank_content_context(self):
        low=Evidence('l','ictihat','', '', 'vergi cezası')
        high=Evidence('h','ictihat','', '', '4857 objektif performans kriterleri fesih savunma')
        self.assertEqual(rank([low,high],analysis())[0].id,'h')
    def test_no_invented_claim(self):
        e=Evidence('x','ictihat','t','https://emsal.uyap.gov.tr/x','Objektif performans kriterleri savunma hakkı. '*3);e.verify()
        self.assertEqual(accepted_claims({'bulgular':[{'kaynak_id':'x','alinti':'Kaynakta olmayan değerlendirme. '*3}]},[e]),[])
        self.assertEqual(len(accepted_claims({'bulgular':[{'kaynak_id':'x','alinti':e.text[:85]}]},[e])),1)
    def test_no_fabricated_relation(self):
        a=Evidence('a','ictihat','t','https://emsal.uyap.gov.tr/x','performans değerlendirmesi '*4);a.verify()
        b=Evidence('b','mevzuat','t','https://mevzuat.gov.tr/x','kanun metni '*7,{'kanun_no':4857,'madde_no':19});b.verify()
        self.assertEqual(related_articles([a,b]),[])
    def test_tools_ictihat(self):
        self.assertEqual(len(asyncio.run(make_server('ictihat').list_tools())),2)
    def test_tools_mevzuat(self):
        self.assertEqual(len(asyncio.run(make_server('mevzuat').list_tools())),3)
    def test_tools_unified(self):
        self.assertEqual(len(asyncio.run(make_server().list_tools())),5)

class Protocol(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_tool_discovery(self):
        for module,count in [('ictihat',2),('mevzuat',3),('all',5)]:
            async with connect(module) as s:
                self.assertEqual(len((await s.list_tools()).tools),count)
    async def test_mcp_rejects_sensitive(self):
        async with connect() as s:
            with self.assertRaises(RuntimeError): await call(s,'ictihat_ara',{'ifade':'12345678901'})

if __name__=='__main__': unittest.main()
