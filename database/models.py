"""
database/models.py
-------------------
Loyihadagi barcha jadvallarning SQL sxemasi. Har bir CREATE TABLE
IF NOT EXISTS ko'rinishida yozilgan, shuning uchun bir necha marta
chaqirilishi xavfsiz.
"""

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id     INTEGER NOT NULL UNIQUE,
    internal_id     TEXT NOT NULL UNIQUE,      -- CH-001, CH-002, ...
    full_name       TEXT,
    username        TEXT,
    status          TEXT NOT NULL DEFAULT 'faol',
    registered_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_activity   TEXT,
    is_deleted      INTEGER NOT NULL DEFAULT 0
);
"""

ADMINS_TABLE = """
CREATE TABLE IF NOT EXISTS admins (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id     INTEGER NOT NULL UNIQUE,
    full_name       TEXT,
    added_at        TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    telegram_id     INTEGER NOT NULL,
    internal_id     TEXT NOT NULL,
    report_date     TEXT NOT NULL DEFAULT (date('now')),
    report_time     TEXT NOT NULL DEFAULT (time('now')),
    report_type     TEXT,                      -- masalan: 'kunlik', 'haftalik'
    media_type      TEXT,                       -- text/photo/video/audio/voice/document/location/contact
    file_id         TEXT,
    content         TEXT,
    status          TEXT NOT NULL DEFAULT 'yangi',
    is_read         INTEGER NOT NULL DEFAULT 0,
    reminder_count  INTEGER NOT NULL DEFAULT 0,
    is_replied      INTEGER NOT NULL DEFAULT 0,
    admin_msg_id    INTEGER,                     -- admin chatidagi xabar id (o'chirish uchun)
    user_msg_id     INTEGER,                     -- foydalanuvchi chatidagi xabar id (o'chirish uchun)
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SCHEDULES_TABLE = """
CREATE TABLE IF NOT EXISTS schedules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    weekday         INTEGER NOT NULL,            -- 0=Dushanba ... 6=Yakshanba
    time            TEXT NOT NULL,                -- 'HH:MM'
    reminder_text   TEXT NOT NULL,
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

REMINDERS_TABLE = """
CREATE TABLE IF NOT EXISTS reminders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    schedule_id     INTEGER REFERENCES schedules(id) ON DELETE SET NULL,
    sent_at         TEXT NOT NULL DEFAULT (datetime('now')),
    chat_message_id INTEGER,
    delivered       INTEGER NOT NULL DEFAULT 1,
    responded       INTEGER NOT NULL DEFAULT 0
);
"""

STATISTICS_TABLE = """
CREATE TABLE IF NOT EXISTS statistics (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    period_type         TEXT NOT NULL,           -- daily/weekly/monthly/all
    period_value        TEXT NOT NULL,           -- '2026-07-19' / '2026-W29' / '2026-07'
    reports_count       INTEGER NOT NULL DEFAULT 0,
    reminders_count     INTEGER NOT NULL DEFAULT 0,
    no_response_count   INTEGER NOT NULL DEFAULT 0,
    updated_at          TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, period_type, period_value)
);
"""

SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key             TEXT NOT NULL UNIQUE,
    value           TEXT
);
"""

EXPORTS_TABLE = """
CREATE TABLE IF NOT EXISTS exports (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id        INTEGER NOT NULL,
    export_type     TEXT NOT NULL,               -- txt/csv/xlsx/pdf
    filter_type     TEXT,
    file_path       TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

BACKUPS_TABLE = """
CREATE TABLE IF NOT EXISTS backups (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_type     TEXT NOT NULL,               -- database/media/logs
    file_path       TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'success',
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

MEDIA_FILES_TABLE = """
CREATE TABLE IF NOT EXISTS media_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    file_id         TEXT NOT NULL,
    media_type      TEXT NOT NULL,
    local_path      TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

READ_STATUS_TABLE = """
CREATE TABLE IF NOT EXISTS read_status (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id      INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    is_read         INTEGER NOT NULL DEFAULT 0,
    read_by         INTEGER,
    read_at         TEXT
);
"""

USER_ACTIVITY_TABLE = """
CREATE TABLE IF NOT EXISTS user_activity (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action          TEXT NOT NULL,
    details         TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS notifications (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id            INTEGER,
    user_id             INTEGER REFERENCES users(id) ON DELETE CASCADE,
    notification_type   TEXT NOT NULL,           -- attention/backup/system
    content             TEXT NOT NULL,
    is_sent             INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

LOGS_TABLE = """
CREATE TABLE IF NOT EXISTS logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    level           TEXT NOT NULL,
    module          TEXT,
    message         TEXT NOT NULL,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(report_date);
CREATE INDEX IF NOT EXISTS idx_schedules_user ON schedules(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_user ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_statistics_user ON statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity(user_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
"""

SCHEMA_STATEMENTS: list[str] = [
    USERS_TABLE,
    ADMINS_TABLE,
    MESSAGES_TABLE,
    SCHEDULES_TABLE,
    REMINDERS_TABLE,
    STATISTICS_TABLE,
    SETTINGS_TABLE,
    EXPORTS_TABLE,
    BACKUPS_TABLE,
    MEDIA_FILES_TABLE,
    READ_STATUS_TABLE,
    USER_ACTIVITY_TABLE,
    NOTIFICATIONS_TABLE,
    LOGS_TABLE,
    *[stmt for stmt in INDEXES.strip().split(";") if stmt.strip()],
]
