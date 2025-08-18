#!/bin/bash

# Database initialization script
# This script will be automatically executed when container starts

# Wait for database service to be ready
echo "Waiting for database service to be ready..."
while true; do
    if python -c "
import psycopg2
try:
    conn = psycopg2.connect(host='db', user='user', password='password', dbname='rewards_db')
    print('Successfully connected to database')
    conn.close()
    exit(0)
except Exception as e:
    print(f'Failed to connect to database: {e}')
    exit(1)
"; then
        break
    fi
    sleep 1
done

echo "Database service is ready, starting initialization..."

# Check if database is already initialized (by checking if db_version table exists)
echo "Checking if database is already initialized..."
TABLE_EXISTS=$(PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'db_version');")

if [[ $TABLE_EXISTS == *"t"* ]]; then
    echo "Database already initialized, skipping base.sql execution"
else
    # Execute database initialization (using merged base.sql script)
    echo "Applying database initialization script base.sql..."
    # Debug info: check if psql command exists
    which psql || echo "psql command not found"
    # Print environment variables
    echo "POSTGRES_USER: ${POSTGRES_USER}"
    echo "POSTGRES_DB: ${POSTGRES_DB}"
    echo "DATABASE_URL: ${DATABASE_URL}"
    # List files in sql directory to confirm base.sql exists
    ls -la sql/
    # Try to execute psql with absolute path and output detailed error info
    echo "Starting to execute base.sql script..."
    PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -v ON_ERROR_STOP=1 -f sql/base.sql 2>&1 || {
        echo "Failed to execute psql with absolute path"
        exit 1
    }

    echo "Database initialization successful"
fi

echo "Database initialization completed"

# Check database version
echo "Querying current database version..."
CURRENT_VERSION=$(PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -t -c "SELECT version FROM db_version ORDER BY applied_at DESC LIMIT 1;")
echo "Current database version: ${CURRENT_VERSION}"

# Format current version number, remove spaces and newlines
CURRENT_VERSION=$(echo "$CURRENT_VERSION" | tr -d ' \n')
# If current version is empty, default to 0.0
if [[ -z "$CURRENT_VERSION" ]]; then
    CURRENT_VERSION="0.0"
fi

echo "Current database version: $CURRENT_VERSION"

# Find all upgrade scripts and sort by version number
UPGRADE_SCRIPTS=($(ls -1 sql/upgrade_db_v*.sql | sort -V))

# Iterate through all upgrade scripts
for SCRIPT in "${UPGRADE_SCRIPTS[@]}"; do
    # Extract script version number
    SCRIPT_VERSION=$(echo "$SCRIPT" | sed -n 's/.*_v\([0-9]\.[0-9]\).*/\1/p')
    
    # Compare version numbers
    if [[ "$SCRIPT_VERSION" > "$CURRENT_VERSION" ]]; then
        echo "Found upgrade script to apply: $SCRIPT (version: $SCRIPT_VERSION)"
        
        # Execute upgrade script
        echo "Applying upgrade script: $SCRIPT..."
        if PGPASSWORD=${POSTGRES_PASSWORD} /usr/bin/psql -h db -U ${POSTGRES_USER} -d ${POSTGRES_DB} -v ON_ERROR_STOP=1 -f "$SCRIPT"; then
            echo "Upgrade script $SCRIPT applied successfully"
            # Update current version
            CURRENT_VERSION="$SCRIPT_VERSION"
        else
            echo "Failed to apply upgrade script $SCRIPT, terminating upgrade process"
            exit 1
        fi
    fi
done

if [[ "$CURRENT_VERSION" != "$(echo "${UPGRADE_SCRIPTS[-1]}" | sed -n 's/.*_v\([0-9]\.[0-9]\).*/\1/p')" ]] && [[ "${#UPGRADE_SCRIPTS[@]}" -gt 0 ]]; then
    echo "Database upgraded to latest version: $CURRENT_VERSION"
fi

# Start Flask application
echo "Initialization completed, starting Flask application..."
flask run --host=0.0.0.0 --port=5000
