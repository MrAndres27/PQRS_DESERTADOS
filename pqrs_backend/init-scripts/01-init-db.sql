-- ============================================================================
-- SCRIPT DE INICIALIZACIÓN - Sistema PQRS
-- Equipo Desertados PQRS
-- Base de datos: PostgreSQL 16
-- ============================================================================
-- 
-- Este script crea:
-- - Todas las tablas del sistema
-- - Relaciones y constraints
-- - Índices para optimización
-- - Triggers automáticos
-- - Vistas útiles para reportes
-- - Datos iniciales (roles, permisos, estados, tipos)
-- - Usuarios de ejemplo (1 por rol)
-- 
-- ============================================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TABLA: roles
-- Define los roles del sistema (Administrador, Gestor, Ciudadano)
-- ============================================================================

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    is_system BOOLEAN DEFAULT FALSE,  -- Roles del sistema no se pueden eliminar
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_roles_name ON roles(name);
CREATE INDEX idx_roles_active ON roles(is_active);

-- ============================================================================
-- TABLA: permissions
-- Permisos granulares del sistema
-- ============================================================================

CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    description VARCHAR(500),
    category VARCHAR(50) NOT NULL,  -- system, pqrs, users, roles, etc.
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_permissions_name ON permissions(name);
CREATE INDEX idx_permissions_category ON permissions(category);
CREATE INDEX idx_permissions_active ON permissions(is_active);

-- ============================================================================
-- TABLA: role_permissions
-- Tabla intermedia para relación muchos a muchos entre roles y permisos
-- ============================================================================

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_role_permissions_permission ON role_permissions(permission_id);

-- ============================================================================
-- TABLA: departments
-- Departamentos de la organización
-- ============================================================================

CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_departments_name ON departments(name);
CREATE INDEX idx_departments_active ON departments(is_active);

-- ============================================================================
-- TABLA: users
-- Usuarios del sistema
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(200),
    document_type VARCHAR(10),  -- CC, TI, CE, PAS
    document_number VARCHAR(20),
    role_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role_id);
CREATE INDEX idx_users_department ON users(department_id);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_document ON users(document_type, document_number);

-- ============================================================================
-- TABLA: pqrs_types
-- Tipos de PQRS (Petición, Queja, Reclamo, Sugerencia)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pqrs_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    color VARCHAR(20),  -- Para UI
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pqrs_types_name ON pqrs_types(name);
CREATE INDEX idx_pqrs_types_active ON pqrs_types(is_active);

-- ============================================================================
-- TABLA: pqrs_status
-- Estados de PQRS (Nuevo, En Proceso, Resuelto, Cerrado, Cancelado)
-- ============================================================================

CREATE TABLE IF NOT EXISTS pqrs_status (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200),
    color VARCHAR(20),  -- Para UI
    is_final BOOLEAN DEFAULT FALSE,  -- Estados finales (Cerrado, Cancelado)
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pqrs_status_name ON pqrs_status(name);
CREATE INDEX idx_pqrs_status_active ON pqrs_status(is_active);
CREATE INDEX idx_pqrs_status_order ON pqrs_status(order_index);

-- ============================================================================
-- TABLA: pqrs
-- Tabla principal de PQRS
-- ============================================================================

