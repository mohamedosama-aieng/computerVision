# تسليم مشروع Hikvision Computer Vision

هذا الملف هو وثيقة التسليم للسيرفر أو لأي ChatGPT سيكمل المشروع. يجب قراءته بالكامل قبل تعديل الكود.

## 1. الهدف النهائي

نريد بناء حل Computer Vision يعمل من البيت على جهاز منفصل عن شبكة المحل، ويصل إلى كاميرات Hikvision الموجودة داخل المحل، ثم يعالج البث الحي ويعرض النتائج أو يطلق تنبيهات.

المطلوب النهائي:

```text
DVR داخل المحل
    -> اتصال Hikvision آمن عبر السحابة أو Agent داخل المحل
    -> جهاز Computer Vision في البيت
    -> OpenCV / YOLO / نموذج الرؤية الحاسوبية
    -> واجهة سطح مكتب وتنبيهات و/أو تسجيل نتائج
```

المستخدم لا يريد حلاً يقتصر على نفس شبكة المحل. المطلوب الوصول من البيت.

## 2. القرار الأمني الإجباري

لا تضع أي كلمة مرور أو Verification Code أو App Secret داخل الكود أو Git أو هذا الملف.

لا تستخدم Reverse Engineering لبروتوكول Hik-Connect.

لا تفتح منافذ DVR على الإنترنت بواسطة Port Forwarding أو DMZ.

لا تفترض أن Serial Number وVerification Code يكفيان للحصول على رابط RTSP سحابي.

أي تكامل سحابي مباشر يجب أن يعتمد على SDK أو API رسمي موثق ومصرح به من Hikvision.

## 3. مواصفات جهاز DVR المؤكدة

المعلومات مأخوذة من صور إعدادات الجهاز التي أرسلها المستخدم:

| العنصر | القيمة |
|---|---|
| Device Name | Embedded Net DVR |
| Device Model | DS-7116HGHI-K1 |
| Firmware | V4.30.122, Build 201107 |
| Hardware Version | 0xe7600 |
| Total Channels | 16 |
| القنوات المستخدمة الظاهرة | A1 إلى A9 |
| نوع الكاميرات | Analog / HD-CVBS |
| IPv4 Address | 192.168.1.100 |
| Subnet Mask | 255.255.255.0 |
| Default Gateway | 192.168.1.1 |
| DHCP | Disabled، والعنوان ثابت |
| HTTP Port | 80 |
| RTSP Port | 1554 |
| Server/SDK Port | 8000 |
| HTTPS Port الظاهر في NAT | 443 |
| Hik Cloud P2P Port الظاهر | 9010 |
| Cloud P2P Data Port الظاهر | 9020 |
| NAT | Disabled |
| Hik-Connect Access Type | Hik-Connect |
| Hik-Connect Enable | Enabled |
| Stream Encryption | Enabled |
| Hik-Connect Status | Online |
| Hik-Connect Account Status | Bound |
| Hik-Connect Server Address | hkddev.eu.hik-connect.com، كما ظهر في الصورة |

الرقم التسلسلي الكامل ظهر في صورة المحادثة لكنه غير مكرر هنا عمداً. لا تحتاجه لتنفيذ الحل الآمن الحالي. يجب عدم إعادة نشره أو نشر QR/Verification Code.

## 4. بيانات الاعتماد

يوجد حالياً حساب إداري على DVR، وقد ظهر في المحادثة. اعتبر كلمة مروره مكشوفة ويجب تغييرها فوراً.

الإجراء المطلوب:

1. تغيير كلمة مرور حساب `admin`.
2. إنشاء حساب منفصل مثل `vision_viewer`.
3. منح الحساب الجديد أقل صلاحيات ممكنة: live view فقط إن كان firmware يسمح بذلك.
4. عدم استخدام `admin` في التطبيق النهائي.
5. تخزين كلمة المرور محلياً في Keychain/Credential Manager أو Secret Manager، وليس في JSON أو `.env` مرفوع إلى Git.

## 5. حقيقة Hik-Connect المهمة

تفعيل Platform Access وظهور الحالة `Online` و`Bound` يعني أن DVR متصل بخدمة Hik-Connect الرسمية وأنه يمكن استخدامه من تطبيق Hik-Connect.

هذا لا يثبت وجود API عام يسمح لتطبيق Python مستقل بعمل الآتي:

```text
Serial Number + Verification Code -> RTSP URL سحابي عام
```

هذا المسار غير موثق كواجهة عامة في المعلومات المتاحة. `ISAPI` هو واجهة الجهاز المحلية، وليس واجهة سحابة Hik-Connect. `RTSP` الظاهر في إعدادات DVR هو منفذ الجهاز المحلي، وليس بالضرورة منفذاً يمكن الوصول إليه عبر Hik-Connect من الإنترنت.

## 6. ما تم التحقق منه من Hikvision

تمت مراجعة بوابة Hikvision المفتوحة وكتالوج SDK الرسمي.

