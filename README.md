# LinkedIn AI News Automation

Roz subah apne aap:

1. **Market research** — Google News (tumhare topics) + TechCrunch / VentureBeat / The Verge
   se pichle 36 ghante ki news nikalta hai.
2. **Research brief** — AI saari news padhkar sabse important story chunta hai aur sirf
   usi ke facts nikalta hai (kuch bhi invent nahi karta).
3. **Insaan jaisa post** — har din alag style (story / contrarian / breakdown / practical /
   question). "AI wale" words (delve, game-changer, em-dash —, etc.) automatic pakad kar
   dobara likhwata hai.
4. **LinkedIn par publish** — clickable hashtags ke saath.
5. **Dashboard** — har post ka poora text, source link aur error GitHub Pages par.

100% free infrastructure (GitHub Actions + RSS + LinkedIn ka free API). Sirf OpenAI ka
kharcha (gpt-4o ke saath roughly $0.02 per post).

---

## Pehle kya galat ho raha tha (diagnosis)

`docs/history.json` ke hisaab se system ne **ek bhi post publish nahi kiya** tha. Code ka
news + AI wala hissa chal raha tha, lekin LinkedIn har baar reject kar raha tha:

| Kab | LinkedIn ka error | Matlab |
|---|---|---|
| Sep – Oct 2026 | `DISABLED_APPLICATION` — "Application is disabled" | Tumhari LinkedIn Developer App disable ho gayi thi |
| ~21 Oct se ab tak | `EXPIRED_ACCESS_TOKEN` | Token ke 60 din poore ho gaye |

Ye dono LinkedIn ki taraf ki settings hain — inhe code se theek nahi kiya ja sakta, tumhe
neeche wale steps karne honge (15 minute). Saath mein code mein ye sudhaar kiye gaye:

- Post se **pehle** token check hota hai aur saaf Roman-Urdu message deta hai ki kya karna hai.
- Token kharab ho tab bhi post **draft** ban kar dashboard par aata hai — "Copy post" dabao
  aur khud LinkedIn par daal do. Din khaali nahi jayega.
- Pehle `continue-on-error` ki wajah se fail hone par bhi run green dikhta tha → ab laal
  hoga aur GitHub tumhe **email** karega.
- LinkedIn ke special characters `( ) [ ] @ #` ab escape hote hain (pehle inse post kat
  jata ya fail ho jata).
- `LinkedIn-Version` header ab apne aap update hota hai (pehle 1 saal baad toot jata).
- Same din dobara run ho to double post nahi hoga; jo story pehle post ho chuki, dobara nahi aayegi.
- `feedparser` dependency hata di (Python ke built-in parser se kaam hota hai).

---

## ✅ Ab tumhe kya karna hai (sirf 4 steps)

### Step 1 — LinkedIn App check karo / nayi banao
1. **https://www.linkedin.com/developers/apps** kholo.
2. Apni purani app kholo. Agar wahan "disabled / restricted" dikhe aur koi restore option
   na ho, to **nayi app bana lo** (neeche Part C1–C2). Nayi app sabse aasan rasta hai.
   - Aam wajahein: app se linked LinkedIn Page **verify nahi** hua tha (Settings tab →
     "Verify" → link Page admin ko bhejo aur approve karo), ya app LinkedIn ki policy check
     mein flag ho gayi.
3. **Products** tab mein ye dono "Added" hone chahiye:
   - **Share on LinkedIn**
   - **Sign In with LinkedIn using OpenID Connect**

### Step 2 — Naya token banao
Do tarike, jo aasan lage:

**(a) Developer portal se (bina code):** app → `Auth` tab → neeche "OAuth 2.0 tools" →
`Create token` → scopes **`openid`, `profile`, `w_member_social`** teeno select karo →
`Request access token` → `Allow` → lamba token copy karo.

**(b) Helper script se (apne computer par):**
1. App → `Auth` tab → "Authorized redirect URLs" mein add karo: `http://localhost:8765/callback`
2. Terminal mein:
   ```bash
   pip install requests
   python scripts/get_linkedin_token.py
   ```
3. Client ID / Secret paste karo (Auth tab mein milte hain), browser mein `Allow` dabao.
   Token, Person URN aur expiry date print ho jayegi.

### Step 3 — GitHub Secrets update karo
Repo → `Settings` → `Secrets and variables` → `Actions`:

| Type | Name | Value |
|---|---|---|
| Secret | `LINKEDIN_ACCESS_TOKEN` | Step 2 wala naya token (update karo) |
| Secret | `OPENAI_API_KEY` | Tumhari OpenAI key (pehle se hai, chhedna nahi) |
| Secret | `LINKEDIN_PERSON_URN` | *Optional ab* — agar token mein `openid profile` hai to system khud nikaal leta hai |
| **Variable** (Variables tab) | `LINKEDIN_TOKEN_CREATED` | Aaj ki date, jaise `2026-11-08` — 50 din baad warning milegi |

> ⚠️ Keys **kabhi** code ya kisi file mein mat likhna — sirf Secrets mein.

### Step 4 — Test karo
1. Repo → `Actions` → "Daily LinkedIn AI Post" → `Run workflow`.
2. Pehli baar **`dry_run` ✅ tick karke** chalao → post banega, dashboard par dikhega,
   LinkedIn par nahi jayega. Post pasand aaye to…
