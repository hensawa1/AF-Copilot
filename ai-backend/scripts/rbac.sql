-- ============================================================================
-- RBAC — AF Copilot
-- SQLite não possui papéis nativos (GRANT/DENY). A política é aplicada na API
-- pela dependência require_perfil() em app/core/auth_deps.py, usando a tabela
-- app_users.perfil. Abaixo está a especificação equivalente em GRANT/DENY,
-- mantida como documentação/evidência da proposta de segurança.
-- ============================================================================

-- Papéis
-- ADMINISTRADOR: acesso total (cadastro, LME, auditoria, exportação, IA)
-- FARMACEUTICO:  consultas de pacientes/LMEs, ações em LME, validação de receita,
--                IA (incluindo pacientes) e insights; SEM exportação de auditoria
-- AUDITOR:       somente leitura de auditoria, pacientes e IA; SEM ações e SEM cadastro
-- ASSISTENTE:    acesso mínimo: SEM auditoria, SEM exportação, SEM cadastro e
--                SEM dados de pacientes mesmo quando consultados pela IA

-- GRANT (equivalente implementado em require_perfil)
-- GRANT SELECT, INSERT, UPDATE ON fictional_lmes    TO ADMINISTRADOR, FARMACEUTICO;
-- GRANT SELECT, INSERT          ON catalog_medications TO ADMINISTRADOR, FARMACEUTICO;
-- GRANT SELECT                  ON audit_logs        TO ADMINISTRADOR, AUDITOR, FARMACEUTICO;
-- GRANT SELECT                  ON fictional_users   TO ADMINISTRADOR, FARMACEUTICO, AUDITOR;
-- GRANT EXECUTE ON admin_insights, admin_ask         TO ADMINISTRADOR, FARMACEUTICO, AUDITOR;
-- GRANT EXECUTE ON admin_ask (apenas intenções agregadas) TO ASSISTENTE;

-- DENY (equivalente implementado nos endpoints)
-- DENY INSERT, UPDATE, DELETE ON audit_logs          TO FARMACEUTICO, AUDITOR, ASSISTENTE;
-- DENY EXPORT audit_logs                             TO FARMACEUTICO, ASSISTENTE;
-- DENY DELETE ON fictional_lmes                      TO ALL;
-- DENY SELECT ON fictional_users                     TO ASSISTENTE;

-- Regra adicional de integração (IA respeita RBAC):
-- O perfil ASSISTENTE não obtém linhas de pacientes/LMEs via /admin/ask
-- (intenções "pacientes", "lmes-pendentes" e "lmes-por-cid"); a resposta é
-- negada antes de o modelo redigir qualquer texto. FARMACEUTICO e AUDITOR
-- podem consultar pacientes, pois esse é o escopo funcional desses perfis.

-- Tabelas reais usadas pelo aplicativo (SQLite):
--   app_users(id, username, password_hash, salt, nome, perfil, unidade, created_at)
--   app_sessions(id, token, username, created_at, revoked)
--   audit_logs(id, actor, acao, entidade, entidade_id, detalhes, created_at)
--   fictional_users, fictional_lmes, catalog_medications
