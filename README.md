# Flora Cleaner Bot 🧹

Telegram guruhida **"kirdi / chiqdi"** (kimdir qo'shildi / chiqdi) va boshqa
xizmat xabarlarini avtomatik o'chirib turadigan bot. Vercel'da serverless
ishlaydi — server doim yonib turishi shart emas.

## 1. Botni yaratish
1. Telegramda [@BotFather](https://t.me/BotFather) ga kiring.
2. `/newbot` buyrug'i bilan yangi bot yarating va **token**ni oling
   (masalan: `123456:ABC-DEF...`).

## 2. Botni guruhga admin qilish
1. Botni **ФЛОРА ХОЛДИНГ** guruhiga qo'shing.
2. Botni **administrator** qiling va **"Delete messages"** (xabarlarni
   o'chirish) ruxsatini yoqing. Aks holda xabarlarni o'chira olmaydi.

## 3. Vercel'ga yuklash
1. Ushbu papkani GitHub'ga yuklang yoki to'g'ridan-to'g'ri Vercel'ga import qiling.
2. Vercel'da loyiha sozlamalarida **Environment Variables** bo'limiga kiring va
   qo'shing:
   - Nomi: `BOT_TOKEN`
   - Qiymati: BotFather bergan token
3. **Deploy** tugmasini bosing. Sizga manzil beriladi, masalan:
   `https://flora-cleaner-bot.vercel.app`

## 4. Webhook'ni ulash
Brauzeringizda quyidagi havolani oching (TOKEN va URL ni o'zingiznikiga
almashtiring):

```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<SIZNING-URL>.vercel.app/api/bot
```

`{"ok":true,"result":true,"description":"Webhook was set"}` chiqsa — tayyor.

## Tekshirish
Guruhga birovni qo'shing yoki chiqaring — "... qo'shildi / chiqdi" degan
xizmat xabari darhol o'chib ketadi. ✅

## Eslatma
- Bot faqat **xizmat xabarlarini** (kirdi/chiqdi, nom/rasm o'zgardi, pin
  va h.k.) o'chiradi. Oddiy yozishmalarga tegmaydi.
- Telegram odatda 48 soatdan eski xabarlarni o'chirishga ruxsat bermaydi —
  bu yangi xabarlarga ta'sir qilmaydi.
