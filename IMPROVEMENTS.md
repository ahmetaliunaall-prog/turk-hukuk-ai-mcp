# Mevcut sistemin geliştirilmesi

## 1. Eski mimarinin sorunları

Baseline 354.438 saniye; 313.108 saniyesi iki model çağrısıydı. Kaynak çağrıları ardışık, 3 içtihat sorgusu/2 mevzuat adayı dardı. Kamu kaynağı önbelleği ve kullanıcı anahtar sistemi yoktu. Vendor istemcileri ve lisansları korunarak üst katmanlar değiştirildi.

## 2. Yapılan değişiklikler

`planning.py`: kişisiz terim aileleri/Türkçe eşleşme. `cache.py`: TTL kamu kaynak belleği. `transport.py`/`adapters.py`: paylaşılan HTTP/sınırlandırma/429. `orchestrator.py`: MCP önce bağlantı, kısa model bütçesi, paralel tarama, dedup/provenance, metadata ön sıralama, seçilmiş tam metinler ve ölçümler. `evidence.py`: açıklanabilir puan/birebir pasaj. `web.py`/`access.py`: araştırma başına güvenilir erişim ve gerçek NDJSON ilerleme. Frontend kartları/yönetici paneli eklendi.

## 3. Performans değişimi

354.438 → 61.868 saniye soğuk (%82.5 düşüş), 30.561 saniye sıcak. 23 soğuk HTTP denemesi daha geniş taramadır; sıcak 21 önbellek isabeti/2 deneme. Araç eşzamanlılığı en fazla 3; UYAP tek istek/2.2 saniye. Model zaman aşımı açık gösterilir. 97 karar/17 kanun adayı; 9/9 soğuk, 10/10 sıcak doğrulanmış kaynak. Ayrıntı `tests/performance.json`, tekrar `tests/benchmark.py`.

## 4. Arama doğruluğu değişimi

Modelin tek sorgusuna bağlılık kaldırıldı. Konu/kavram/kanun/madde, başlık/tam metin, mahkeme/daire/tarih puanları açıklanır. Az adayda ek sayfa/mahkeme araştırılır. Tekrarlar birleştirilirken sorgu desteği korunur. Mevzuat numarası/adı/içerik ifadeleri taranır ve ilgili maddeler seçilir. Fuzzy eşleşme alıntıyı değiştirmez. Gerçek benchmark geniş aday/doğrulanmış metin verdi; bağımsız hukuki precision/recall ölçülmedi.

## 5. Güvenlik değişiklikleri

12 karakter crypto random anahtarın yalnız SHA-256 özeti DB'de, düz anahtar bir kez gösterilir. Backend aktiflik/expiry/iptal/usage/rate denetler. Araştırma `consume` gerektirir; frontend kapısını aşmak işe yaramaz. Yönetici JWT'si gerçek Auth servisinden doğrulanır, DB üyeliği zorunludur. Yerel oturum/Host/origin/kilit korunur. Service key frontend'e girmez; olay Supabase'e gönderilmez.

## 6. Supabase yapısı

Mevcut proje `ztkopywelwximjiopdci`; yalnız yeni `thaimcp_admins`, `thaimcp_api_keys`, `thaimcp_usage`, iki trusted RPC ve `thaimcp-access`. Migration uygulandı, RLS/grant engelleri test edildi. Diğer tablo/işlevler korunur. İstenen mevcut Auth kullanıcısı yönetici yapıldı, parola yetkili API ile değiştirildi; parola repoda tutulmaz.

## 7. Netlify deploy

Mevcut proje https://turk-hukuk-ai-mcp.netlify.app; main bağlı yayın, publish `frontend/`, CSP Supabase/localhost. DNS/domain ve diğer projeler değiştirilmez. Yerel model Netlify'a taşınmaz. Yayın doğrulaması TEST_REPORT teslim notuna işlenir.

## 8. Test sonuçları

40 birim testi PASS; Node gerçek Edge güvenlik kontrolleri PASS; 8 canlı kaynak/8 canlı Supabase kontrolü PASS; gerçek DB rollback SQL PASS. RAM baskılı ilk MCP test denemesi başarısızdı; düzeltme sonrası tekrar geçti. Qwen planı benchmarkta zaman aşımı, bir karar HTTP 429; başarılı gibi gösterilmez. Ayrıntılı kapsam/sınırlar TEST_REPORT içinde.
