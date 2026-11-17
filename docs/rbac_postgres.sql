-- Equivalente SQL do RBAC implementado na API (referência para PostgreSQL).
-- A aplicação usa SQLite + FastAPI; a política real está em app/core/auth_deps.py.
CREATE ROLE administrador;
CREATE ROLE farmaceutico;
CREATE ROLE auditor;
CREATE ROLE assistente;

GRANT SELECT, INSERT, UPDATE ON fictional_lmes TO administrador, farmaceutico;
GRANT SELECT, INSERT ON catalog_medications TO administrador, farmaceutico;
GRANT SELECT ON fictional_users TO administrador, farmaceutico, auditor;
GRANT SELECT ON audit_logs TO administrador, auditor, farmaceutico;
GRANT EXECUTE ON FUNCTION admin_ask(text) TO administrador, farmaceutico, auditor, assistente;

DENY SELECT ON fictional_users TO assistente;
DENY INSERT, UPDATE, DELETE ON audit_logs TO farmaceutico, auditor, assistente;
REVOKE EXPORT ON audit_logs FROM farmaceutico, assistente;
REVOKE ALL ON catalog_medications FROM assistente;
