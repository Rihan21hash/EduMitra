import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("edumitra.migrations")

def run_migrations(engine: Engine):
    """
    Run additive migrations for EduMitra v2 schema changes:
    - Add response_variants table
    - Add conversation_state table
    - Add topic_key, language, subject, topic to quizzes table
    - Add baseline_type to quiz_attempts table
    """
    logger.info("Running schema migrations (v2)...")
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.begin() as conn:
        # 1. response_variants table
        if "response_variants" not in existing_tables:
            logger.info("Creating response_variants table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS response_variants (
                    id VARCHAR(36) PRIMARY KEY,
                    response_id VARCHAR(36) NOT NULL,
                    language VARCHAR(10) NOT NULL,
                    content TEXT NOT NULL,
                    origin VARCHAR(20) DEFAULT 'generated',
                    model VARCHAR(50) DEFAULT 'qwen2.5-coder:7b',
                    created_at DATETIME,
                    FOREIGN KEY(response_id) REFERENCES responses(id) ON DELETE CASCADE,
                    UNIQUE(response_id, language)
                )
            """))

        # 2. conversation_state table
        if "conversation_state" not in existing_tables:
            logger.info("Creating conversation_state table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS conversation_state (
                    id VARCHAR(36) PRIMARY KEY,
                    conversation_id VARCHAR(36) NOT NULL UNIQUE,
                    summary TEXT,
                    subject VARCHAR(50),
                    topic VARCHAR(100),
                    last_response_id VARCHAR(36),
                    answer_language VARCHAR(10),
                    updated_at DATETIME,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """))

        # 3. Alter quizzes table if needed
        if "quizzes" in existing_tables:
            quiz_cols = [c["name"] for c in inspector.get_columns("quizzes")]
            if "topic_key" not in quiz_cols:
                logger.info("Adding topic_key column to quizzes...")
                conn.execute(text("ALTER TABLE quizzes ADD COLUMN topic_key VARCHAR(100)"))
            if "language" not in quiz_cols:
                logger.info("Adding language column to quizzes...")
                conn.execute(text("ALTER TABLE quizzes ADD COLUMN language VARCHAR(10)"))
            if "subject" not in quiz_cols:
                logger.info("Adding subject column to quizzes...")
                conn.execute(text("ALTER TABLE quizzes ADD COLUMN subject VARCHAR(50)"))
            if "topic" not in quiz_cols:
                logger.info("Adding topic column to quizzes...")
                conn.execute(text("ALTER TABLE quizzes ADD COLUMN topic VARCHAR(100)"))

        # 4. Alter quiz_attempts table if needed
        if "quiz_attempts" in existing_tables:
            attempt_cols = [c["name"] for c in inspector.get_columns("quiz_attempts")]
            if "baseline_type" not in attempt_cols:
                logger.info("Adding baseline_type column to quiz_attempts...")
                conn.execute(text("ALTER TABLE quiz_attempts ADD COLUMN baseline_type VARCHAR(30) DEFAULT 'first-attempt'"))

    logger.info("Schema migrations completed successfully.")

if __name__ == "__main__":
    from app.db import engine
    run_migrations(engine)
