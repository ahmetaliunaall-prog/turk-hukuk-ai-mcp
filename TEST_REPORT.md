# Doğrulama raporu — 28 Eylül 2026

**23 otomatik test + 8 canlı kontrol başarılı.** Canlı birleşik araştırma: 10 doğrulanmış kaynak (3 mevzuat maddesi + 7 karar), 18 MCP araç çağrısı, kaynağa birebir eşleşen 3 Qwen seçimi, hata listesi boş. Birleşik araştırma yaklaşık 327 saniye sürdü; bu donanımda birkaç dakika bekleme normaldir.

| İstenen kontrol | Sonuç / kanıt |
|---|---|
| 1. Ollama bağlantısı | PASS — localhost API ve model listesi |
| 2. Qwen 3 1.7B yanıtı | PASS — gerçek yerel model yanıtı |
| 3. İçtihat MCP başlatma | PASS — ayrı stdio sunucu, 2 araç |
| 4. Mevzuat MCP başlatma | PASS — ayrı stdio sunucu, 3 araç |
| 5. Birleşik MCP | PASS — SDK 2.2.0 üzerinde 5 araç |
| 6. Tool discovery | PASS — gerçek MCP ClientSession ile ayrı ve birleşik sunucular |
| 7. İçtihat arama | PASS — canlı UYAP sorgusu |
| 8. Karar getirme | PASS — aramadan gelen kimlikle resmî tam metin |
| 9. Mevzuat arama | PASS — Bedesten üzerinden 4857 |
| 10. Madde getirme | PASS — kaynak ağacından elde edilen madde kimliğiyle metin |
| 11. Qwen → MCP | PASS — Qwen'in yapılandırılmış planı gerçek MCP çağrılarına dönüştürüldü |
| 12. Mevzuat + içtihat | PASS — örnekte iki kaynak türünün tam metinleri getirildi |
| 13. Çoklu sorgu | PASS — model planı ve sınırlı çoklu arama |
| 14. Duplicate temizleme | PASS — kaynak türü + kaynak kimliği bazında |
| 15. Alaka sıralaması | PASS — konu/sorun/alt konu/kavram/kanun eşleşmesi testi; ek mahkeme ve tarih sinyalleri |
| 16. Kaynak doğrulama | PASS — kaynak alan adı, metin, hash ve birebir alıntı kontrolü; hayalî alıntı reddi |
| 17. Hassas veri | PASS — TC, telefon, e-posta, IBAN, etiketli adres ve kişi; dış sorgu reddi |
| 18. Dilekçe akışı | PASS — canlı birleşik araştırmadan kaynaklı taslak; eksik alanlar yer tutucu |
| 19. Web arayüzü | PASS — yerel/published sayfa, bağlantı göstergesi, dilekçe modu ve görsel kontrol; HTTP origin/Host/token testleri |
| 20. Netlify deploy | PASS — yeni GitHub deposundan otomatik yayın; .netlify.app HTTP 200 |

## Test sınırları

Bu sonuçlar hukuki doğruluk, güncellik, kesinleşme veya bütün soru türlerinde aynı başarı için garanti değildir. İşe iade örneği gerçek kaynaklarla denetlendi; diğer hukuk alanları ayrıca örneklerle doğrulanmalıdır. Qwen 1.7B bazen hatalı araştırma adayı üretebilir; kaynak doğrulama bu adayları nihai cevapta kaynak gibi sunmaz.

Maskeleme tüm etiketsiz kişi adlarını veya adres biçimlerini kapsamaz. Olası çelişki işaretlemesi hukukçu incelemesi gerektirir. Web arayüzünün her tarayıcıda HTTPS→localhost erişimi garanti edilmez; yerel ağ izni gerekebilir. Yerel web arayüzü bağımsız olarak çalışır. Browser'da tam 327 saniyelik araştırma yeniden çalıştırılmadı: canlı pipeline testi ve HTTP arayüz koruma/akış testleri ayrı yürütüldü.

Supabase ve DNS bu sürümde kullanılmadı/değiştirilmedi. Mevcut site/depolar üzerinde değişiklik yapılmadı. Sonuç metadata'sı bu raporda özetlenir; tam canlı karar metinleri ve olay metni GitHub'a yüklenmez.
