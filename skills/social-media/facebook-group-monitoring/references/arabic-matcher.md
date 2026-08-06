# Arabic Dialect Matcher — full reference (RASD engine)

Verified 16/16 on fixtures via `node scripts/test_arabic_matcher.js`. Implemented in
both Python (`arabic_matcher.py`) and JS (`matcher.js`) — keep in sync, same fixtures.

## normalize(text)
```
NFKC; [أإآ]→ا; ة→ه; ؤ→و; ئ→ي; strip ـ (tatweel); strip \u064B-\u0652 (diacritics);
typo fixes e.g. عفس→عفش; collapse whitespace.
```

## Concept dictionary structure
```python
CONCEPTS = {
  "moving":      {"label": "🚛 نقل عفش / أثاث",  "keywords": [...], "stem": "نقل",  "seller_terms": ["شركتنا","متخصصه","احنا",...]},
  "plumbing":    {"label": "🔧 سباك / مواسير",   "keywords": [...], "stem": "سباك", "seller_terms": [...]},
  "electrician": {"label": "⚡ كهربائي",          "keywords": [...], "stem": "كهرب", ...},
  "dentist":     {"label": "🦷 دكتور أسنان",     "keywords": [...], "stem": "اسنان", ...},
  "ac":          {"label": "❄️ تكييف",           "keywords": [...], "stem": "تكييف", ...},
  "cleaning":    {"label": "🧽 تنظيف / مكافحة",  "keywords": [...], "stem": "نظف", ...},
  "datawork":    {"label": "💻 شغل ريموت / داتا", "keywords": ["data annotation","appen","remotasks","telus","outlier","oneforma","شغل من البيت","وظايف ريموت","الدفع نزل","قبضت",...], "stem": "شغل", ...},
}
```
Rule: keyword hit OR (stem hit AND buyer signal present). Seller_terms deduct 25 from score.

## Signal lists (Egyptian Arabic)
- **BUYER**: عايز/عاوز, محتاج, في حد, حد يرشح, مين يعرف, مين عندو, حد عنده, في وظيفه/فيه وظيفة, مشكله في, عايزه/عاوزه, محتاجين/عايزين, ياريت حد, بدور/ادور, لو حد يعرف, ...
- **SELLER**: شركتنا, احنا, بنقدم, خدماتنا, كلمونا, خصم, عروضنا, للتواصل, على الخاص, تواصل معانا, ...
- **HOT**: ضروري, بسرعه, النهارده/النهاردة, مستعجل, فورا, بكره/بكرة, دلوقتي, كام سعر/كلفه/تكلفه, تليفون/رقم/واتساب, ...
- **NOISE** (hard skip): للبيع, مطلوب للشراء, انا بعرض, عندي عربيه للبيع, فيديو, كومنت, ...

## Scoring
```
base 60
+20 buyer-only signal        −40 seller-only signal        +5 ambiguous both
−25 any concept seller_term  +25 any hot signal            +5 contains ؟/?
−15 len(raw) < 12
```
## Classify
- ≥90 🔥 hot lead (reply first) —  ≥70 ✅ clear lead —  ≥50 ⚠️ maybe —  else ❌ skip
- Seller ads land at −5..20 → automatically ❌ (this is why a tiered classifier matters:
  the pre-fix version sent every match as ⚠️, alerting on competitors)

## Alert message format (Telegram HTML)
```
{🔥/✅} <b>{label}</b> — {heat}
📝 "{post text ≤500 chars}"
👥 {group}   🔗 {url}
💬 <b>رد جاهز:</b> <i>أهلاً بيك! {business} — {label} متاحين فوراً. لو مهتم ابعت التفاصيل على {phone}</i>
⚡ رصد RASD
```
The ready-made copy-paste reply is the selling feature — always include it.

## Fixture highlights (16 cases)
- "عايز حد ينقل عفش من مدينة نصر للفيوم بكرة الصبح ضروري" → 🔥 105
- "شركتنا متخصصة في نقل العفش بأفضل الأسعار كلمونا 0100" → ❌ −5 (seller ad)
- "عايزه حد ينضف الشقة قبل ما اجي من السفر" → ✅ 80 (verb-form keyword ينضف)
- "محتاج انقل موبيليا من اسكندرية للقاهرة كام التكلفة؟" → 🔥 110 (price ask = hot)
- "حد عنده مشكله في الدفع من Appen؟" → ✅ 85 (datawork domain)
- "شركة توظيف بتقدم وظايف ريموت بخصم 50%" → ❌ 20 (seller)
