# Deployment Environment Guide

This guide explains where each environment variable is used and how to configure them for different deployment scenarios.

---

## Environment Variable Reference

### Frontend Variables (Vite)

| Variable | Required | Where Used | Description |
|----------|----------|------------|-------------|
| `VITE_API_BASE_URL` | Yes | Frontend API calls | Base URL for the Sponge API |
| `VITE_SUPABASE_URL` | No | Supabase client (if used) | Supabase project URL |
| `VITE_SUPABASE_ANON_KEY` | No | Supabase client (if used) | Public anon key |

**Note:** Variables prefixed with `VITE_` are exposed to the frontend bundle. Never put secrets here.

### Backend Variables (Edge Functions)

| Variable | Required | Where Used | Description |
|----------|----------|------------|-------------|
| `SUPABASE_URL` | Yes | Edge Function | Project URL for Supabase client |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Edge Function | Service role key (bypasses RLS) |
| `OPENAI_API_KEY` | Yes* | LLM extraction | OpenAI API key |
| `ANTHROPIC_API_KEY` | No | LLM extraction | Alternative provider |
| `LLM_PROVIDER` | No | LLM client | Provider selection (default: stub) |
| `LLM_MODEL` | No | LLM client | Model to use |

*Required for production. Can use `LLM_PROVIDER=stub` for testing without API key.

---

## Deployment Scenarios

### 1. Local Development (Supabase CLI)

```bash
# .env file
VITE_API_BASE_URL=http://localhost:54321/functions/v1/api
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=<local-anon-key>

# These are auto-provided by Supabase CLI for Edge Functions
# SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are injected automatically
```

Start local Supabase:
```bash
supabase start
supabase functions serve api
```

### 2. GitHub Pages + Supabase Cloud

**Frontend (GitHub Pages):**
- Build with `VITE_API_BASE_URL` pointing to Supabase Edge Function
- Deploy static files to GitHub Pages

```bash
# Build command
VITE_API_BASE_URL=https://xyz.supabase.co/functions/v1/api npm run build
```

**Backend (Supabase Edge Functions):**

Set secrets in Supabase:
```bash
supabase secrets set OPENAI_API_KEY=sk-...
supabase secrets set LLM_PROVIDER=openai
supabase secrets set LLM_MODEL=gpt-4o-mini
```

Deploy function:
```bash
supabase functions deploy api --no-verify-jwt
```

### 3. Vercel + Supabase Cloud

**Frontend (Vercel):**

Set environment variables in Vercel dashboard:
- `VITE_API_BASE_URL` = `https://xyz.supabase.co/functions/v1/api`

**Backend (Supabase):**
Same as GitHub Pages setup.

---

## Setting Supabase Secrets

### Via CLI

```bash
# Set a secret
supabase secrets set KEY_NAME=value

# Set multiple secrets
supabase secrets set \
  OPENAI_API_KEY=sk-... \
  LLM_PROVIDER=openai

# List secrets (names only, not values)
supabase secrets list
```

### Via Dashboard

1. Go to **Settings** → **Edge Functions**
2. Click **Manage secrets**
3. Add key-value pairs

---

## Required Secrets by Feature

### Minimum Viable (Stub Mode)

No secrets required. Uses stub LLM responses.

```bash
supabase secrets set LLM_PROVIDER=stub
```

### Production (OpenAI)

```bash
supabase secrets set OPENAI_API_KEY=sk-...
supabase secrets set LLM_PROVIDER=openai
supabase secrets set LLM_MODEL=gpt-4o-mini
```

### Production (Anthropic)

```bash
supabase secrets set ANTHROPIC_API_KEY=sk-ant-...
supabase secrets set LLM_PROVIDER=anthropic
supabase secrets set LLM_MODEL=claude-3-haiku-20240307
```

---

## CORS Configuration

The Edge Function includes CORS headers for cross-origin requests.

### Default Allowed Origins

```typescript
const ALLOWED_ORIGINS = [
  "http://localhost:3000",
  "http://localhost:5173",
  "https://danherrski.github.io",
];
```

### Customizing Origins

Edit `supabase/functions/api/index.ts`:

```typescript
const ALLOWED_ORIGINS = [
  "https://your-custom-domain.com",
  "https://your-username.github.io",
];
```

Redeploy after changes:
```bash
supabase functions deploy api
```

---

## Security Checklist

### Frontend
- [ ] `VITE_API_BASE_URL` points to your Supabase project
- [ ] No secret keys in frontend code
- [ ] CORS origins are restricted to your domains

### Backend (Edge Functions)
- [ ] `SUPABASE_SERVICE_ROLE_KEY` is set as a secret (never in code)
- [ ] `OPENAI_API_KEY` is set as a secret
- [ ] `LLM_PROVIDER` is set to production provider (not stub)

### Database
- [ ] Migrations have been applied
- [ ] pgvector extension is enabled
- [ ] Row Level Security is configured (if using auth)

---

## Troubleshooting

### "SUPABASE_SERVICE_ROLE_KEY is not set"

```bash
# Check if secret exists
supabase secrets list

# Set the secret
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

### "OPENAI_API_KEY is invalid"

- Verify key at https://platform.openai.com/api-keys
- Check for trailing whitespace when copying
- Ensure key has API access (not just ChatGPT Plus)

### "CORS error from frontend"

1. Check that your origin is in `ALLOWED_ORIGINS`
2. Redeploy the Edge Function
3. Hard refresh frontend (Ctrl+Shift+R)

### "Edge Function timeout"

- LLM calls may be slow on first request
- Consider using faster models (gpt-4o-mini)
- Check Supabase function logs for errors

---

## Environment Validation Script

Add to your CI/CD:

```bash
#!/bin/bash
# validate-env.sh

check_var() {
  if [ -z "${!1}" ]; then
    echo "ERROR: $1 is not set"
    exit 1
  fi
}

# For frontend build
check_var VITE_API_BASE_URL

echo "Environment validated successfully"
```
