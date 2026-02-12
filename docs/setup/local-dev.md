# Local Development with Supabase CLI

This guide covers running Sponge locally using the Supabase CLI.

---

## Prerequisites

1. **Docker** - Required for local Supabase
   ```bash
   # macOS
   brew install --cask docker

   # Linux
   curl -fsSL https://get.docker.com | sh
   ```

2. **Supabase CLI**
   ```bash
   # npm
   npm install -g supabase

   # Homebrew
   brew install supabase/tap/supabase
   ```

3. **Deno** (for Edge Function development)
   ```bash
   # macOS/Linux
   curl -fsSL https://deno.land/install.sh | sh

   # Homebrew
   brew install deno
   ```

---

## Quick Start

### 1. Start Local Supabase

```bash
# From project root
cd /path/to/sponge

# Start all Supabase services
supabase start
```

This starts:
- PostgreSQL on port 54322
- API Gateway on port 54321
- Studio (dashboard) on port 54323
- Storage on port 54321

### 2. Apply Migrations

```bash
# Apply all migrations
supabase db push

# Or reset and apply fresh
supabase db reset
```

### 3. Start Edge Function

```bash
# Serve the API function locally
supabase functions serve api --env-file .env

# Or with debug output
supabase functions serve api --env-file .env --debug
```

### 4. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Access Services

| Service | URL |
|---------|-----|
| API | http://localhost:54321/functions/v1/api |
| Studio | http://localhost:54323 |
| Database | postgresql://postgres:postgres@localhost:54322/postgres |
| Storage | http://localhost:54321/storage/v1 |

---

## Common Commands

### Database

```bash
# Apply migrations
supabase db push

# Reset database (drops all data!)
supabase db reset

# Create new migration
supabase migration new <name>

# View migration status
supabase migration list

# Open SQL editor
supabase db studio
```

### Edge Functions

```bash
# Serve all functions
supabase functions serve

# Serve specific function
supabase functions serve api

# Deploy to cloud
supabase functions deploy api

# View function logs
supabase functions logs api
```

### Storage

```bash
# List buckets
supabase storage ls

# Create bucket
supabase storage create uploads
```

### General

```bash
# View status
supabase status

# Stop all services
supabase stop

# View logs
supabase logs
```

---

## Environment Setup

### Create .env file

```bash
cp .env.example .env
```

### Configure for local development

```bash
# .env
VITE_API_BASE_URL=http://localhost:54321/functions/v1/api
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=<from supabase status>
LLM_PROVIDER=stub
```

### Get local credentials

```bash
supabase status
```

Output includes:
- `anon key` - Use for VITE_SUPABASE_ANON_KEY
- `service_role key` - Used automatically by CLI

---

## Development Workflow

### 1. Making Schema Changes

```bash
# Create a new migration
supabase migration new add_user_preferences

# Edit the migration file in supabase/migrations/
# Then apply it
supabase db push
```

### 2. Testing Edge Functions

```bash
# Health check
curl http://localhost:54321/functions/v1/api/health

# Create chat turn
curl -X POST http://localhost:54321/functions/v1/api/chat_turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'

# Get graph view
curl "http://localhost:54321/functions/v1/api/graph_view?session_id=<id>"
```

### 3. Debugging

```bash
# View function logs in real-time
supabase functions serve api --debug

# Check database
supabase db studio
# Opens Studio at http://localhost:54323
```

### 4. Resetting Everything

```bash
# Stop services
supabase stop

# Remove all data
supabase stop --no-backup

# Start fresh
supabase start
supabase db push
```

---

## Troubleshooting

### "Docker is not running"

Start Docker Desktop or the Docker daemon:
```bash
# macOS/Windows
open -a Docker

# Linux
sudo systemctl start docker
```

### "Port already in use"

```bash
# Find what's using the port
lsof -i :54321

# Or use different ports
supabase start --api-port 54421
```

### "Function not found"

```bash
# Ensure you're in the project root
pwd  # Should show /path/to/sponge

# Check function exists
ls supabase/functions/api/

# Restart function serving
supabase functions serve api
```

### "Migration failed"

```bash
# Check migration syntax
cat supabase/migrations/20240130000001_create_enums.sql

# Reset and retry
supabase db reset
```

### "Cannot connect to database"

```bash
# Check Supabase is running
supabase status

# Restart services
supabase stop && supabase start
```

---

## IDE Setup

### VS Code Extensions

- **Deno** - For Edge Function development
- **PostgreSQL** - For SQL syntax highlighting
- **Supabase** - Official Supabase extension

### Deno Configuration

Create `.vscode/settings.json`:
```json
{
  "deno.enable": true,
  "deno.lint": true,
  "deno.unstable": true,
  "deno.enablePaths": ["supabase/functions"]
}
```

---

## Next Steps

1. [Supabase Setup Guide](./supabase-setup.md) - For cloud deployment
2. [Deploy Environment Guide](./deploy-env.md) - For production configuration
3. [Storage Configuration](./storage.md) - For file uploads
