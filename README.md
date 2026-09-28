# Türk Hukuk AI MCP

Mevcut içtihat ve mevzuat istemcilerini koruyan, Windows'ta yerel Qwen 3 1.7B destekli hukuk araştırma sistemi.

## Kullanım

`start.cmd` veya `start.ps1` çalıştırın. Yerel arayüz: http://127.0.0.1:8765. Python 3.14, mevcut MCP 2.2.0 ve Ollama kullanılır; bu geliştirmede paket/model indirilmedi. Ana model `qwen3:1.7b` ve adresi yalnız `127.0.0.1:11434`.

Production: https://turk-hukuk-ai-mcp.netlify.app. Yönetici: `/admin.html`. Yönetici Supabase hesabıyla giriş yapar ve 12 karakterli anahtar oluşturur. Kullanıcı anahtarı giriş kapısında doğrular. Anahtar yalnız sekme belleğindedir; sayfa yenilenince yeniden girilir.

Netlify araştırması için aynı bilgisayarda yerel sunucu çalışmalıdır. `config/local.json` içinde izinli Netlify origin'i tanımlanır; örnek `local.example.json`. Bağlantı ayarlarına yerel uygulamanın gösterdiği geçici oturum kodu girilir. Tarayıcı yerel ağ izni isteyebilir; HTTPS→localhost engelinde yerel arayüz kullanılabilir. Netlify üzerinde yerel Qwen çalışmaz. Tünel veya dışarı açık AI endpoint yoktur.

## Mimari ve araştırma

`frontend/` sade arayüz; `local_ai/` Ollama ve localhost köprüsü; `legal_mcp/` MCP, planlama, sıralama, kaynak doğrulama ve erişim; `vendor/` mevcut lisanslı kaynak istemcileri; `supabase/` migration, Edge Function ve SQL testleri.

Yerel maskeleme → MCP bağlantısı → süre sınırlı Qwen kavram desteği → kişisiz hukuk sorguları → sınırlı paralel içtihat/mevzuat araması → metadata ön sıralama → seçilmiş tam metinler → birebir kaynak pasajları → araştırma/dilekçe taslağı.

Qwen 64 token/8 saniyelik plan desteği verir. Yanıt yoksa hukuki terim ailelerinden sınırlı araştırma planı kurulur; bu durum sonuçta açıkça bildirilir. Plan başarılıysa 32 token/4 saniyelik pasaj kimliği seçimi denenir; başarısızsa kaynak metninden birebir pasaj seçilir. Bu yerel seçim hukuki yorum değildir. Modelin önerdiği kanun veya madde kaynak sayılmaz.

MCP araçları korunur: `ictihat_ara`, `karar_getir`, `search_mevzuat`, `get_mevzuat_article_tree`, `get_mevzuat_article_content`. Birleşik sunucu `python -m legal_mcp.server`; ayrı kaynaklar `ictihat` / `mevzuat` argümanıyla çalışır.

İçtihat için en fazla 5 farklı kişisiz sorgu, sonuç azsa ek sayfa ve başka mahkeme ailesi araştırılır. Önce 20 sonuçlu metadata aranır; normal araştırmada en fazla 7 karar tam metni seçilir. Mevzuat adı/numarası ve içerik ifadeleri aranır; en fazla 3 kanun ve ilgili madde düğümleri getirilir. Daha fazla karar sonraki sayfayı araştırır. Aynı mahkeme/kimlik tekrarları birleştirilir; aynı belgenin farklı sorgularda bulunması korunur.

Türkçe harf normalizasyonu, kısmi ve yaklaşık eşleşme yalnız sıralamada kullanılır. Konu, alt konu, sorun, kavram, kanun/madde, sorgu, başlık, tam metin, mahkeme/daire ve düşük ağırlıklı tarih puanları gösterilir. Alıntı kabulü yaklaşık değildir: metin kaynağın birebir alt dizisi olmalıdır. Kaynak kartları mahkeme, daire, esas/karar, tarih, puan, ilgili pasaj, resmî bağlantı ve tam metni gösterir. İlerleme gerçek sunucu olaylarından gelir.

