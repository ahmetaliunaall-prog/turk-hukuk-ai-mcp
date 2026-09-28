# Türk Hukuk AI MCP — çalışma kuralları

## Kapsam ve kaynaklar

Bu depo tamamen yeni Türk hukuk AI projesidir. Başka kişisel hukuk sitesi depolarını, mevcut Netlify projelerini veya DNS/Metunic ayarlarını değiştirmeyin. Yeni proje URL'si https://turk-hukuk-ai-mcp.netlify.app; GitHub https://github.com/ahmetaliunaall-prog/turk-hukuk-ai-mcp.

Kaynak istemcilerini sıfırdan yazmayın. `vendor/ictihat` Aydın Can Polatkan'ın MIT lisanslı `aydincan/turk-hukuku-ictihat-mcp` projesidir. `vendor/mevzuat` saidsurucu'nun MIT lisanslı projesinin erişilebilir `turkgent/mevzuat-mcp` forkundan alınmıştır. Ayrıntılar, commit kimlikleri, forklar, yerel uyarlamalar ve lisanslar README'dedir. Copyright ve LICENSE dosyalarını koruyun. Resmî kaynak erişim koşullarına uyun; CAPTCHA veya erişim engeli atlatmayın.

## Mimari

`frontend/` bağımlılıksız Türkçe web arayüzü; `local_ai/` yerel Ollama ve HTTP köprüsü; `legal_mcp/` adapter, MCP client/server, orchestrator, kaynak doğrulama ve maskeleme; `vendor/` yeniden kullanılan veri erişim kodları; `config/` ayar örnekleri; `tests/` anlamlı testler.

Akış: olay → yerel maskeleme → Qwen yapılandırılmış problem ve plan → MCP tool discovery → planın sınırlı araç çağrılarına çevrilmesi → resmî mevzuat ve karar arama/getirme → tekrar temizleme → bağlamsal sıralama → kaynak metni doğrulama → Qwen birebir alıntı seçimi → araştırma/dilekçe taslağı.

Qwen'in ilk model planı tek başına doğruluk kanıtı değildir. Küçük modelin işe iade sorularında yanlış kanun adı üretmesini azaltmak için `analyze` içinde resmî API'de adı/kimliği teyit edilmiş 4857 ve 18/19/20 maddelerini **araştırma adayı** olarak veren dar bir rehber vardır. Yeni rehber kayıtlarını yalnızca resmî kaynaktan teyit ederek ekleyin. Bu rehber yapay zekâ problem analizinin yerine geçmez.

## Yerel çalışma sınırları

Windows, yaklaşık 4 GB RAM, Python 3.14. Mevcut MCP SDK **2.2.0** kullanılır: `mcp.server.mcpserver.MCPServer`, snake_case `is_error`/`structured_content` alanları. Eski FastMCP örneklerini doğrudan kopyalamayın. Kurulu API'yi inceleyin; SDK sürümünü düşürmeyin.

Ana model **qwen3:1.7b**, yalnızca **http://127.0.0.1:11434**. 0.6B'yi ana model yapmayın; yeni veya büyük model indirmeyin; Ollama'yı yeniden kurmayın. Bağlam 2048 token, tahmin 600 token, tek eşzamanlı araştırma; düşük sıcaklık. Kaynak sentezine sınırlı sayıda ve uzunlukta metin parçası verilir. Büyük embedding, vektör DB, Docker veya ağır framework eklemeyin. Var olan paketleri yeniden kurmayın.

Web köprüsü yalnızca **127.0.0.1:8765** üzerinde dinler. Ollama'yı internete açmayın, tünel/ngrok/Cloudflare Tunnel/port forwarding kullanmayın. `start.cmd` veya `start.ps1` çalıştırılır. Yerel origin ve Host denetimini, geçici oturum kodunu ve tek araştırma kilidini koruyun. HTTPS Netlify arayüzü yerel ağ erişim izni gerektirebilir; tarayıcı kısıtlarında yerel arayüz çalışmaya devam etmelidir.

