"use client";

import { useRef, useState } from "react";
import { uploadFile, type UploadResponse } from "@/lib/api";

interface UploadButtonProps {
  sessionId: string | null;
  onUploadComplete?: (response: UploadResponse) => void;
}

export function UploadButton({ sessionId, onUploadComplete }: UploadButtonProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleClick = () => {
    if (!sessionId) return;
    fileRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !sessionId) return;

    setIsUploading(true);
    try {
      const response = await uploadFile(sessionId, file);
      onUploadComplete?.(response);
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setIsUploading(false);
      // Reset input so the same file can be re-uploaded
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <>
      <input
        ref={fileRef}
        type="file"
        accept=".txt,.docx"
        onChange={handleFileChange}
        style={{ display: "none" }}
      />
      <button
        onClick={handleClick}
        disabled={!sessionId || isUploading}
        title={!sessionId ? "Start a session first" : "Upload .txt or .docx"}
        style={{
          padding: "8px 14px",
          background: !sessionId || isUploading ? "#e0e0e0" : "#f5f5f5",
          color: !sessionId || isUploading ? "#aaa" : "#333",
          border: "1px solid #d0d0d0",
          borderRadius: "6px",
          fontSize: "13px",
          cursor: !sessionId || isUploading ? "not-allowed" : "pointer",
        }}
      >
        {isUploading ? "Uploading..." : "Upload doc"}
      </button>
    </>
  );
}
