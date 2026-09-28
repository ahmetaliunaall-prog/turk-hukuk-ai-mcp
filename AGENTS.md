# Çalışma kuralları

Mevcut turk-hukuk-ai-mcp mimarisini ve vendor veri istemcilerini koruyun. README attribution ve MIT lisanslarına dokunmayın. Başka kişisel site projeleri/DNS/domain değiştirilmez.

Windows 4 GB RAM, Python 3.14, MCP SDK 2.2.0 (`MCPServer`, snake_case çıktı alanları). Yalnız mevcut qwen3:1.7b/localhost kullanılır. Model, paket, embedding, Docker veya ağır framework indirmeyin. Tek araştırma; global araç eşzamanlılığı 3, UYAP hostu tek istek/2.2 saniye aralık. Kaynak 429'a saygı gösterin; erişim engeli atlatılmaz.

MCP araçlarını ve adapter payload/parse davranışlarını koruyun. Metadata ön sıralama → seçilmiş tam metin → doğrulanmış birebir pasaj akışını sürdürün. Türkçe fuzzy eşleşme sıralama içindir; alıntı kontrolü birebirdir. Model plan/kanun/madde önerisi kaynak değildir. Model 64 token/8 saniye plan, 32 token/4 saniye pasaj seçimi bütçesindedir. Model planı başarısızsa ikinci model çağrısı yapılmaz; açık fallback raporlanır. Sonuçları başarılı AI hukuki sentezi gibi sunmayın.

Önbellek yalnız kamu kaynakları/kişisiz sorgular için 256 kayıt/300 saniyedir. Olay/model yanıtı/geçmiş tutulmaz. Dış kaynak sorgularını izinli hukuk terimleriyle sınırlayın. Etiketsiz isim maskelemesi garanti değildir.

Yerel sunucu yalnız 127.0.0.1:8765, Ollama yalnız 127.0.0.1:11434. Tünel/public AI endpoint açılmaz. Her araştırmada yerel oturum, Host/origin ve uzak Edge `consume` doğrulaması gerekir. Frontend kapısı yetki kaynağı değildir; backend fail closed kalır.

Supabase yalnız thaimcp_* tabloları ve thaimcp-access işleviyle kullanılır. RLS ve anon/authenticated yetki engellerini koruyun. RPC sadece service_role. Yönetici JWT'sini Auth'tan doğrulayın ve DB üyeliğini kontrol edin. Service key/parola/JWT/düz erişim anahtarı repoya veya frontend'e konmaz. Anahtar crypto random 12 karakter, hash SHA-256; sadece bir kez yanıtlanır. İptal/expiry/usage/rate kontrolleri server tarafındadır. Hesap parola değişikliği aynı Supabase Auth kullanıcısının diğer uygulamalarını da etkileyebilir.

README, TEST_REPORT, IMPROVEMENTS ve ölçümleri değişiklikle güncelleyin. 40 birim testi, Node Edge güvenlik testi, 8 canlı kaynak kontrolü, 8 canlı erişim kontrolü ve rollback SQL kontrolleri vardır. Yeni değişiklik/gerekçe yoksa pahalı canlı testleri tekrar tekrar çalıştırmayın. Süre aşımı/429/çalıştırılmamış testleri dürüstçe bildirin. tests/live-report.json, research-live.json, config/local.json, config/access.json ve günlükler ignore kalır.

Netlify frontend/ yayınlar; bağlı main deploy'un terminal Published durumunu ve production sayfasını doğrulayın. Araştırma için kullanıcının yerel Qwen sunucusu gerekir. Kullanıcıya Türkçe, somut ve kısa sonuç verin. Hukuki doğruluk/güncellik garantisi vermeyin.