الكتالوج يعرض `Device Network SDK` للحزم التالية:

- Windows 64-bit
- Windows 32-bit
- Linux 32-bit
- Linux 64-bit

وتوجد أمثلة بلغات:

- C++
- C#
- Java

وصف الحزمة هو remote access/control لأجهزة Hikvision. لم يظهر في الكتالوج الذي تمت مراجعته SDK معلن باسم Hik-Connect Cloud P2P SDK يتيح الحصول على live stream لجهاز Bound باستخدام Serial وVerification Code فقط.

لم يتم العثور على حزمة Device Network SDK رسمية لـ macOS في الكتالوج.

## 7. حالة المشروع الحالية

المشروع موجود داخل:

```text
HikVision/
```

الملفات الرئيسية:

```text
HikVision/
  pyproject.toml
  .gitignore
  hikvision_app/
    __init__.py
    main.py
    models.py
    settings.py
    security.py
    isapi.py
    stream.py
    vision.py
    ui.py
  tests/
    test_isapi.py
```

التطبيق الحالي MVP محلي، وليس بعدُ Hik-Connect Cloud client.

المزايا الموجودة:

- واجهة Desktop بـ PySide6.
- اكتشاف القنوات عبر ISAPI.
- اتصال HTTP/HTTPS بـ ISAPI باستخدام HTTP Digest Authentication.
- إنشاء روابط RTSP للقنوات.
- عرض عدة كاميرات في Grid.
- إعادة اتصال تلقائية للبث.
- OpenCV motion detection hook.
- حفظ إعدادات غير سرية في ملف إعدادات محدود الصلاحيات.
- تخزين كلمة المرور في `keyring`.
- دعم البث الفرعي.

الإعدادات الافتراضية الحالية مطابقة لجهاز المحل:

```text
Host: 192.168.1.100
ISAPI Port: 80
RTSP Port: 1554
HTTPS: Disabled
Substream: Enabled
```

هذه الإعدادات تعمل فقط من داخل شبكة المحل أو من شبكة VPN/Tailscale تصل إلى شبكة المحل.

## 8. الاختبارات الحالية

تم تشغيل:

```bash
.venv/bin/python -m pytest -q
```

والنتيجة الأخيرة:

```text
5 passed
```

تم أيضاً اختبار إنشاء نافذة PySide6 في وضع offscreen بنجاح.

لم يتم اختبار البث الحقيقي لأن جهاز التطوير الحالي كان خارج شبكة `192.168.1.0/24`.

لا تنقل مجلد `.venv` إلى السيرفر. حجمه كبير ومخصص لبيئة macOS الحالية. أنشئ بيئة جديدة على النظام المستهدف.

## 9. المسارات الممكنة للوصول من البيت

### المسار A: Hik-Connect Cloud SDK رسمي

هذا هو المسار المطلوب إذا كان الشرط هو عدم وجود أي جهاز Agent داخل المحل.

لا يمكن البدء في تنفيذه فعلياً قبل الحصول من Hikvision على:

```text
Cloud/OpenSDK name
Official SDK binaries or REST/WebSocket API
API documentation
App Key
App Secret
Tenant/project ID إن وجد
Region/endpoint
Supported operating systems
Permission to consume live video for Computer Vision
```

يجب سؤال موزع Hikvision أو الدعم بهذه الصيغة:

```text
We need an official third-party integration for live video from a Hik-Connect-bound
DS-7116HGHI-K1 (firmware V4.30.122, Build 201107) to a remote computer-vision
application. Does this model/firmware support an official Hik-Connect Cloud P2P
OpenSDK or OpenAPI for live stream access? Please provide the supported Windows 64-bit
or macOS integration package, authentication flow, SDK license, and live-stream API.
```

إذا أعطى Hikvision SDK Windows فقط، فالأفضل تشغيل جزء الاتصال على Windows ثم تمرير frames أو stream مشفر إلى خادم الرؤية.

### المسار B: Windows Agent داخل المحل + Tailscale

هذا هو المسار العملي الموصى به إذا لم يوجد Cloud SDK رسمي.

البنية:

```text
DVR 192.168.1.100:1554
  -> Windows Agent داخل المحل
  -> Tailscale encrypted network
  -> Computer Vision server في البيت
```

الخطوات:

1. توفير جهاز Windows 64-bit يعمل دائماً داخل المحل وعلى نفس شبكة DVR.
2. تثبيت Tailscale على جهاز المحل وعلى جهاز البيت.
3. تفعيل حساب Tailscale واحد أو tailnet مخصص.
4. عدم تفعيل Port Forwarding.
5. اختبار أن جهاز البيت يرى جهاز المحل عبر عنوان Tailscale.
6. تشغيل Agent على جهاز المحل يسحب RTSP محلياً من `192.168.1.100:1554`.
7. إرسال stream أو frames إلى جهاز البيت عبر Tailscale.
8. تشغيل OpenCV/YOLO على جهاز البيت.
9. استخدام حساب DVR محدود الصلاحيات.

