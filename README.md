# Türk Hukuk AI MCP

Türk hukukunda içtihat ve mevzuatı birlikte araştıran, Windows üzerinde yerel Qwen 3 1.7B kullanan hafif sistem. Yeni proje deposu: https://github.com/ahmetaliunaall-prog/turk-hukuk-ai-mcp

## Çalıştırma

`start.cmd` dosyasını açın. Yerel arayüz: http://127.0.0.1:8765

Python 3.14, MCP SDK 2.2.0 ve mevcut Ollama kullanılır. Yeni model indirilmez. Ana model `qwen3:1.7b`; 0.6B seçilmez. Eksik bağımlılıklar için `python -m pip install -r requirements.txt`; zaten kurulu paketleri yeniden kurmayın. Bu ortamda yalnızca eksik `httpx` ve hafif HTML dönüştürücü `markdownify` eklendi.

Netlify arayüzü yerel sunucu çalışırken kullanılabilir. `config/local.example.json` dosyasını `config/local.json` olarak kopyalayın ve yalnızca yeni Netlify origin'ini yazın. Netlify arayüzünde **Bağlantı ayarları** üzerinden yerel uygulamanın gösterdiği oturum kodunu girin. Kod oturum başına yenilenir ve tarayıcı belleğinde tutulur. Tarayıcının yerel ağ erişim izni gerekebilir. HTTPS→localhost kısıtı olan tarayıcılarda yerel arayüzü kullanın. Ollama CORS ayarı değiştirilmez.

## Mimari

Model kaynak pasajlarının kimliklerini seçer; birebir alıntı metni kaynak tablosundan alınır. Böylece uzun metni modelin yeniden üretmesi gerekmez. Kaynak sıra puanı sorun/konu/alt konu/kavram/kanun eşleşmeleri, uygun mahkeme/daire ve düşük ağırlıklı tarih sinyaliyle açıklanabilir; ağır embedding kullanılmaz.

Kullanıcı → yerel maskeleme → Qwen hukuki problem/araştırma planı → MCP istemcisi → birleşik MCP → mevcut içtihat/mevzuat istemcileri → tekrar temizleme → bağlamsal sıralama → kaynak metni doğrulama → Qwen alıntı seçimi → kaynaklı araştırma taslağı.

`local_ai/`: localhost Ollama ve HTTP köprüsü. `legal_mcp/`: adapter, MCP sunucu/istemci, araştırma, kaynak ve gizlilik katmanları. `vendor/`: lisanslı kaynak istemcileri. `frontend/`: bağımlılıksız web arayüzü. `config/`: yerel ayar örneği. `tests/`: birim ve canlı testler.

MCP araçları: `ictihat_ara`, `karar_getir`, `search_mevzuat`, `get_mevzuat_article_tree`, `get_mevzuat_article_content`. Birleşik sunucu: `python -m legal_mcp.server`. Modüller ayrı da başlatılabilir: `python -m legal_mcp.server ictihat` / `mevzuat`.

Qwen şemalı JSON ile dava türü, konu, alt konu, hukuki sorun, kavramlar, mevzuat önerileri ve çoklu sorgular üretir. Orchestrator bu planı sınırlandırılmış MCP çağrılarına çevirir. Modelin kanun/madde önerileri kaynak sayılmaz. Arama sonuçlarından alınan kimliklerle tam metinler getirilir. Arama sayfası başına 10–20 kaynak; en fazla 3 içtihat sorgusu, 2 mevzuat araştırması. `Daha fazla karar` sonraki sayfayı getirir; önceki sonuçlarla kalıcı birleşik geçmiş tutulmaz.

## Kaynak ve gizlilik sınırları

Modelden gelen serbest hukuki iddia gösterilmez. Yalnızca doğrulanmış kaynak kimliğine bağlı ve kaynak metninde birebir bulunan alıntılar kabul edilir. Kaynak metadata'sı adapter'dan alınır; modelin karar numarası veya tarih üretmesine izin verilmez. SHA-256 ve erişim zamanı kaydedilir; bu yalnızca metnin resmî kaynaktan alınmasını doğrular, kararın kesinleşmesi veya mevzuatın güncelliğini doğrulamaz. Olası çelişkiler iki kaynaktan doğrulanmış alıntılarla inceleme önerisi olarak gösterilir; otomatik hukuki çelişki hükmü verilmez. Kanun/madde ilişkisi yalnızca karar metninde iki belirteç de bulunduğunda aday bağlantıdır; semantik bağ ayrıca incelenmelidir.

