"""PostgreSQL trigger management for real-time notifications."""
import asyncpg
from .config import POSTGRESQL_URL

async def setup_model_trigger(model_class):
    """
    Create a PostgreSQL trigger for any SQLAlchemy model class.
    The trigger will notify on INSERT/UPDATE operations with all columns from the model.
    
    Args:
        model_class: SQLAlchemy model class that inherits from Base
    """
    if not hasattr(model_class, '__table__'):
        raise ValueError("Input must be a SQLAlchemy model class")

    table_name = model_class.__tablename__
    channel_name = f"{table_name}_changes"
    trigger_name = f"{table_name}_notify_trigger"
    function_name = f"notify_{table_name}_change"
    
    # Get all column names from the model
    columns = [column.name for column in model_class.__table__.columns]
    json_fields = ',\n                        '.join([f"'{col}', NEW.{col}" for col in columns])
    
    conn = await asyncpg.connect(POSTGRESQL_URL)
    try:
        # Create the trigger function
        await conn.execute(f"""
            CREATE OR REPLACE FUNCTION {function_name}()
            RETURNS trigger AS $$
            BEGIN
                PERFORM pg_notify(
                    '{channel_name}',
                    json_build_object(
                        'operation', TG_OP,
                        {json_fields}
                    )::text
                );
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
        """)

        # Create the trigger
        await conn.execute(f"""
            DROP TRIGGER IF EXISTS {trigger_name} ON {table_name};
            CREATE TRIGGER {trigger_name}
                AFTER INSERT OR UPDATE ON {table_name}
                FOR EACH ROW
                EXECUTE FUNCTION {function_name}();
        """)
    finally:
        await conn.close()