يمكن استخدام RTSP/FFmpeg/OpenCV في الـ Agent بدون Hik-Connect Cloud SDK، لأن الـ Agent داخل نفس الشبكة المحلية.

### المسار C: WireGuard/VPN إلى الشبكة

بديل لـ Tailscale، لكنه يحتاج إعداد VPN وFirewall وإدارة مفاتيح يدوية. لا تستخدمه مع فتح منافذ DVR مباشرة؛ افتح منفذ VPN فقط على جهاز VPN مخصص، لا على DVR.

### المسار D: Port Forwarding مباشر

غير موصى به. لا تفتح منافذ `80`, `1554`, `8000`, `443`, `9010`, أو `9020` للعامة. هذا يعرض DVR لمحاولات تسجيل الدخول والاستغلال.

## 10. ما يجب على ChatGPT في السيرفر فعله

لا يدعي تنفيذ Hik-Connect Cloud قبل وجود SDK/API رسمي.

ينفذ بالترتيب:

1. يحدد نظام تشغيل السيرفر ومعمارية CPU.
2. يفحص المشروع ويستبعد `.venv` وملفات الأسرار.
3. يختبر التطبيق الحالي محلياً.
4. يختار المسار A إذا توفرت وثائق Cloud SDK رسمية.
5. إذا لم تتوفر، ينفذ المسار B: Agent Windows داخل المحل + Tailscale.
6. يفصل `transport` عن `computer vision` عبر interface واضحة.
7. يضيف health checks وreconnect وbackoff وmetrics.
8. يضيف دعم stream منخفض الجودة للتحليل وstream اختياري للعرض.
9. يضيف حفظ الأسرار في Windows Credential Manager أو macOS Keychain أو secret manager.
10. يمنع تسجيل كلمات المرور والـ RTSP URLs التي تحتوي credentials في logs.
11. يضيف اختبارات unit وintegration mock بدون الحاجة لبيانات DVR الحقيقية.
12. يوثق تشغيل الخدمة تلقائياً وطرق إيقافها وحذف الأسرار.

## 11. تعليمات تشغيل المشروع الحالي

على macOS أو Linux مع Python 3.11 أو أحدث:

```bash
cd HikVision
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest -q
.venv/bin/hikvision-viewer
```

على Windows PowerShell:

```powershell
cd HikVision
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\hikvision-viewer.exe
```

إذا تم تشغيل التطبيق داخل شبكة المحل، استخدم:

```text
Host: 192.168.1.100
ISAPI Port: 80
RTSP Port: 1554
```

## 12. المطلوب من المستخدم قبل الاختبار النهائي

لا تطلب من المستخدم إرسال أسرار في ChatGPT.

المطلوب محلياً على الجهاز فقط:

- تغيير كلمة مرور `admin` التي ظهرت في المحادثة.
- إنشاء حساب مشاهدة منفصل.
- التأكد من أن Platform Access ما زال `Online` و`Bound`.
- معرفة هل يوجد Windows/Linux يعمل دائماً داخل المحل.
- تحديد نظام تشغيل جهاز Computer Vision في البيت.
- الحصول على موافقة/بيانات Hikvision Cloud SDK إذا كان المطلوب اتصال سحابي مباشر بدون Agent.

## 13. تعريف النجاح

يعتبر المشروع مكتملاً فقط عندما:

1. يرى جهاز البيت DVR من خلال المسار الرسمي المختار.
2. تظهر القنوات A1-A9 أو القنوات المتاحة فعلياً.
3. يعمل live stream مستقر لمدة اختبار لا تقل عن 30 دقيقة.
4. يعمل reconnect بعد قطع الشبكة وإعادتها.
5. تصل frames إلى pipeline Computer Vision.
6. لا توجد كلمات مرور أو رموز تحقق في الملفات أو logs.
7. لا توجد منافذ DVR مكشوفة للعامة.
8. تعمل الخدمة تلقائياً بعد إعادة تشغيل الجهاز الوسيط.
9. توجد طريقة واضحة لتغيير credentials وإبطال الوصول.

## 14. الخلاصة التنفيذية

الجهاز DS-7116HGHI-K1 متصل فعلاً بـ Hik-Connect وحالته Online/Bound، لكن هذا وحده لا يمنح تطبيق Python مستقلاً API سحابياً موثقاً. على Windows يمكن استخدام Hikvision Device Network SDK الرسمي، لكنه لا يثبت دعم Hik-Connect P2P Cloud. لذلك:

- إن حصلنا على Cloud SDK/API رسمي: نبني Cloud adapter.
- إن لم نحصل عليه: نستخدم Windows Agent داخل المحل مع Tailscale، ثم نعالج البث على جهاز البيت.
- لا نستخدم reverse engineering ولا Port Forwarding مباشر.

هذا هو المسار الآمن والقابل للصيانة والاختبار.
