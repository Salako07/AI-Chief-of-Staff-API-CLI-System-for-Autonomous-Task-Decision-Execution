-- Migration: Add DigitalOcean Spaces support to media_files table
-- Date: 2024-06-01
-- Purpose: Store video files in DigitalOcean Spaces instead of local disk

-- Add Spaces-related columns to media_files table
ALTER TABLE media_files
  ADD COLUMN IF NOT EXISTS spaces_key VARCHAR(500),
  ADD COLUMN IF NOT EXISTS spaces_url TEXT,
  ADD COLUMN IF NOT EXISTS storage_type VARCHAR(20) DEFAULT 'local'
    CHECK(storage_type IN ('local', 'spaces'));

-- Add index for efficient cleanup queries
CREATE INDEX IF NOT EXISTS idx_media_files_created_storage
  ON media_files(created_at, storage_type);

-- Add index for Spaces key lookups
CREATE INDEX IF NOT EXISTS idx_media_files_spaces_key
  ON media_files(spaces_key)
  WHERE spaces_key IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN media_files.spaces_key IS 'Remote file path in DigitalOcean Spaces (e.g., videos/2024/06/abc-123.mp4)';
COMMENT ON COLUMN media_files.spaces_url IS 'Public or presigned URL for accessing the file';
COMMENT ON COLUMN media_files.storage_type IS 'Storage location: local (disk) or spaces (cloud)';

-- Update existing records to have storage_type = 'local' (if not already set)
UPDATE media_files
SET storage_type = 'local'
WHERE storage_type IS NULL;