## Performans

Aynı işe iade araştırması eski sürümde 354.438 saniye, yeni sürümde soğuk 61.868 ve sıcak 30.561 saniye ölçüldü. İlk ölçümde 97 karar ve 17 mevzuat adayı bulundu; 9/9 kaynak doğrulandı. Sıcak ölçüm 10/10 doğrulanmış kaynak verdi. Önceki 20 HTTP denemesine karşı soğuk 23, sıcak 2 deneme: hız kazanımı yalnız çağrı azaltımı değildir; model süresi sınırı, ön seçim, paralellik ve önbellek etkilidir.

Toplam araç eşzamanlılığı 3; UYAP hostunda tek istek ve en az 2.2 saniye aralık vardır. 429 yanıtı geri çekilme ve açık hata üretir. 256 kayıt/300 saniyelik bellek önbelleğinde yalnız kamu kaynakları ve kişisiz arama sonuçları tutulur. Olay, model yanıtı ve araştırma geçmişi önbelleğe alınmaz. 4 GB RAM'de model/MCP başlatma ve disk belleği hâlâ süreyi etkiler; her sorgunun aynı hızda biteceği garanti edilmez.

## Supabase ve erişim güvenliği

Mevcut Supabase projesinde yalnız yeni `thaimcp_admins`, `thaimcp_api_keys`, `thaimcp_usage` tabloları kullanılır. Mevcut kişisel site tabloları ve diğer Edge Functions değiştirilmez. Olay metni Supabase'e gönderilmez; sadece erişim anahtarı doğrulaması ve kullanım metadata'sı işlenir.

`thaimcp-access` Edge Function kriptografik rastgele 12 alfanümerik karakter üretir. Düz anahtar sadece oluşturma/yenileme yanıtında bir kez döner. DB'de SHA-256, 3 karakter önek, etiket, aktiflik, süre sonu, kullanım sayacı/zamanı ve iptal bilgisi bulunur. Liste hash içermez. Yenileme eski anahtarı atomik iptal eder; iptal edilmiş anahtar tekrar açılamaz. Süresi geçmiş/pasif/iptal/geçersiz anahtar reddedilir.

RLS açık, anon/authenticated tablo ve RPC yetkileri kapalıdır. Güvenilir RPC yalnız service_role tarafından çağrılır. Yönetici JWT'si Auth sunucusundan doğrulanır, `thaimcp_admins` üyeliği DB'de kontrol edilir; frontend yönetici rolü veremez. Publishable key genel ayardır; service key yalnız Edge Function ortamındadır. Yönetici parolası, JWT, service key ve düz erişim anahtarı repoda tutulmaz. Yönetici panelinde oluştur/listeler, aktif/pasif, iptal, yenileme, süre sonu ve kullanım bilgileri vardır.

IP özetiyle 30/dakika, toplam 600/dakika ve araştırma anahtarıyla 10/dakika sunucu sınırı uygulanır. Yerel doğrulama 20/dakikadır. Her araştırmada Edge Function'a yeniden `consume` çağrılır; frontend kapısını atlamak erişim sağlamaz. Erişim hizmeti yoksa araştırma kapalı kalır. Origin/Host, yerel oturum kodu ve tek araştırma kilidi de korunur.

## Gizlilik ve kanıt sınırları

Regex maskeleme T.C. kimlik, telefon, e-posta, IBAN, kart ve etiketli kişi/adres/dosya bilgilerini kapsar; tüm etiketsiz isimleri yakalayamaz. Olayı anonim anlatın. Dış sorgular sadece onaylı kısa hukuk kavramlarıdır; olay yalnız yerel modelde işlenir.