Maskeleme T.C. kimlik, telefon, e-posta, IBAN, kart ve etiketli adres/kişi/dosya bilgilerini kapsar. Etiketsiz isimler ve her adres biçimi güvenilir biçimde tespit edilemez: kullanıcı kişileri anonim anlatmalıdır. Sorgular sadece genel hukuki kavramlar olmalıdır; model bu yönde sınırlandırılır ve belirgin kişisel veri taşıyan dış sorgular reddedilir. Kullanıcı olay metni yalnızca yerel Ollama'ya gider. Araştırma geçmişi, olay metni, oturum kodu veya müvekkil belgesi Supabase/Netlify/GitHub'a kaydedilmez. Supabase ilk sürümde gerekli olmadığı için kullanılmaz; mevcut veritabanı değişmez.

Yerel sunucu sadece `127.0.0.1:8765` üzerinde dinler. Host ve origin kontrolü, oturum kodu ve tek araştırma kilidi bulunur. Tünel, public AI endpoint, port yönlendirme, Docker, embedding, vektör veritabanı yok. Dilekçe çıktısı tamamlanacak alanlar ve doğrulanmış kaynak alıntıları içeren **araştırma taslağıdır**, mahkemeye hazır belge değildir.

## Açık kaynak / attribution

* [aydincan/turk-hukuku-ictihat-mcp](https://github.com/aydincan/turk-hukuku-ictihat-mcp), sürüm 0.4.0, commit `5dac35d11e5a600a66171cf501cf6a635250f71c`, MIT, © 2026 Aydın Can Polatkan. Fork: https://github.com/ahmetaliunaall-prog/turk-hukuku-ictihat-mcp. UYAP, Danıştay ve AYM arama/getirme mekanizmaları korunur. MCP v1 `FastMCP` import'u SDK 2.2 `MCPServer` olarak uyarlanmıştır. İlgili gizlilik ve sorumluluk metinleri korunur.
* Özgün proje [saidsurucu/mevzuat-mcp](https://github.com/saidsurucu/mevzuat-mcp), © 2025 saidsurucu, MIT. Özgün depo bu çalışma sırasında git ile erişilebilir değildi; [turkgent/mevzuat-mcp](https://github.com/turkgent/mevzuat-mcp) forkundaki commit `7b2f13ff90e36089278f07518dc607b43003a3d9` kullanılır. Fork: https://github.com/ahmetaliunaall-prog/mevzuat-mcp. Bedesten arama, madde ağacı ve madde getirme payload'ları korunur. Ağır MarkItDown yerine hafif markdownify HTML dönüşümü kullanılır. Eski sunucu fastmcp 2.9.2 kullanıyordu; birleşik adapter SDK 2.2 ile araçları yeniden sunar.

Üçüncü taraf lisansları `vendor/*/LICENSE` altında aynen korunmuştur. Mevzuat API'sinin başlıksız madde düğümleri için `title` alanı nullable yapılmıştır; boş başlık yerine model kaynakta olmayan başlık üretmez. Yeni `legal_mcp/`, `local_ai/`, arayüz ve test katmanları bu projenin geliştirmeleridir. Kaynak sitelerin erişim koşulları geçerlidir; CAPTCHA/erişim engeli atlatılmaz.

## Testler

Küçük modelin alıntısı kaynakla birebir eşleşmezse sistem, hata bilgisini göstererek kaynak metninden doğrudan ilgili pasajları seçer. Bu CPU seçimi hukuki yorum veya semantik doğrulama değildir. İşe iade için resmî API'de teyit edilen 4857, madde 18/19/20 araştırma rehberi kullanılır. Modelin diğer kanun önerileri doğrulanmadan kaynak olarak gösterilmez.

`python -m unittest discover -s tests -p "test_*.py" -v`

`python tests/live.py` canlı Ollama, Qwen, MCP araçları, kaynak arama/getirme ve birleşik dilekçe araştırmasını denetler. Canlı veri yoksa test başarılı sayılmaz. Canlı çıktı `tests/live-report.json` (git tarafından yok sayılır). `TEST_REPORT.md` son doğrulama durumunu açıklar.

Netlify `netlify.toml` ile yalnızca `frontend/` klasörünü yayınlar. GitHub main değişiklikleri bağlı yeni Netlify projesine deploy edilir. DNS ve özel domain ayarı yapılmaz.
