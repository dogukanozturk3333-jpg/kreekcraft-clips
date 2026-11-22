# ZEIPAN — marka sistemi

Her klip otomatik olarak ZEIPAN markasıyla çıkar. Hiçbir şeyi elle eklemen gerekmez.

## Her videoda ne var

| An | Ne oluyor |
|---|---|
| 0.0 – 1.7 sn | Sarı **Z** logosu yüzkamera ile oyun görüntüsünün birleştiği çizgide "pop" ederek belirir, içinden **ZEIPAN** yazısı kayarak çıkar ve geri girer. Kısa bir "whoosh + pop" sesi eşlik eder. Video ilk kareden başlar, izleyici beklemez. |
| Video boyunca | Küçük **Z** rozeti aynı yerde kalır. İçeriğin bize ait olduğunu gösterir ve başkası indirip yüklerse bizim logomuz üstünde kalır. |
| Kapanış (son 2.5 sn) | Üstte büyük logo ve **ZEIPAN** yazısı, ortada kampanyanın zorunlu twitch linki, altta **+ FOLLOW @ZEIPAN** butonu. Butona "dokunulur", buton **✓ FOLLOWING**'e döner ve zil sesi çalar. |

### Neden uzun intro yok?
Shorts, TikTok ve Reels'te izleyicinin çoğu ilk 1 saniyede kaydırıp geçer. Videonun başına konan 2–3 saniyelik bir intro izlenmeyi ciddi şekilde düşürür. Profesyonel klip kanalları bu yüzden markayı içeriğin **üstüne** koyar, önüne koymaz. Bizim açılış animasyonu da böyle çalışıyor.

Tam ekran intro dosyaları yine de hazır. Uzun YouTube videolarında ve derlemelerde (compilation) kullanılır:
- `intro-vertical-1080x1920.mp4` (1.2 sn, dikey)
- `intro-wide-1920x1080.mp4` (2 sn, yatay)

## Kanal görselleri (`art/`)
- `avatar-800.png`: profil fotoğrafı (YouTube, TikTok, Instagram)
- `youtube-banner-2560x1440.png`: YouTube kanal kapağı. Yazılar her cihazda görünen güvenli alanın içinde.
- `logo.png`: şeffaf arka planlı logo (1024 px)

## Ayarlar (`brand.json`)
- `handle`: Kapanıştaki **@zeipan** yazısı. Kanalın gerçek kullanıcı adı farklıysa burayı değiştir.
- `tagline`: Banner ve introdaki slogan.
- `colors`: Marka renkleri (sarı #FFE500, koyu #0B0B0F, beyaz).

Bir şey değiştirince `python3 tools/brand.py build` komutu bütün dosyaları yeniden üretir.

## Teknik
- `tools/brand.py`: Marka kitini üretir. `apply` komutu hazır bir klibe markayı sonradan ekler.
- `tools/render.py`: Yeni klipleri render ederken markayı otomatik ekler. Bir klipte istemezsen o klibin ayarına `"brand": false` yaz.
- `build/`: Animasyon kareleri. Otomatik üretilir, repoya eklenmez.