CREATE TABLE IF NOT EXISTS pqrs (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,  -- PQRS-YYYYMMDD-XXXX
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    pqrs_type_id INTEGER NOT NULL REFERENCES pqrs_types(id),
    status_id INTEGER NOT NULL REFERENCES pqrs_status(id),
    priority VARCHAR(20) DEFAULT 'media',  -- baja, media, alta, urgente
    created_by_user_id INTEGER NOT NULL REFERENCES users(id),
    assigned_to_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    response TEXT,
    response_date TIMESTAMP,
    closed_date TIMESTAMP,
    due_date TIMESTAMP,
    is_anonymous BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pqrs_code ON pqrs(code);
CREATE INDEX idx_pqrs_type ON pqrs(pqrs_type_id);
CREATE INDEX idx_pqrs_status ON pqrs(status_id);
CREATE INDEX idx_pqrs_priority ON pqrs(priority);
CREATE INDEX idx_pqrs_created_by ON pqrs(created_by_user_id);
CREATE INDEX idx_pqrs_assigned_to ON pqrs(assigned_to_user_id);
CREATE INDEX idx_pqrs_department ON pqrs(department_id);
CREATE INDEX idx_pqrs_created_at ON pqrs(created_at DESC);
CREATE INDEX idx_pqrs_due_date ON pqrs(due_date);

-- ============================================================================
-- TABLA: pqrs_history
-- Historial de cambios de estado de PQRS
-- ============================================================================

CREATE TABLE IF NOT EXISTS pqrs_history (
    id SERIAL PRIMARY KEY,
    pqrs_id INTEGER NOT NULL REFERENCES pqrs(id) ON DELETE CASCADE,
    old_status_id INTEGER REFERENCES pqrs_status(id),
    new_status_id INTEGER NOT NULL REFERENCES pqrs_status(id),
    changed_by_user_id INTEGER NOT NULL REFERENCES users(id),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pqrs_history_pqrs ON pqrs_history(pqrs_id);
CREATE INDEX idx_pqrs_history_new_status ON pqrs_history(new_status_id);
CREATE INDEX idx_pqrs_history_created_at ON pqrs_history(created_at DESC);

-- ============================================================================
-- TABLA: comments
-- Comentarios en PQRS
-- ============================================================================

CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    pqrs_id INTEGER NOT NULL REFERENCES pqrs(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,  -- Comentario interno (solo staff)
    is_edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_comments_pqrs ON comments(pqrs_id);
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);

-- ============================================================================
-- TABLA: attachments
-- Archivos adjuntos a PQRS
-- ============================================================================

CREATE TABLE IF NOT EXISTS attachments (
    id SERIAL PRIMARY KEY,
    pqrs_id INTEGER NOT NULL REFERENCES pqrs(id) ON DELETE CASCADE,
    uploaded_by_user_id INTEGER NOT NULL REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT NOT NULL,  -- En bytes
    mime_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_attachments_pqrs ON attachments(pqrs_id);
CREATE INDEX idx_attachments_user ON attachments(uploaded_by_user_id);
CREATE INDEX idx_attachments_created_at ON attachments(created_at DESC);

-- ============================================================================
-- TABLA: notifications
-- Notificaciones del sistema
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pqrs_id INTEGER REFERENCES pqrs(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- new_pqrs, status_change, assignment, comment, etc.
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_pqrs ON notifications(pqrs_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at DESC);

-- ============================================================================
-- TABLA: audit_log
-- Registro de auditoría del sistema
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,  -- login, logout, create_pqrs, update_user, etc.
    entity_type VARCHAR(50),  -- pqrs, user, role, etc.
    entity_id INTEGER,
    details JSONB,  -- Detalles adicionales en formato JSON
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Aplicar trigger a todas las tablas con updated_at
CREATE TRIGGER update_roles_updated_at BEFORE UPDATE ON roles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_permissions_updated_at BEFORE UPDATE ON permissions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_departments_updated_at BEFORE UPDATE ON departments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pqrs_types_updated_at BEFORE UPDATE ON pqrs_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pqrs_status_updated_at BEFORE UPDATE ON pqrs_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pqrs_updated_at BEFORE UPDATE ON pqrs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger para generar código PQRS automáticamente
CREATE OR REPLACE FUNCTION generate_pqrs_code()
RETURNS TRIGGER AS $$
DECLARE
    date_part VARCHAR(8);
    sequence_part VARCHAR(4);
    new_code VARCHAR(50);
BEGIN
    IF NEW.code IS NULL OR NEW.code = '' THEN
        date_part := TO_CHAR(CURRENT_DATE, 'YYYYMMDD');
        
        -- Obtener el siguiente número de secuencia del día
        SELECT LPAD((COUNT(*) + 1)::TEXT, 4, '0') INTO sequence_part
        FROM pqrs
        WHERE created_at::DATE = CURRENT_DATE;
        
        new_code := 'PQRS-' || date_part || '-' || sequence_part;
        NEW.code := new_code;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER generate_pqrs_code_trigger BEFORE INSERT ON pqrs
    FOR EACH ROW EXECUTE FUNCTION generate_pqrs_code();

-- Trigger para registrar cambios de estado en historial
CREATE OR REPLACE FUNCTION log_pqrs_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status_id IS DISTINCT FROM NEW.status_id THEN
        INSERT INTO pqrs_history (pqrs_id, old_status_id, new_status_id, changed_by_user_id, comment)
        VALUES (NEW.id, OLD.status_id, NEW.status_id, NEW.assigned_to_user_id, 'Estado actualizado');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER log_pqrs_status_change_trigger AFTER UPDATE ON pqrs
    FOR EACH ROW EXECUTE FUNCTION log_pqrs_status_change();

-- ============================================================================
-- VISTAS ÚTILES
-- ============================================================================

-- Vista: Resumen de PQRS por estado
CREATE OR REPLACE VIEW view_pqrs_by_status AS
SELECT 
    ps.name AS estado,
    ps.color,
    COUNT(p.id) AS total_pqrs,
    COUNT(CASE WHEN p.priority = 'urgente' THEN 1 END) AS urgentes,
    COUNT(CASE WHEN p.priority = 'alta' THEN 1 END) AS altas
FROM pqrs_status ps
LEFT JOIN pqrs p ON ps.id = p.status_id
WHERE ps.is_active = TRUE
GROUP BY ps.id, ps.name, ps.color, ps.order_index
ORDER BY ps.order_index;

-- Vista: Resumen de PQRS por tipo
CREATE OR REPLACE VIEW view_pqrs_by_type AS
SELECT 
    pt.name AS tipo,
    pt.color,
    COUNT(p.id) AS total_pqrs,
    AVG(EXTRACT(EPOCH FROM (COALESCE(p.closed_date, CURRENT_TIMESTAMP) - p.created_at))/86400)::NUMERIC(10,2) AS promedio_dias
FROM pqrs_types pt
LEFT JOIN pqrs p ON pt.id = p.pqrs_type_id
WHERE pt.is_active = TRUE
GROUP BY pt.id, pt.name, pt.color
ORDER BY total_pqrs DESC;

-- Vista: PQRS con detalles completos
CREATE OR REPLACE VIEW view_pqrs_details AS
SELECT 
    p.id,
    p.code,
    p.subject,
    p.description,
    pt.name AS tipo,
    ps.name AS estado,
    p.priority AS prioridad,
    u_created.full_name AS creado_por,
    u_assigned.full_name AS asignado_a,
    d.name AS departamento,
    p.created_at AS fecha_creacion,
    p.due_date AS fecha_limite,
    p.closed_date AS fecha_cierre,
    CASE 
        WHEN p.closed_date IS NOT NULL THEN EXTRACT(EPOCH FROM (p.closed_date - p.created_at))/86400
        ELSE EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - p.created_at))/86400
    END::NUMERIC(10,2) AS dias_transcurridos
FROM pqrs p
JOIN pqrs_types pt ON p.pqrs_type_id = pt.id
JOIN pqrs_status ps ON p.status_id = ps.id
JOIN users u_created ON p.created_by_user_id = u_created.id
LEFT JOIN users u_assigned ON p.assigned_to_user_id = u_assigned.id
LEFT JOIN departments d ON p.department_id = d.id;

-- Vista: Estadísticas por usuario gestor
CREATE OR REPLACE VIEW view_user_stats AS
SELECT 
    u.id,
    u.username,
    u.full_name,
    r.name AS rol,
    COUNT(DISTINCT p_assigned.id) AS pqrs_asignadas,
    COUNT(DISTINCT CASE WHEN ps.is_final = FALSE THEN p_assigned.id END) AS pqrs_pendientes,
    COUNT(DISTINCT CASE WHEN ps.is_final = TRUE THEN p_assigned.id END) AS pqrs_completadas,
    COUNT(DISTINCT c.id) AS comentarios_realizados
FROM users u
JOIN roles r ON u.role_id = r.id
LEFT JOIN pqrs p_assigned ON u.id = p_assigned.assigned_to_user_id
LEFT JOIN pqrs_status ps ON p_assigned.status_id = ps.id
LEFT JOIN comments c ON u.id = c.user_id
WHERE u.is_active = TRUE
GROUP BY u.id, u.username, u.full_name, r.name;

-- ============================================================================
-- DATOS INICIALES
-- ============================================================================

-- Insertar Roles del sistema
INSERT INTO roles (name, description, is_system, is_active) VALUES
('Administrador', 'Acceso completo al sistema', TRUE, TRUE),
('Gestor', 'Gestiona y responde PQRS', TRUE, TRUE),
('Ciudadano', 'Usuario que crea PQRS', TRUE, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insertar Permisos del sistema
INSERT INTO permissions (name, display_name, description, category, is_active) VALUES
-- Permisos de sistema
('system.admin', 'Administración total', 'Acceso completo al sistema', 'system', TRUE),
('system.view_dashboard', 'Ver dashboard', 'Visualizar panel de control', 'system', TRUE),
('system.view_reports', 'Ver reportes', 'Acceder a reportes del sistema', 'system', TRUE),

-- Permisos de PQRS
('pqrs.create', 'Crear PQRS', 'Crear nuevas PQRS', 'pqrs', TRUE),
('pqrs.view_own', 'Ver propias PQRS', 'Ver sus propias PQRS', 'pqrs', TRUE),
('pqrs.view_all', 'Ver todas las PQRS', 'Acceder a todas las PQRS', 'pqrs', TRUE),
('pqrs.update', 'Actualizar PQRS', 'Modificar PQRS existentes', 'pqrs', TRUE),
('pqrs.delete', 'Eliminar PQRS', 'Eliminar PQRS del sistema', 'pqrs', TRUE),
('pqrs.assign', 'Asignar PQRS', 'Asignar PQRS a gestores', 'pqrs', TRUE),
('pqrs.change_status', 'Cambiar estado', 'Modificar estado de PQRS', 'pqrs', TRUE),
('pqrs.respond', 'Responder PQRS', 'Dar respuesta a PQRS', 'pqrs', TRUE),

-- Permisos de usuarios
('users.create', 'Crear usuarios', 'Crear nuevos usuarios', 'users', TRUE),
('users.view', 'Ver usuarios', 'Listar y ver usuarios', 'users', TRUE),
('users.update', 'Actualizar usuarios', 'Modificar datos de usuarios', 'users', TRUE),
('users.delete', 'Eliminar usuarios', 'Eliminar usuarios del sistema', 'users', TRUE),
('users.manage_roles', 'Gestionar roles', 'Asignar roles a usuarios', 'users', TRUE),

-- Permisos de roles y permisos
('roles.create', 'Crear roles', 'Crear nuevos roles', 'roles', TRUE),
('roles.view', 'Ver roles', 'Listar y ver roles', 'roles', TRUE),
('roles.update', 'Actualizar roles', 'Modificar roles existentes', 'roles', TRUE),
('roles.delete', 'Eliminar roles', 'Eliminar roles personalizados', 'roles', TRUE),
('permissions.manage', 'Gestionar permisos', 'Asignar permisos a roles', 'roles', TRUE),

-- Permisos de comentarios
('comments.create', 'Crear comentarios', 'Agregar comentarios a PQRS', 'comments', TRUE),
('comments.view', 'Ver comentarios', 'Ver comentarios de PQRS', 'comments', TRUE),
('comments.update', 'Actualizar comentarios', 'Editar comentarios propios', 'comments', TRUE),
('comments.delete', 'Eliminar comentarios', 'Eliminar comentarios', 'comments', TRUE),
('comments.internal', 'Comentarios internos', 'Crear y ver comentarios internos', 'comments', TRUE),

-- Permisos de archivos
('attachments.upload', 'Subir archivos', 'Adjuntar archivos a PQRS', 'attachments', TRUE),
('attachments.download', 'Descargar archivos', 'Descargar archivos adjuntos', 'attachments', TRUE),
('attachments.delete', 'Eliminar archivos', 'Eliminar archivos adjuntos', 'attachments', TRUE),

-- Permisos de notificaciones
('notifications.view', 'Ver notificaciones', 'Ver propias notificaciones', 'notifications', TRUE),
('notifications.send', 'Enviar notificaciones', 'Enviar notificaciones a usuarios', 'notifications', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Asignar permisos a rol Administrador (TODOS)
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'Administrador'
ON CONFLICT DO NOTHING;

-- Asignar permisos a rol Gestor
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'Gestor' AND p.name IN (
    'system.view_dashboard',
    'system.view_reports',
    'pqrs.view_all',
    'pqrs.update',
    'pqrs.assign',
    'pqrs.change_status',
    'pqrs.respond',
    'comments.create',
    'comments.view',
    'comments.update',
    'comments.internal',
    'attachments.upload',
    'attachments.download',
    'notifications.view'
)
ON CONFLICT DO NOTHING;

-- Asignar permisos a rol Ciudadano
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, permissions p
WHERE r.name = 'Ciudadano' AND p.name IN (
    'pqrs.create',
    'pqrs.view_own',
    'comments.create',
    'comments.view',
    'attachments.upload',
    'attachments.download',
    'notifications.view'
)
ON CONFLICT DO NOTHING;

-- Insertar Tipos de PQRS
INSERT INTO pqrs_types (name, description, color, is_active) VALUES
('Petición', 'Solicitud de información o servicio', '#3498db', TRUE),
('Queja', 'Expresión de insatisfacción', '#e74c3c', TRUE),
('Reclamo', 'Manifestación de inconformidad por incumplimiento', '#e67e22', TRUE),
('Sugerencia', 'Propuesta de mejora', '#2ecc71', TRUE),
('Felicitación', 'Reconocimiento positivo', '#9b59b6', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insertar Estados de PQRS
INSERT INTO pqrs_status (name, description, color, is_final, order_index, is_active) VALUES
('Nuevo', 'PQRS recién creada', '#95a5a6', FALSE, 1, TRUE),
('En Revisión', 'PQRS siendo revisada', '#3498db', FALSE, 2, TRUE),
('En Proceso', 'PQRS en proceso de atención', '#f39c12', FALSE, 3, TRUE),
('Pendiente Información', 'Esperando información del ciudadano', '#e67e22', FALSE, 4, TRUE),
('Resuelto', 'PQRS resuelta', '#2ecc71', FALSE, 5, TRUE),
('Cerrado', 'PQRS cerrada exitosamente', '#27ae60', TRUE, 6, TRUE),
('Cancelado', 'PQRS cancelada', '#e74c3c', TRUE, 7, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insertar Departamentos
INSERT INTO departments (name, description, is_active) VALUES
('Atención al Cliente', 'Departamento de servicio al cliente', TRUE),
('Sistemas', 'Departamento de tecnología e IT', TRUE),
('Recursos Humanos', 'Gestión de personal', TRUE),
('Administración', 'Administración general', TRUE),
('Calidad', 'Control de calidad', TRUE)
ON CONFLICT (name) DO NOTHING;

-- Insertar Usuarios de ejemplo (contraseña hasheada: admin123, gestor123, ciudadano123)
-- Nota: Las contraseñas están hasheadas con bcrypt

-- Usuario Admin: Felipe Cañón
INSERT INTO users (username, email, password_hash, full_name, phone, address, document_type, document_number, role_id, department_id, is_active)
SELECT 
    'felipe.canon',
    'jpcano360@gmail.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5eoKZqZWJqRB6', -- admin123
    'Felipe Cañón',
    '3004343918',
    'Carrera 8A Número 182-61',
    'CC',
    '1234567890',
    r.id,
    d.id,
    TRUE
FROM roles r, departments d
WHERE r.name = 'Administrador' AND d.name = 'Administración'
ON CONFLICT (username) DO NOTHING;

-- Usuario Gestor
INSERT INTO users (username, email, password_hash, full_name, phone, document_type, document_number, role_id, department_id, is_active)
SELECT 
    'gestor.prueba',
    'gestor@pqrs.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', -- gestor123
    'María García',
    '3001234567',
    'CC',
    '9876543210',
    r.id,
    d.id,
    TRUE
FROM roles r, departments d
WHERE r.name = 'Gestor' AND d.name = 'Atención al Cliente'
ON CONFLICT (username) DO NOTHING;

-- Usuario Ciudadano
INSERT INTO users (username, email, password_hash, full_name, phone, document_type, document_number, role_id, is_active)
SELECT 
    'ciudadano.prueba',
    'ciudadano@pqrs.com',
    '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', -- ciudadano123
    'Juan Pérez',
    '3009876543',
    'CC',
    '1122334455',
    r.id,
    TRUE
FROM roles r
WHERE r.name = 'Ciudadano'
ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- FIN DEL SCRIPT
-- ============================================================================

-- Verificar instalación
DO $$
DECLARE
    table_count INTEGER;
    user_count INTEGER;
    role_count INTEGER;
    permission_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO role_count FROM roles;
    SELECT COUNT(*) INTO permission_count FROM permissions;
    
    RAISE NOTICE '✅ Base de datos inicializada correctamente';
    RAISE NOTICE '📊 Tablas creadas: %', table_count;
    RAISE NOTICE '👥 Usuarios creados: %', user_count;
    RAISE NOTICE '🔐 Roles creados: %', role_count;
    RAISE NOTICE '🔑 Permisos creados: %', permission_count;
    RAISE NOTICE '';
    RAISE NOTICE '🎉 Sistema PQRS listo para usar';
    RAISE NOTICE '';
    RAISE NOTICE '👤 Usuario Admin:';
    RAISE NOTICE '   Username: felipe.canon';
    RAISE NOTICE '   Email: jpcano360@gmail.com';
    RAISE NOTICE '   Password: admin123';
END $$;
