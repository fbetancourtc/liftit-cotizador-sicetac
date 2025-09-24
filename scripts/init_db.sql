-- Initialize PostgreSQL database for SICETAC Quotation System

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS sicetac;

-- Set search path
SET search_path TO sicetac, public;

-- Create quotations table if not exists
CREATE TABLE IF NOT EXISTS quotations (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Request details
    period VARCHAR(6) NOT NULL,
    configuration VARCHAR(10) NOT NULL,
    origin_code VARCHAR(8) NOT NULL,
    destination_code VARCHAR(8) NOT NULL,
    cargo_type VARCHAR(50),
    unit_type VARCHAR(50),
    logistics_hours FLOAT DEFAULT 0.0,

    -- Quote results (JSONB for better performance in PostgreSQL)
    quotes_data JSONB NOT NULL,

    -- Metadata
    user_id VARCHAR(255),
    company_name VARCHAR(255),
    notes TEXT,
    status VARCHAR(20) DEFAULT 'active',

    -- Calculated fields
    total_cost FLOAT,
    selected_quote_index INTEGER
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_quotations_user_id ON quotations(user_id);
CREATE INDEX IF NOT EXISTS idx_quotations_status ON quotations(status);
CREATE INDEX IF NOT EXISTS idx_quotations_user_status ON quotations(user_id, status);
CREATE INDEX IF NOT EXISTS idx_quotations_period_config ON quotations(period, configuration);
CREATE INDEX IF NOT EXISTS idx_quotations_route ON quotations(origin_code, destination_code);
CREATE INDEX IF NOT EXISTS idx_quotations_created_at ON quotations(created_at);
CREATE INDEX IF NOT EXISTS idx_quotations_quotes_data ON quotations USING GIN (quotes_data);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_quotations_updated_at ON quotations;
CREATE TRIGGER update_quotations_updated_at
    BEFORE UPDATE ON quotations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create audit table for tracking changes
CREATE TABLE IF NOT EXISTS quotations_audit (
    audit_id SERIAL PRIMARY KEY,
    quotation_id INTEGER NOT NULL,
    action VARCHAR(10) NOT NULL,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    old_data JSONB,
    new_data JSONB
);

-- Create index on audit table
CREATE INDEX IF NOT EXISTS idx_audit_quotation_id ON quotations_audit(quotation_id);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON quotations_audit(changed_at);

-- Create function for audit logging
CREATE OR REPLACE FUNCTION audit_quotations_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO quotations_audit(quotation_id, action, changed_by, old_data)
        VALUES (OLD.id, 'DELETE', current_user, row_to_json(OLD)::jsonb);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO quotations_audit(quotation_id, action, changed_by, old_data, new_data)
        VALUES (NEW.id, 'UPDATE', current_user, row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO quotations_audit(quotation_id, action, changed_by, new_data)
        VALUES (NEW.id, 'INSERT', current_user, row_to_json(NEW)::jsonb);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Create trigger for audit logging
DROP TRIGGER IF EXISTS audit_quotations ON quotations;
CREATE TRIGGER audit_quotations
    AFTER INSERT OR UPDATE OR DELETE ON quotations
    FOR EACH ROW
    EXECUTE FUNCTION audit_quotations_changes();

-- Create materialized view for statistics (optional)
CREATE MATERIALIZED VIEW IF NOT EXISTS quotations_stats AS
SELECT
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as total_quotes,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT company_name) as unique_companies,
    AVG(total_cost) as avg_cost,
    origin_code,
    destination_code,
    configuration
FROM quotations
WHERE status = 'active'
GROUP BY month, origin_code, destination_code, configuration;

-- Create index on materialized view
CREATE INDEX IF NOT EXISTS idx_stats_month ON quotations_stats(month);

-- Grant permissions (adjust user as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA sicetac TO sicetac_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA sicetac TO sicetac_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA sicetac TO sicetac_user;