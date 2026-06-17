# UwU Apps 2FA Bot

Telegram bot (`@uwuapps_2fa_bot`) that provides **Login with Telegram** for all UwU Apps.  
Users link their Telegram account to their UwU Apps account once, then log in to any UwU App instantly - via a deep link or a one-time OTP code.

All data is stored in Supabase alongside the existing `uwu_users` table.

---

## How it works

### Flow A - Web app initiates (deep link)

```text
Web app                          Bot (this repo)             Supabase
   │                                    │                        │
   │── User clicks "Login with Telegram"│                        │
   │── Generate token + insert into ────────────────────────────►│
   │   uwutele_tokens                   │                        │
   │── Redirect to t.me/uwuapps_2fa_bot?start=<token>           │
   │                                    │                        │
   │                  User opens Telegram, bot receives /start   │
   │                                    │── Verify token ────────►
   │                                    │── Fetch uwu_users ─────►
   │                                    │── Upsert link ─────────►
   │                                    │── Mark token used ──────►
   │                                    │── Reply: ✅ Approved   │
   │                                    │                        │
   │◄── Poll uwutele_tokens: used=true ─────────────────────────►│
   │── User is now logged in            │                        │
```

### Flow B - User initiates from Telegram (OTP code)

```text
User (Telegram)                  Bot (this repo)           Web app
   │                                    │                      │
   │── /login ──────────────────────────►                      │
   │                                    │── Insert OTP ────────►(Supabase)
   │◄── "Your code: 123456" ────────────│                      │
   │                                    │                      │
   │── Opens web app, enters code ──────────────────────────────►
   │                                    │── Verify OTP ────────►(Supabase)
   │                                    │── Mark OTP used ──────►
   │◄── Logged in ──────────────────────────────────────────────│
```

Both flows use **5-minute, single-use** tokens/codes.

---

## Project structure

```text
telegram/
├── bot.js               # Entry point
├── config.js            # Env var loader
├── db.js                # All DB operations via Supabase
├── supabaseClient.js    # Supabase client + uwu_users queries
├── issueToken.js        # CLI utility: insert a deep-link token
├── handlers/
│   ├── start.js         # /start + deep-link token processing (Flow A)
│   ├── login.js         # /login OTP generation (Flow B)
│   ├── link.js          # /link conversation
│   ├── unlink.js        # /unlink with confirmation
│   ├── status.js        # /status
│   ├── help.js          # /help
│   └── callback.js      # Generic persisted button router
├── package.json
├── .env.example
├── .gitignore
└── README.md
```

---

## Supabase tables (`uwutele_` prefix)

| Table | Purpose |
| --- | --- |
| `uwutele_links` | Telegram ↔ UwU Apps account mappings |
| `uwutele_tokens` | Pending deep-link login tokens (Flow A) |
| `uwutele_otps` | Bot-generated OTP codes (Flow B) |
| `uwutele_sessions` | Audit log of completed logins |
| `uwutele_link_state` | In-progress `/link` conversation state |
| `uwutele_buttons` | Persisted inline keyboard buttons (survive restarts) |

All tables have RLS enabled. Only the service role key (used by the bot and your Vercel backends) can access them - no public/anon access.

---

## Setup

### 1. BotFather

1. Message `@BotFather` on Telegram
2. `/newbot` → Name: `UwU Apps 2FA Bot` → Username: `uwuapps_2fa_bot`
3. Copy the token → paste into `.env` as `BOT_TOKEN`
4. `/setprivacy` → your bot → **Disable**
5. `/setdescription` → `Log in to UwU Apps (uwuapps.org) using your Telegram account. Link once, log in everywhere.`
6. `/setcommands` → paste:

```text
start - Start or process a login request
login - Get a one-time login code to enter in a UwU App
link - Link your Telegram to your UwU Apps account
unlink - Unlink your Telegram from your UwU Apps account
status - Check your link status
help - Show help information
```

### 2. Supabase - run the migration

1. Open your Supabase project → **SQL Editor** → **New query**
2. Paste the contents of `migration.sql` and run it
3. Tables will appear under **Table Editor**

### 3. VPS setup

```bash
git clone https://github.com/YOUR_USERNAME/uwuapps-2fa.git
cd uwuapps-2fa/telegram

npm install

cp .env.example .env
nano .env   # Fill in BOT_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_KEY
```

### 4. Run in tmux

```bash
tmux new -s uwu2fa
npm start
# Ctrl+B then D to detach

# Reattach: tmux attach -t uwu2fa
```

---

## Web app integration

Your web app backends (Vercel) can use `@supabase/supabase-js` with the **service role key** to insert tokens and verify OTPs directly - no VPS proxy needed.

### Flow A - Deep link (web app initiates)

```javascript
import { createClient } from '@supabase/supabase-js'
import crypto from 'crypto'

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY)

// 1. Generate and store the token
const token = crypto.randomBytes(32).toString('base64url')
await supabase.from('uwutele_tokens').insert({
  token,
  uwu_user_id: session.userId,   // UUID from uwu_users
  app_id:      'mrt-app',
  app_label:   'UwU MRT Info',
  expires_at:  new Date(Date.now() + 5 * 60 * 1000).toISOString(),
})

// 2. Redirect user to the deep link
const deepLink = `https://t.me/uwuapps_2fa_bot?start=${token}`
redirect(deepLink)

// 3. Poll for confirmation
const { data } = await supabase
  .from('uwutele_tokens')
  .select('used, uwu_user_id')
  .eq('token', token)
  .single()

if (data?.used) {
  // User is authenticated as data.uwu_user_id
}
```

### Flow B - OTP code (user initiates from Telegram)

```javascript
// User types their 6-digit code into the login form
const otp = req.body.otp

const now = new Date().toISOString()
const { data } = await supabase
  .from('uwutele_otps')
  .select('*')
  .eq('otp', otp)
  .eq('used', false)
  .gt('expires_at', now)
  .single()

if (!data) return res.status(401).json({ error: 'Invalid or expired code' })

// Mark used and log the session
await supabase.from('uwutele_otps').update({
  used: true, used_at: now
}).eq('otp', otp)

await supabase.from('uwutele_sessions').insert({
  token: otp, telegram_id: data.telegram_id,
  uwu_user_id: data.uwu_user_id, app_id: 'mrt-app',
})

// data.uwu_user_id is the authenticated user's UUID
```

---

## Testing token issuance

```bash
node issueToken.js "<uwu_user_id_uuid>" "test-app" "My Test App"
# Outputs: Token and deep link
# Open the deep link in Telegram to test Flow A end-to-end
```

---

## Environment variables

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `BOT_TOKEN` | ✅ | - | From @BotFather |
| `SUPABASE_URL` | ✅ | - | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | ✅ | - | Supabase service role key |
| `TOKEN_EXPIRY_SECONDS` | ❌ | `300` | Token/OTP lifetime in seconds |

---

## Updating the bot

```bash
tmux attach -t uwu2fa
# Ctrl+C to stop
git pull
npm install   # only if package.json changed
npm start
# Ctrl+B then D to detach
```