Model karar kimliği, tarih veya serbest hukuki iddia üretemez. Metadata resmî istemciden alınır. SHA-256/erişim zamanı metnin kaynaktan alındığını kanıtlar; hukuki bağlayıcılık veya güncellik garantisi vermez. Kanun-madde ilişkisi kaynakta görünen aday bağlantıdır. Dilekçe tamamlanacak alanlar ve doğrulanmış alıntılar içeren araştırma taslağıdır.

## Kurulum ve yayın

Migration: `supabase/migrations/202609280001_thaimcp_access.sql`; Edge: `supabase/functions/thaimcp-access/index.ts`. Yönetici Auth kullanıcısı önce oluşturulur, UID `thaimcp_admins` tablosuna güvenilir sunucu/SQL üzerinden eklenir. Parola admin Auth API ile değiştirilir; repoya yazılmaz. Edge platform JWT anahtarı denetimi kapalıdır çünkü publishable key desteklenir; yönetici JWT denetimi kod içinde zorunludur. `supabase/config.toml` ayarı bunu belgelendirir.

`frontend/config.js` ve `config/access.public.json` yalnız Supabase URL/publishable key içerir. Özel yerel ayarlar `config/access.json` ignore kapsamındadır. Edge service kimliğini Supabase ortamından alır. Netlify yalnız `frontend/` yayınlar; main bağlı otomatik deploy kullanılır. DNS/domain ayarları değiştirilmez.

## Kontroller

```text
python -m unittest discover -s tests -p "test_*.py" -v
node tests/security.test.mjs
python tests/live.py
python tests/access_live.py
python tests/benchmark.py
node --check frontend/app.js
node --check frontend/admin.js
```

SQL bütünlük/yetki kontrolleri `supabase/tests/access.sql` içinde rollback ile çalışır. Canlı kaynak testleri sonuç yoksa başarılı sayılmaz. Model zaman aşımı fallback başarı olarak saklanmaz; kaynak araştırmasının başarısı ayrı raporlanır. Son ölçümler `tests/performance.json`, açıklamalar `TEST_REPORT.md` ve `IMPROVEMENTS.md` içindedir.

## Açık kaynak / attribution


* [aydincan/turk-hukuku-ictihat-mcp](https://github.com/aydincan/turk-hukuku-ictihat-mcp), sürüm 0.4.0, commit `5dac35d11e5a600a66171cf501cf6a635250f71c`, MIT, © 2026 Aydın Can Polatkan. Fork: https://github.com/ahmetaliunaall-prog/turk-hukuku-ictihat-mcp. UYAP, Danıştay ve AYM arama/getirme mekanizmaları korunur. MCP v1 `FastMCP` import'u SDK 2.2 `MCPServer` olarak uyarlanmıştır. İlgili gizlilik ve sorumluluk metinleri korunur.
* Özgün proje [saidsurucu/mevzuat-mcp](https://github.com/saidsurucu/mevzuat-mcp), © 2025 saidsurucu, MIT. Özgün depo bu çalışma sırasında git ile erişilebilir değildi; [turkgent/mevzuat-mcp](https://github.com/turkgent/mevzuat-mcp) forkundaki commit `7b2f13ff90e36089278f07518dc607b43003a3d9` kullanılır. Fork: https://github.com/ahmetaliunaall-prog/mevzuat-mcp. Bedesten arama, madde ağacı ve madde getirme payload'ları korunur. Ağır MarkItDown yerine hafif markdownify HTML dönüşümü kullanılır. Eski sunucu fastmcp 2.9.2 kullanıyordu; birleşik adapter SDK 2.2 ile araçları yeniden sunar.

Üçüncü taraf lisansları `vendor/*/LICENSE` altında aynen korunmuştur. Mevzuat API'sinin başlıksız madde düğümleri için `title` alanı nullable yapılmıştır; boş başlık yerine model kaynakta olmayan başlık üretmez. Yeni `legal_mcp/`, `local_ai/`, arayüz ve test katmanları bu projenin geliştirmeleridir. Kaynak sitelerin erişim koşulları geçerlidir; CAPTCHA/erişim engeli atlatılmaz.
