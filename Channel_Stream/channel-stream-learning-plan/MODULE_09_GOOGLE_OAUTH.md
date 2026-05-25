# Module 9 — Google Sign-In: How OAuth Actually Works

## What we built and why it was broken

Channel Stream lets users sign in with their Google account so their league/team selections are saved across devices. When you click "Sign up / Sign in", the site is supposed to send you to Google's login page, then bring you back with a token that proves who you are.

It wasn't working on the live site because the three pieces of config the auth system needs — the Cognito domain, the client ID, and the redirect URL — were never included in the production build. The frontend code had `COGNITO_DOMAIN ?? ""`, so it was silently building URLs that pointed nowhere.

This module explains every piece of how OAuth works so you could rebuild this from scratch.

---

## The big picture: why we don't handle passwords ourselves

Storing passwords is dangerous. If your database leaks, every user's password leaks. Instead, we delegate authentication to a trusted provider (Google) via a standard called **OAuth 2.0**. Google verifies the password; we only receive a signed token saying "this person is who they say they are."

The flow looks like this:

```
User clicks "Sign in"
       ↓
Your site → redirects to → Google's login page
                                  ↓
                         User logs in to Google
                                  ↓
Google → redirects back to → Your callback page (with a code)
                                  ↓
                    Your site exchanges code → tokens
                                  ↓
                         User is now signed in
```

---

## The pieces involved

### 1. AWS Cognito (the middleman)
Cognito is an "identity provider proxy" — it sits between your app and Google. Instead of your app talking directly to Google's OAuth server, it talks to Cognito. Cognito handles the Google integration, returns tokens in a standard format, and adds user management on top.

Think of it like: **your app → Cognito → Google**

In our case, the Cognito domain is:
```
https://channel-stream-jl.auth.us-east-1.amazoncognito.com
```

### 2. The App Client (who's allowed to ask for tokens)
Inside Cognito, an "app client" represents your frontend application. It has:
- A **client ID** — a public identifier for your app (`1bsck4p8ma568p0pj8rk4gkug9`)
- A list of **allowed redirect URIs** — where Cognito is allowed to send users after login

If your redirect URI doesn't exactly match what's registered in Cognito, the login fails. This is a security measure — it prevents a malicious site from hijacking the auth flow.

### 3. The authorization code + PKCE
OAuth returns an **authorization code** (a one-time-use string) to your callback page. Your app then exchanges this code for actual tokens. 

**PKCE** (Proof Key for Code Exchange) adds security on top: before starting the flow, your app generates a random secret called a `code_verifier`. It hashes it into a `code_challenge` and sends the hash to Cognito. When exchanging the code for tokens, your app sends the original `code_verifier`. Cognito verifies the hash matches — proving the same browser session that started the login is completing it. This prevents someone from intercepting the code and using it themselves.

```
Start login:
  1. Generate random code_verifier (stored in sessionStorage)
  2. Hash it → code_challenge
  3. Redirect to Cognito with code_challenge

After Google login, Cognito redirects to your callback with ?code=abc123:
  4. Read code_verifier from sessionStorage
  5. POST to Cognito /oauth2/token with: code + code_verifier
  6. Cognito verifies hash(code_verifier) == code_challenge → issues tokens
```

### 4. The tokens
After a successful exchange, you get three JWTs (JSON Web Tokens):
- **access_token** — proves who you are to the backend API (used in `Authorization: Bearer` headers)
- **id_token** — contains user info (email, name, sub/user-id)
- **refresh_token** — used to get new access tokens when they expire (15 min default)

A JWT is three base64-encoded JSON objects joined by dots: `header.payload.signature`. The payload contains claims like `{ sub: "abc123", email: "you@gmail.com", exp: 1234567890 }`. You can read the payload without a secret key — but only the signature (which only Cognito knows how to produce) proves it's genuine.

---

## The code, explained line by line

### `lib/auth.ts` — starting the login

```typescript
export async function startLogin(): Promise<void> {
  // 1. Generate the PKCE verifier and challenge
  const verifier  = randomString(64)                          // random secret
  const challenge = base64UrlEncode(await sha256(verifier))   // hash of secret

  // 2. Random state to prevent CSRF attacks
  const state = randomString(16)

  // 3. Save verifier + state in the browser tab (sessionStorage)
  sessionStorage.setItem("pkce_verifier", verifier)
  sessionStorage.setItem("pkce_state",    state)

  // 4. Build the URL and send the user there
  const params = new URLSearchParams({
    response_type:         "code",        // we want an auth code, not a token directly
    client_id:             CLIENT_ID,     // which app is asking
    redirect_uri:          REDIRECT_URI,  // where to send the user after login
    scope:                 "openid email profile",  // what info we want
    state,                                // CSRF protection
    code_challenge:        challenge,     // PKCE
    code_challenge_method: "S256",        // SHA-256 hashing
    identity_provider:     "Google",      // skip Cognito's own login page, go straight to Google
  })

  window.location.href = `${COGNITO_DOMAIN}/oauth2/authorize?${params}`
}
```

### `app/auth/callback/page.tsx` — receiving the code

After Google login, the browser is redirected to `https://jonathanlohr.com/channel-stream/auth/callback?code=ABC&state=XYZ`. This page:

