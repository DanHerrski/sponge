# Supabase Project Setup Guide

This guide walks through setting up a Supabase project for the Sponge backend.

---

## 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click **New Project**
3. Configure:
   - **Name**: `sponge` (or your preferred name)
   - **Database Password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users
   - **Pricing Plan**: Free tier works for MVP
4. Click **Create new project** and wait ~2 minutes for provisioning

---

## 2. Find Your Project Credentials

After project creation, find these values in the Supabase dashboard:

### Project URL
**Location**: Settings → API → Project URL
```
https://<project-ref>.supabase.co
```

### Anon Key (Public)
**Location**: Settings → API → Project API Keys → `anon` `public`
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
- Safe to expose in frontend code
- Used for client-side requests with Row Level Security

### Service Role Key (Secret)
**Location**: Settings → API → Project API Keys → `service_role` `secret`
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```
- **NEVER expose in frontend code**
- Bypasses Row Level Security
- Used only in server-side code (Edge Functions)

### Database Connection String
**Location**: Settings → Database → Connection string → URI
```
postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
```
- Used for direct database connections (migrations, admin tasks)

---

## 3. Required Secrets

You need to configure secrets in **two places**:

### A. Supabase Edge Function Secrets

Set these via CLI or Supabase Dashboard (Settings → Edge Functions → Secrets):

```bash
# Required: Your OpenAI API key for LLM extraction
supabase secrets set OPENAI_API_KEY=sk-...

# Required: Service role key (from Settings → API → service_role secret)
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

### B. GitHub Repository Secret

Set this in GitHub (Settings → Secrets → Actions):

| Secret | Value |
|--------|-------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://<project-ref>.supabase.co/functions/v1/api` |

This tells the frontend where to send API requests.

---

## 4. Enable pgvector Extension

The schema uses pgvector for embeddings. Enable it:

1. Go to **Database → Extensions**
2. Search for `vector`
3. Click **Enable** on the `vector` extension

Or via SQL Editor:
```sql
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;
```

---

## 5. Apply Database Migrations

### Option A: Via Supabase CLI (Recommended)

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref <your-project-ref>

# Apply migrations
supabase db push
```

### Option B: Via SQL Editor

1. Go to **SQL Editor** in dashboard
2. Copy contents of each file in `supabase/migrations/` in order
3. Run each migration

Migration files:
1. `20240130000001_create_enums.sql`
2. `20240130000002_create_tables.sql`
3. `20240130000003_create_indexes.sql`

---

## 6. Deploy Edge Functions

```bash
# Deploy all functions
supabase functions deploy api

# Or deploy with specific flags
supabase functions deploy api --no-verify-jwt
```

After deployment, your API endpoint will be:
```
https://<project-ref>.supabase.co/functions/v1/api
```

---

## 7. Configure CORS for GitHub Pages

Edge Functions need CORS headers for cross-origin requests from GitHub Pages.

The Edge Function includes CORS handling for:
- `https://<username>.github.io`
- `http://localhost:3000` (development)

To customize allowed origins, edit `supabase/functions/api/index.ts`:
```typescript
const ALLOWED_ORIGINS = [
  'https://your-username.github.io',
  'http://localhost:3000',
];
```

---

## 8. Test Your Deployment

### Health Check
```bash
curl https://<project-ref>.supabase.co/functions/v1/api/health
```

Expected response:
```json
{"status": "ok", "timestamp": "2024-01-30T12:00:00Z"}
```

### Create a Session
```bash
curl -X POST https://<project-ref>.supabase.co/functions/v1/api/chat_turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'
```

---

## 9. Deploy Frontend to GitHub Pages

The frontend is automatically built and deployed by GitHub Actions when you push to main. You just need to set up the workflow once.

### One-Time Setup

1. **Create the workflow file** `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install and Build
        run: |
          cd frontend
          npm ci
          npm run build
        env:
          NEXT_PUBLIC_API_BASE_URL: ${{ secrets.NEXT_PUBLIC_API_BASE_URL }}

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./frontend/out
```

2. **Add GitHub secret**: Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Name: `NEXT_PUBLIC_API_BASE_URL`
   - Value: `https://<project-ref>.supabase.co/functions/v1/api`

3. **Enable GitHub Pages**: Go to **Settings** → **Pages** → set Source to **GitHub Actions**

4. **Push to main** - the Action runs automatically and deploys your site to `https://<username>.github.io/<repo>/`

### Local Development (Optional)

If you want to test locally before pushing:

```bash
cd frontend
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:54321/functions/v1/api" > .env.local
npm install
npm run dev
```

---

## Troubleshooting

### "Permission denied" on Edge Function
- Check that `SUPABASE_SERVICE_ROLE_KEY` is set in function secrets
- Verify the key hasn't been rotated

### "relation does not exist"
- Migrations haven't been applied
- Run `supabase db push` or apply SQL manually

### CORS errors
- Check that your origin is in the `ALLOWED_ORIGINS` list
- Verify the Edge Function is returning proper CORS headers

### pgvector errors
- Ensure the `vector` extension is enabled
- Check that embeddings column uses correct dimension (1536)

---

## Next Steps

1. [Configure Storage](./storage.md) for file uploads (optional, for document uploads)
2. [Deploy Environment Guide](./deploy-env.md) for all environment variable details

## Quick Reference: Your Deployment Checklist

- [ ] Create Supabase project at supabase.com
- [ ] Copy your Project URL: `https://<ref>.supabase.co`
- [ ] Enable pgvector extension in Database → Extensions
- [ ] Apply migrations with `supabase db push` (or paste SQL manually)
- [ ] Set Edge Function secrets: `supabase secrets set OPENAI_API_KEY=sk-...`
- [ ] Deploy Edge Function: `supabase functions deploy api --no-verify-jwt`
- [ ] Update CORS origins in Edge Function if using custom domain
- [ ] Add GitHub secret `NEXT_PUBLIC_API_BASE_URL` with your Supabase URL
- [ ] Push to main branch to trigger GitHub Pages deployment