3. Dobara `Run workflow` bina tick ke → LinkedIn par post ho jayega. 🎉

Iske baad roz **9:00 AM IST** apne aap chalega.

---

## Apne hisaab se settings badalna (`config.json`)

Code chhune ki zaroorat nahi, sirf `config.json` edit karo (GitHub par file kholo → ✏️):

| Setting | Kya karta hai |
|---|---|
| `author_persona` | **Zaroor badlo.** 1-2 line mein tum kaun ho / kya kaam karte ho. Isse post tumhari awaaz mein lagta hai. Jaise: `"I'm a data analyst in Karachi working with fintech startups."` |
| `topics` | Kin cheezon ki research ho. Har topic ek Google News search hai. Jaise `{"name": "Pakistan tech", "query": "Pakistan startup OR fintech"}` |
| `extra_rss_feeds` | Aur RSS feeds (optional) |
| `post_language` | `English` (default). Chaho to `"Roman Urdu"` bhi likh sakte ho |
| `min_words` / `max_words` | Post ki lambai |
| `max_hashtags` | Kitne hashtags (3 natural lagta hai) |
| `include_source_link` | `true` = post mein news ka link. (LinkedIn link wale posts ki reach kam karta hai, isliye default `false`) |
| `openai_model` | Default `gpt-4o`. GitHub Variable `OPENAI_MODEL` se bhi badal sakte ho |

**Posting time badalna:** `.github/workflows/daily-post.yml` mein `- cron: '30 3 * * *'`
(UTC time hai; IST = UTC + 5:30). Shaam 7 baje IST ke liye: `'30 13 * * *'`.

**Manual run options** (Actions → Run workflow):
- `dry_run` — sirf test, LinkedIn par nahi jayega
- `force` — aaj post ho chuka ho tab bhi ek aur
- `post_format` — style fix karo (story / contrarian / breakdown / practical / question)

---

## Har 60 din: Token renew karna

LinkedIn ka self-serve token 60 din chalta hai (ye LinkedIn ki limit hai, refresh token
sirf unke approved partners ko milta hai). Jab expire hoga:
- Actions run laal hoga + GitHub email aayega
- Dashboard par laal box mein likha hoga "token EXPIRE ho gaya hai"
- Us din ka post draft dashboard par ready hoga — copy karke manually daal sakte ho

Fix: **Step 2** dobara karo → **Step 3** mein `LINKEDIN_ACCESS_TOKEN` aur
`LINKEDIN_TOKEN_CREATED` update karo. 5 minute ka kaam.

---

## Problem aaye to

| Dashboard / Actions mein error | Kya karo |
|---|---|
| `token EXPIRE ho gaya` | Step 2 + 3 (naya token) |
| `App DISABLED hai` | Step 1 (app check / nayi app), phir Step 2 + 3 |
| `token REVOKED` | LinkedIn password badla ya app access hataya — Step 2 + 3 |
| `scope 'openid profile' missing` | Token banate waqt `openid` + `profile` bhi select karo, ya `LINKEDIN_PERSON_URN` secret add karo |
| `OPENAI_API_KEY set nahi hai` / `insufficient_quota` | OpenAI key check karo / platform.openai.com par billing mein balance daalo |
| `Koi nayi news nahi mili` | `config.json` ke topics bahut narrow hain, ya feeds down hain — kal dobara try hoga |

Local test (apne computer par):
```bash
pip install -r requirements.txt
python scripts/fetch_news.py          # sirf news dekho (koi key nahi chahiye)
export OPENAI_API_KEY="sk-..."
python scripts/generate_post.py       # post banao, LinkedIn par NAHI jayega
export LINKEDIN_ACCESS_TOKEN="..."
python scripts/post_to_linkedin.py    # sirf token check
```

---

## Files

```
config.json                     <- tumhari settings (topics, persona, length...)
scripts/run_all.py              <- poora flow (GitHub Actions ise chalata hai)
scripts/fetch_news.py           <- market research (RSS)
scripts/generate_post.py        <- research brief + human-style post + AI-word filter
scripts/post_to_linkedin.py     <- token check + LinkedIn publish
scripts/get_linkedin_token.py   <- (optional) naya token nikaalne ka helper
docs/index.html                 <- dashboard (GitHub Pages)
docs/history.json               <- har run ka record
.github/workflows/daily-post.yml
```

---

## Pehli baar setup (agar bilkul naye se kar rahe ho)

### Part C1 — LinkedIn Developer App banao
1. **developer.linkedin.com** → apne LinkedIn account se login → `Create app`.
2. App name: kuch bhi. LinkedIn Page: koi page chahiye (na ho to wahin "Create a LinkedIn
   Page" se chhota sa bana lo). Logo: koi bhi image.
3. `Create app` → phir **Settings** tab mein Page **Verify** karo (page admin ke taur par
   link kholo aur approve karo). Ye skip karne se app disable ho sakti hai.

### Part C2 — Products add karo
App → `Products` tab → **Share on LinkedIn** aur **Sign In with LinkedIn using OpenID
Connect** dono ka `Request access`. Usually turant approve hota hai.

Phir upar wala **Step 2 → 3 → 4** karo.

### Part D — Dashboard (GitHub Pages)
Repo `Settings` → `Pages` → Source: `Deploy from a branch` → Branch: `main`, folder `/docs`
→ `Save`. Kuch minute mein URL milega: `https://<username>.github.io/<repo-name>/`