```typescript
// 1. Read the code and state from the URL
const code  = params.get("code")
const state = params.get("state")

// 2. Exchange the code for tokens
exchangeCode(code, state)
  .then((tokens) => {
    storeTokens(tokens)             // save to sessionStorage
    window.location.href = "/"      // full reload so AuthProvider re-reads sessionStorage
  })
```

`window.location.href = "/"` is important — a React client-side navigation (`router.push`) wouldn't re-run the code in `AuthProvider` that checks sessionStorage. A full page reload does.

### `components/AuthContext.tsx` — reading the stored token

On every page load, `AuthProvider` checks sessionStorage:
```typescript
function initUser(): User | null {
  const token = getStoredToken()    // reads "cs_access_token" from sessionStorage
  if (!token) return null
  const payload = parseJwtPayload(token)   // decode without verifying signature
  return { sub: payload.sub, email: payload.email, name: payload.name }
}
```

### `lib/api.ts` — using the token with the backend

When saving preferences, the access token goes in the `Authorization` header:
```typescript
async function authedPut(path, token, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method:  "PUT",
    headers: {
      "Content-Type":  "application/json",
      "Authorization": `Bearer ${token}`,  // ← this is how the backend knows who you are
    },
    body: JSON.stringify(body),
  })
}
```

### `internal/auth/auth.go` — the backend verifying the token

When the Go backend receives a request with an `Authorization: Bearer <token>` header, it doesn't just trust the token. It verifies the **signature** by fetching Cognito's public keys (JWKS) and checking that the token was signed by Cognito:

```go
// Fetch public keys from Cognito
jwksURL := fmt.Sprintf("%s/.well-known/jwks.json", cognitoDomain)
// Verify the token signature against those keys
// If valid → extract the sub (user ID) and proceed
```

This is why a fake token would be rejected in production — the signature can only be created by Cognito's private key.

---

## Why the Cognito env vars must be set at build time

Next.js has two kinds of environment variables:
- **Server-side** (`NEXT_SECRET_KEY`) — only available during build/SSR, never sent to the browser
- **Client-side** (`NEXT_PUBLIC_API_URL`) — baked into the JavaScript bundle at build time

Channel Stream is a **static export** (no server). Every page is pre-built HTML+JS uploaded to S3. When the user's browser downloads the JS, it's already compiled — it can't read environment variables from a server.

So `NEXT_PUBLIC_COGNITO_DOMAIN` must be baked in at build time:
```
npm run build
```
becomes (behind the scenes):
```
NEXT_PUBLIC_COGNITO_DOMAIN="https://channel-stream-jl.auth.us-east-1.amazoncognito.com" next build
```

The build replaces `process.env.NEXT_PUBLIC_COGNITO_DOMAIN` with the literal string everywhere in the bundle. If the variable isn't set, it's replaced with `undefined` → falls back to `""` → the login URL is broken.

This was the bug. The CI workflow was missing those three lines.

---

## How to set this up from scratch

If you were starting a new project and wanted Google sign-in:

**1. Create a Cognito User Pool**
- AWS Console → Cognito → Create user pool
- Choose "Email" as sign-in option
- Under "Federated identity providers" → Add Google
- You'll need a Google OAuth client ID + secret (created in Google Cloud Console)

**2. Create the App Client**
- Inside your User Pool → App clients → Create app client
- Enable "Authorization code grant" flow
- Add your callback URLs: `http://localhost:3000/auth/callback` AND your production URL
- Add logout URLs

**3. Note your values**
- User pool ID (for backend JWT verification)
- App client ID (goes in `NEXT_PUBLIC_COGNITO_CLIENT_ID`)
- Cognito domain (goes in `NEXT_PUBLIC_COGNITO_DOMAIN`)

**4. Add env vars to your build**
- Locally: create `.env.local` with the `NEXT_PUBLIC_` vars
- In CI: add them to the workflow's `env:` block under the build step
- They are NOT secrets — they're public values baked into client JS

**5. Wire up the callback route**
- Create `app/auth/callback/page.tsx`
- It reads `?code=` from the URL, calls your token exchange function, stores tokens, redirects home

---

## What sessionStorage means (vs localStorage vs cookies)

| Storage | Survives tab close? | Survives browser close? | Accessible by JS? |
|---------|--------------------|-----------------------|-------------------|
| `sessionStorage` | No | No | Yes |
| `localStorage` | Yes | Yes | Yes |
| `httpOnly cookie` | Yes (until expiry) | Yes (until expiry) | No |

We use `sessionStorage` so tokens automatically disappear when the user closes the tab. This is a reasonable security tradeoff for a learning project. A production app would typically use `httpOnly` cookies (which JavaScript can't read, so XSS attacks can't steal the token) or rotate short-lived access tokens via a server-side proxy.

---

## Summary: what we fixed and what you'd do if you broke it again

| What was wrong | Why | Fix |
|----------------|-----|-----|
| Sign-in button did nothing | `COGNITO_DOMAIN` was `""` in production build | Add `NEXT_PUBLIC_COGNITO_DOMAIN` to CI env vars |
| Redirect failed with Cognito error | Redirect URI not in allowed list | Add exact URL to Cognito app client's Callback URLs |
| Token exchange failed | `REDIRECT_URI` in code didn't match what Cognito registered | Both must be identical — even a trailing slash matters |
| Backend rejected token | Wrong User Pool or region in backend env | Backend needs the same Cognito issuer URL |
