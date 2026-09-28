# Doğrulama raporu — 28 Eylül 2026

## Otomatik ve canlı kontroller

| Kontrol | Sonuç |
|---|---|
| Başlangıç birim testleri | 23/23 PASS, 21.366 saniye |
| Son birim testleri | 40/40 PASS, 41.728 saniye |
| Gerçek Edge koduyla Node güvenlik testi | PASS; 1000 rastgele anahtar, hash, JWT/origin/olay reddi, tek gösterim/liste gizliliği |
| Canlı Ollama ve resmî kaynak testleri | 8/8 PASS; gerçek kısa Qwen yanıtı 37.68 saniye; arama/karar/kanun/ağaç/madde ve birleşik taslak |
| Gerçek Supabase negatif erişim testleri | 8/8 PASS; geçersiz key, JWT yok/sahte, yanlış origin, üç tablo ve RPC yetki reddi |
| Supabase rollback SQL | PASS; RLS/grant, yönetici yetkisi, create/list, consume/sayaç, expiry/pasif/iptal/rotate/rate |
| Python derleme ve frontend JS sözdizimi | PASS |
| Yönetici hesabı | Yetki DB'de doğrulandı; istenen parola Auth admin API ile ayarlandı; panelde gerçek giriş ve anahtar oluşturma PASS |
| Giriş kapısı | Gerçek UI'de geçersiz anahtar reddi ve geçerli anahtar kabulü PASS |

Canlı kaynak testi, modelin araştırma planı ürettiğini zorunlu başarı koşulu saymaz. Modelin kısa doğrudan yanıtı başarılıdır; aşağıdaki araştırma ölçümlerinde plan süre aşımına uğramış, deterministik plan kullanılmıştır.

## Ölçülen performans

Aynı anonim işe iade sorusu, aynı Windows/4 GB RAM, baseline commit `9a765a8`. Pipeline ölçümü frontend ve Supabase doğrulama gecikmesini içermez. Tam ölçüm `tests/performance.json`; tekrar `python tests/benchmark.py`.

| Ölçüm | Eski | Yeni soğuk | Yeni sıcak |
|---|---:|---:|---:|
| Toplam saniye | 354.438 | 61.868 | 30.561 |
| Qwen planı | 175.211 | 9.298 | 9.140 |
| Qwen pasaj seçimi | 137.897 | 0 (atlanır) | 0 (atlanır) |
| HTTP denemeleri | 20 | 23 | 2 |
| Kamu kaynak önbellek isabeti | 0 | 0 | 21 |
| Azami araç eşzamanlılığı | 1 | 3 | 1 |
| Karar / kanun adayı | — | 97 / 17 | 97 / 17 |
| Sunulan / doğrulanan kaynak | 10 / 10 | 9 / 9 | 10 / 10 |
| Birebir kabul edilen alıntı | — | 4 | 4 |

Yeni soğuk süre yaklaşık %82.5 azaldı. Eski Qwen toplamı 313.108 saniye (%88.3) idi. Yeni içtihat/mevzuat arama duvar süresi 9.163/8.510; tam metin duvar süresi 25.408/25.110 saniye; aşamalar örtüşür, toplanmaz. Araç süre toplamları paralellik nedeniyle duvar süresinden büyük olabilir.

## Başarısız denemeler ve sınırlar

- RAM baskısında benchmark ile eşzamanlı ilk son-test denemesi: 1/40 FAIL, MCP stdio başlangıcı 60 saniyede zaman aşımı. Model çağrısı iptal edilebilir akışa geçirildi, keep_alive=0 ve MCP bağlantısı modelden önce kuruldu; model boşta ardışık yeniden çalıştırma 40/40 PASS. İlk başarısız deneme başarılı sayılmaz.
- Yeni benchmark Qwen planı 8 saniyelik bütçeyi aştı; HTTP kurulumu/zamanlama dahil yaklaşık 9 saniye görüldü. Yerel hukuk terim planına dönüldü; ikinci Qwen çağrısı atlandı. Bu başarılı model analizi değildir.
- Soğuk benchmarkta bir karar isteği HTTP 429 verdi; kalan 9 kaynak doğrulandı. Daha sık istek deneyleri daha fazla 429 üretti; son sürüm tek host isteği/2.2 saniye aralık kullanır. Her isteğin başarısı garanti edilmez.
- `node --check` doğrudan TypeScript üzerinde çalışmadı. Gerçek Edge modülü Node stripTypeScriptTypes üzerinden çalıştırılarak kontroller geçti; başarısız komut PASS diye raporlanmaz.
- Mevzuat API'si madde ağacını tek cevapta verir; sadece ilgili madde içerikleri seçilir. Sunucudan ağacın alt dalını indirme özelliği yoktur.
- Fuzzy sıralama ve geniş aday taraması test edildi; bağımsız hukuki precision/recall veri kümesi ölçülmedi. İşe iade dışındaki bütün alanlar için başarı iddiası yoktur.
- Netlify statik arayüzdür. Araştırma için aynı bilgisayarda yerel sunucu gerekir. Tarayıcı localhost izni gerekebilir.
- Alıntı doğrulama güncellik/bağlayıcılık veya tüm isimlerin maskelenmesi garantisi değildir.

## Teslim doğrulaması

Yerel gerçek UI araştırması 71.604 saniyede 7 doğrulanmış kaynak gösterdi; 6 kartta birebir pasaj, künye ve resmî bağlantılar görünür. Model zaman aşımı ve 3 resmî 429 açık bildirildi. Kullanım sayacı 1 oldu. Test anahtarı pasifleştirildiğinde backend reddetti; yenileme eski anahtarı iptal etti. Geçici test anahtarları iptal edildi. Kullanıcının diğer anahtarları korunur. Production yayın doğrulaması aşağıya eklenir.