## Kanıt ve gizlilik

Modelin karar numarası, tarih, mahkeme, kanun veya madde üretmesini kaynak olarak kabul etmeyin. Araştırma önerileriyle gerçekten getirilen kaynakları ayırın. Kimlikler arama sonuçlarından alınır. Yalnızca izinli resmî alan adları, başarıyla alınan yeterli metin ve kaynağa birebir eşleşen alıntılar doğrulanır. SHA-256 ve erişim zamanı hukuki güncellik/bağlayıcılık garantisi değildir. Kaynakta bulunmayan serbest hukuki iddia gösterilmez. Olası çelişkiler iki doğrulanmış alıntıyla hukukçu incelemesine sunulur.

Kişisel veri yerelde maskelenir. Regex maskelemesi tüm isim ve adresleri garantiyle yakalayamaz; etiketsiz isimler için kullanıcı anonim anlatmalıdır. Dış kaynak sorguları kısa ve kişisiz hukuk kavramlarıdır; olay metni yalnızca yerel Ollama'ya gider. Müvekkil metni, bağlantı kodu, kimlik bilgisi veya canlı araştırma sonucu GitHub'a yüklenmez. `.env`, `config/local.json`, `tests/live-report.json`, `tests/research-live.json` ve günlükler ignore kapsamındadır. Anahtarları asla hard-code etmeyin. Supabase service-role frontend'e konmaz. İlk sürüm Supabase kullanmaz. İleride gerekirse yalnızca yeni `thaimcp_*` tabloları, kullanıcıya bağlı RLS ve minimum anonim metadata kullanın; mevcut tabloları değiştirmeyin.

Dilekçe çıktısı **araştırma taslağı** olarak etiketlenir. Mahkeme, taraf, delil, talep ve süre bilgilerini model uydurmaz; eksik alanlar hukukçu tarafından doldurulur.

## Kontroller ve yayın

Qwen'in alıntısı doğrulanamadığında kaynak metninden birebir pasaj seçimi fallback olarak kullanılır. Bu durum `errors` içinde açık bildirilir. Bunu semantik AI sentezinin başarılı olması gibi raporlamayın; hukuki yorum veya doğruluk garantisi vermeyin.

`python -m unittest discover -s tests -p "test_*.py" -v`

`python tests/live.py`

`node --check frontend/app.js`

Canlı testleri yalnızca yeni değişiklik/hata gerektiriyorsa tekrarlayın. Resmî veri yoksa test başarılı sayılmaz. Ollama, 1.7B yanıtı, ayrı/birleşik MCP başlatma ve tool discovery, arama/getirme, ortak araştırma, tekrar temizleme, alaka, kaynak doğrulama, maskeleme, dilekçe, HTTP koruması ve UI doğrulanır. Netlify deploy kaydının terminal durumunu ve gerçek sayfa erişimini kontrol edin. GitHub bağlantılı yayın yalnızca yeni proje üzerinde yapılır; gizli veri frontend paketi içine girmemelidir. Son test durumu `TEST_REPORT.md` dosyasına dürüstçe yazılır.

İleride değişiklik yaparken mevcut testi ve çalışan veri istemcisini koruyun. Hukuki anlam, güncellik, otomatik çelişki analizi veya isim maskelemesi için garanti vermeyin. Kullanıcıya kısa, Türkçe, somut sonuç raporu sunun; başarısız/çalıştırılmamış kontrolleri açık belirtin. Başlangıç doğrulaması: 23 otomatik test ve 8 canlı kontrol başarılı; ayrıntılar `TEST_REPORT.md`. Örnek araştırma yaklaşık 327 saniye sürmüştür. Kimlik seçimine dayanan kaynak sentezinde en fazla 120 çıktı tokenı kullanılır.
