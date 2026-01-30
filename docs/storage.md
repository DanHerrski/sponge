# Supabase Storage Configuration

This guide covers setting up Supabase Storage for the Sponge file upload feature.

---

## Overview

Sponge uses Supabase Storage for uploaded files (transcripts, documents, notes). The MVP uses a simple private bucket with metadata stored in the `documents` table.

---

## 1. Create Storage Bucket

### Via Dashboard

1. Go to **Storage** in the Supabase dashboard
2. Click **New bucket**
3. Configure:
   - **Name**: `uploads`
   - **Public**: **OFF** (private bucket)
   - **File size limit**: 50MB (adjust as needed)
   - **Allowed MIME types**: Leave empty for MVP (allow all)
4. Click **Create bucket**

### Via SQL

```sql
-- Run in SQL Editor
INSERT INTO storage.buckets (id, name, public)
VALUES ('uploads', 'uploads', false)
ON CONFLICT (id) DO NOTHING;
```

---

## 2. Storage Policies

For MVP, we use a simple policy that allows authenticated access via service role.

### Private Access (Service Role Only)

The Edge Function uses the `service_role` key which bypasses RLS. No additional policies needed for MVP.

### Future: User-Scoped Access

For production with user authentication:

```sql
-- Allow users to upload to their session folders
CREATE POLICY "Users can upload to their sessions"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'uploads'
  AND (storage.foldername(name))[1] IN (
    SELECT id::text FROM sessions WHERE user_id = auth.uid()
  )
);

-- Allow users to read their session files
CREATE POLICY "Users can read their session files"
ON storage.objects FOR SELECT
USING (
  bucket_id = 'uploads'
  AND (storage.foldername(name))[1] IN (
    SELECT id::text FROM sessions WHERE user_id = auth.uid()
  )
);
```

---

## 3. File Organization

Files are organized by session:

```
uploads/
├── {session_id}/
│   ├── document1.pdf
│   ├── transcript.txt
│   └── notes.docx
├── {another_session_id}/
│   └── ...
```

### Storage Path Convention

```
uploads/{session_id}/{filename}
```

The `documents.storage_path` column stores this full path.

---

## 4. Upload Flow

### Current (Metadata Only)

1. Frontend calls `POST /upload` with metadata
2. Edge Function stores metadata in `documents` table
3. File upload to Storage is pending implementation

### Future (Full Upload)

1. Frontend requests signed upload URL from Edge Function
2. Frontend uploads directly to Storage using signed URL
3. Edge Function stores metadata after upload confirmation

### Signed URL Upload (Future Implementation)

```typescript
// Edge Function: Generate signed upload URL
const { data, error } = await supabase.storage
  .from('uploads')
  .createSignedUploadUrl(`${sessionId}/${filename}`);

return { upload_url: data.signedUrl, path: data.path };
```

```typescript
// Frontend: Upload file
const response = await fetch(upload_url, {
  method: 'PUT',
  body: file,
  headers: { 'Content-Type': file.type },
});
```

---

## 5. Downloading Files

### Via Edge Function

```typescript
const { data, error } = await supabase.storage
  .from('uploads')
  .download(`${sessionId}/${filename}`);
```

### Via Signed URL

```typescript
const { data, error } = await supabase.storage
  .from('uploads')
  .createSignedUrl(`${sessionId}/${filename}`, 3600); // 1 hour expiry

return { download_url: data.signedUrl };
```

---

## 6. File Size Limits

| Tier | Max File Size | Max Total Storage |
|------|---------------|-------------------|
| Free | 50MB | 1GB |
| Pro | 50MB (configurable) | 100GB |

For larger files, consider:
- Chunked uploads
- External storage (S3) with Supabase as metadata store

---

## 7. Supported File Types

MVP supports:
- `.txt` - Plain text
- `.md` - Markdown
- `.docx` - Word documents
- `.pdf` - PDF documents

Recommended MIME type restrictions:
```
text/plain
text/markdown
application/vnd.openxmlformats-officedocument.wordprocessingml.document
application/pdf
```

---

## 8. Cleanup and Retention

### Delete Session Files

When a session is deleted, clean up storage:

```typescript
// In session deletion handler
const { data: files } = await supabase.storage
  .from('uploads')
  .list(sessionId);

if (files?.length) {
  const paths = files.map(f => `${sessionId}/${f.name}`);
  await supabase.storage.from('uploads').remove(paths);
}
```

### Automatic Cleanup (Future)

Consider implementing:
- Retention policy (delete files older than X days)
- Orphan file cleanup (files without document records)

---

## 9. Troubleshooting

### "Bucket not found"
- Create the `uploads` bucket in Storage dashboard
- Check bucket name matches exactly

### "Permission denied"
- Verify service role key is being used
- Check storage policies if using user auth

### "File too large"
- Check bucket file size limit
- Consider chunked upload for large files

### "Invalid MIME type"
- Check bucket's allowed MIME types setting
- Either allow all or add the specific type

---

## Next Steps

1. [Deploy Environment](./deploy-env.md) for production configuration
2. Implement full file upload in Edge Function
3. Add file processing for nugget extraction from documents
