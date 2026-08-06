#!/usr/bin/env node
/* Verify an Arabic matcher.js port: node scripts/test_arabic_matcher.js <path/to/matcher.js>
   Expects matcher to module.exports { matchPost, classifyAlert, normalize }. */

const path = process.argv[2] || "./matcher.js";
const { matchPost, classifyAlert } = require(path);

const TESTS = [
  ["عايز حد ينقل عفش من مدينة نصر للفيوم بكرة الصبح ضروري", "🔥"],
  ["محتاج سباك يصلح سخان في المعادي النهارده", "🔥"],
  ["في حد يرشحلي دكتور أسنان كويس في مدينة نصر؟", "✅"],
  ["شركتنا متخصصة في نقل العفش بأفضل الأسعار كلمونا 0100", "❌"],
  ["عندي عربية نقل للبيع موديل 2015", "❌"],
  ["بدور على فني تكييف شاطر يظبط التكييف في الشقة ضروري", "🔥"],
  ["عايزه حد ينضف الشقة قبل ما اجي من السفر", "✅"],
  ["صباح الخير يا جماعة", "❌"],
  ["مين يعرف سباك شاطر في المعادي؟ مستعجل", "🔥"],
  ["شركة نقل عفش محترمة للتواصل على الخاص", "❌"],
  ["محتاج انقل موبيليا من اسكندرية للقاهرة كام التكلفة؟", "🔥"],
  ["حد يرشحلي عيادة أسنان محترمة في التجمع؟", "✅"],
  ["حد عنده مشكله في الدفع من Appen؟", "✅"],
  ["في وظيفة Data Annotation شغل من البيت؟", "✅"],
  ["انا عندي خبره في Appen وبدور على شغل", "✅"],
  ["شركة توظيف بتقدم وظايف ريموت بخصم 50%", "❌"],
];

let pass = 0;
for (const [text, exp] of TESTS) {
  const v = matchPost(text);
  const got = classifyAlert(v);
  const ok = got === exp;
  if (ok) pass++;
  console.log((ok ? "✔" : "✘"), got, "[" + v.score + "]", (v.label || "—").padEnd(22), "|", text.slice(0, 52));
}
console.log("---\nResult:", pass + "/" + TESTS.length);
process.exit(pass === TESTS.length ? 0 : 1);
