-- ============================================================
-- Supabase Row Level Security (RLS) Enforcement Script
-- Protects all public tables and sensitive columns from direct unauthorized API access.
-- ============================================================

-- Enable RLS on all application tables
ALTER TABLE IF EXISTS institutions ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS users ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS otp_verifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS verification_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS batch_logs ENABLE ROW LEVEL SECURITY;

-- Note:
-- FastAPI connects directly over PostgreSQL (via DATABASE_URL / connection pooler)
-- as the database owner, maintaining full backend database operations while
-- completely blocking unauthorized public PostgREST / anon API calls from the web.
