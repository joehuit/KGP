# KGP LIST — Database Setup & Management

## Local Development Database

KGP LIST uses **PostgreSQL 16** as its primary relational database.

### 1. Starting PostgreSQL via Docker

If Docker Desktop is installed on your Windows machine:

```powershell
# Navigate to database directory
cd database

# Start PostgreSQL with persistent storage in background
docker compose up -d

# Check container health status
docker compose ps
```

The database will be reachable at:
- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `kgp_db`
- **Username:** `kgp_user`
- **Password:** `kgp_secret_password_change_me` (or as set in `.env`)

### 2. Native Windows PostgreSQL Installation (Alternative to Docker)

If Docker is not installed on your system, install PostgreSQL directly:
1. Download PostgreSQL 16 for Windows from [postgresql.org](https://www.postgresql.org/download/windows/).
2. Run installer and note your `postgres` superuser password and port `5432`.
3. Open `psql` or pgAdmin 4:
   ```sql
   CREATE USER kgp_user WITH PASSWORD 'kgp_secret_password_change_me';
   CREATE DATABASE kgp_db OWNER kgp_user;
   GRANT ALL PRIVILEGES ON DATABASE kgp_db TO kgp_user;
   ```
4. Verify your `backend/.env` file matches these credentials.

### 3. Applying Alembic Migrations

Once PostgreSQL is running, apply all database migrations from the `backend/` directory:

```powershell
cd ../backend

# Apply all migrations up to head
alembic upgrade head
```

To rollback a migration:
```powershell
alembic downgrade -1
```

To view current migration revision:
```powershell
alembic current
```

### 4. Database Persistence

Data is stored persistently:
- In Docker: In the Docker volume `kgp_postgres_dev_data`.
- In Native Windows: In PostgreSQL's default `data` directory.

To reset the database completely in Docker development:
```powershell
docker compose down -v
docker compose up -d
alembic upgrade head
```
