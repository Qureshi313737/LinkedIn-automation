# LinkedIn AI News Automation

Roz current AI news dhoondh kar, ek professional post likh kar, LinkedIn
par khud publish karne wala system. 100% free (GitHub Actions + RSS +
tumhari OpenAI key + LinkedIn ka apna free API).

Is file mein wahi 3 cheezein hain jo tumhe khud bharni hain, exact steps
ke saath. Baaki sab code already ready hai, kuch edit nahi karna.

---

## Kya-kya bharna hai (total 3 cheezein)

1. `OPENAI_API_KEY` — tumhari OpenAI key
2. `LINKEDIN_ACCESS_TOKEN` — LinkedIn se milega (neeche exact steps)
3. `LINKEDIN_PERSON_URN` — tumhara profile ID (neeche exact steps)

**Ye teeno kahin bhi code file mein NAHI likhni hain** — inhe GitHub ke
"Secrets" section mein daalna hai, jo encrypted rehta hai aur kabhi
public nahi dikhta.

---

## Part A — Repository GitHub par upload karna

1. github.com par login karo → `+` → `New repository`
2. Naam do: `linkedin-ai-automation` → **Private** rakho → `Create repository`
3. Ye poora folder (jo maine banaya hai) us repository mein upload karo:
   - Sabse aasan tarika: GitHub ke web page par `Add file` → `Upload files`
     → saari files/folders drag-drop kar do (folder structure automatically
     maintain rahega).
4. `Commit changes` dabao.

---

## Part B — Secrets add karna (Step 1: OpenAI key)

1. Apne repo mein jaake `Settings` tab kholo (upar).
2. Left side mein `Secrets and variables` → `Actions` par click karo.
3. `New repository secret` button dabao.
4. **Name**: `OPENAI_API_KEY`
   **Value**: apni OpenAI key paste karo (jo `sk-...` se shuru hoti hai,
   platform.openai.com/api-keys se milti hai)
5. `Add secret` dabao.

---

## Part C — LinkedIn se Access Token aur Person URN nikaalna

Ye sabse zyada steps wala part hai, lekin ek-time hi karna hai.

### C1 — LinkedIn Developer App banao
1. **developer.linkedin.com** par jaake apne normal LinkedIn account se
   login karo.
2. `Create app` dabao.
3. Fields bharo:
   - App name: kuch bhi (e.g. "My AI News Bot")
   - LinkedIn Page: agar tumhare paas company page nahi hai, ek chhota
     sa test page bana lo (LinkedIn app banane ke liye ek page link
     karna zaroori hai) — `Create a LinkedIn Page` option wahin milega.
   - Logo: koi bhi image upload kar do (chhoti si)
4. `Create app` dabao.

### C2 — "Share on LinkedIn" product add karo
1. Apne naye app ke andar `Products` tab kholo.
2. **"Share on LinkedIn"** dhoondo → `Request access` dabao.
3. Ye usually turant approve ho jata hai (kabhi 1-2 din).
4. Isi tab mein **"Sign In with LinkedIn using OpenID Connect"** bhi
   request kar lo — isse Person URN nikaalna aasan ho jayega (C4 mein).

### C3 — Access Token generate karo (LinkedIn ka apna built-in tool use karke)
LinkedIn khud ek tool deta hai jisse tumhe khud OAuth code likhne ki
zaroorat nahi:

1. Apne app ke andar `Auth` tab kholo.
2. Neeche scroll karo, **"OAuth 2.0 tools"** section dhoondo.
3. `Create token` button dabao.
4. Jo scopes (permissions) dikhengi, unme se ye do zaroor select karo:
   - `w_member_social` (post karne ke liye)
   - `openid`, `profile` (tumhari identity ke liye)
5. `Request access token` dabao — ek naya tab khulega jisme apna LinkedIn
   account se authorize karna hoga (`Allow` dabao).
6. Wapas aakar tumhe ek lamba token milega jaisa:
   `AQXn...` (bahut lamba string) — **isko copy kar lo**.

**Zaroori baat**: ye token 60 din mein expire hota hai. Har 60 din mein
yehi C3 step dobara karke naya token GitHub Secrets mein update karna
hoga (5 minute ka kaam).

### C4 — Person URN nikaalna
Ye tumhari profile ka unique ID hai, isse pata karne ke 2 tarike hain:

**Tarika 1 (aasan)** — apne computer/phone ke browser mein ye URL kholo
(token wahi jo C3 mein mila):
```
https://api.linkedin.com/v2/userinfo
```
Isse seedha nahi khulega kyunki isko "Authorization" header chahiye —
isliye ye command apne computer ke Terminal/Command Prompt mein chalao
(Python installed honi chahiye, ya koi bhi online "API tester" tool jaise
Postman use kar sakte ho):

```bash
curl -H "Authorization: Bearer YAHAN_APNA_TOKEN_PASTE_KARO" https://api.linkedin.com/v2/userinfo
```

Response mein ek field milega `"sub": "XXXXXXXXXX"` — yehi tumhara ID hai.

**Final Person URN banega**: `urn:li:person:XXXXXXXXXX`
(bas `urn:li:person:` ke aage wo ID laga do jo `sub` field mein mili)

### C5 — Dono values GitHub Secrets mein daalo
Part B jaisa hi process:
1. `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
2. **Name**: `LINKEDIN_ACCESS_TOKEN` → **Value**: wo lamba token (C3 se)
3. Phir se `New repository secret`:
   **Name**: `LINKEDIN_PERSON_URN` → **Value**: `urn:li:person:XXXXXXXXXX` (C4 se)

---

## Part D — GitHub Pages (dashboard) enable karna

1. Repo `Settings` → left side `Pages` par jao.
2. **Source**: `Deploy from a branch` select karo.
3. **Branch**: `main` select karo, folder: `/docs` select karo.
4. `Save` dabao.
5. Kuch minute mein ek URL milega jaisa:
   `https://tumhara-username.github.io/linkedin-ai-automation/`
   — yahan tumhara status dashboard dikhega.

---

## Part E — Test karo

1. Repo ke `Actions` tab mein jao.
2. Left side "Daily LinkedIn AI Post" workflow par click karo.
3. Right side `Run workflow` button dabao → `Run workflow` (confirm).
4. 30-60 second wait karo, refresh karo — dekho green tick (success) aata
   hai ya laal cross (failed).
5. Agar success hai, apna LinkedIn profile khol ke check karo post gaya
   ya nahi. Dashboard URL (Part D) khol ke bhi status dekh sakte ho.
6. Agar fail hua, `Actions` tab mein us run par click karke error message
   padh sakte ho — usually ya to koi Secret galat hai ya LinkedIn token
   expire ho gaya.

---

## Ab yeh hamesha ke liye chalega

Koi aur kadam nahi — workflow file (`daily-post.yml`) mein schedule set
hai (roz 9:00 AM IST). Ab yeh apne aap roz chalega, LinkedIn par post
karega, aur dashboard update karta rahega.

**Sirf yaad rakhne wali baat**: har ~60 din mein LinkedIn access token
expire hoga (C3 dobara karna hoga) — GitHub tumhe email se batayega agar
koi run fail hota hai.

### Apna posting time badalna ho to
`.github/workflows/daily-post.yml` file mein ye line dhoondo:
```
- cron: '30 3 * * *'
```
Ye UTC time hai. Format: `minute hour * * *`. IST = UTC + 5:30, isliye
IST 9:00 AM ke liye UTC 3:30 likha hai. Agar IST 7:00 PM (shaam) chahiye,
to UTC 1:30 PM hoga → `- cron: '30 13 * * *'`
