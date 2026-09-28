-- Migration: sync DB schema with SQLAlchemy models

-- ── users: thêm cột mới ────────────────────────────────────────────────────────
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(50) DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(1000);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_oauth BOOLEAN DEFAULT FALSE;

-- ── documents: thêm cột mới ───────────────────────────────────────────────────
ALTER TABLE documents ADD COLUMN IF NOT EXISTS is_paywall BOOLEAN DEFAULT FALSE;

-- ── document_categories ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS document_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    color VARCHAR(20) DEFAULT '#6366f1',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── researcher_applications ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS researcher_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    admin_note TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

-- ── organizations ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    max_slots INTEGER,
    max_monthly_docs INTEGER,
    max_monthly_docs_owner INTEGER,
    max_annual_docs_owner INTEGER,
    package_type VARCHAR(20) DEFAULT 'monthly',
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── org_invite_codes ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS org_invite_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    duration_months INTEGER NOT NULL,
    max_uses INTEGER,
    used_count INTEGER DEFAULT 0,
    valid_until TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── org_members ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS org_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    invite_code_id UUID REFERENCES org_invite_codes(id),
    duration_months INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
);

-- ── enterprise_tickets ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS enterprise_tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    school_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    message TEXT,
    status VARCHAR(20) DEFAULT 'open',
    admin_note TEXT,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── enterprise_offers ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS enterprise_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID REFERENCES enterprise_tickets(id) ON DELETE SET NULL,
    token VARCHAR(32) UNIQUE NOT NULL,
    school_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    amount INTEGER NOT NULL,
    duration_months INTEGER DEFAULT 12,
    package_type VARCHAR(20) DEFAULT 'monthly',
    max_slots INTEGER,
    max_monthly_docs_member INTEGER,
    max_monthly_docs_owner INTEGER,
    max_annual_docs_owner INTEGER,
    ref_code VARCHAR(30) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    activated_email VARCHAR(255),
    activated_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- ── notifications ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    type VARCHAR(20) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    link VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ── payments ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    plan VARCHAR(50) NOT NULL,
    amount INTEGER NOT NULL,
    ref_code VARCHAR(30) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    reviewed_by UUID REFERENCES users(id)
);
