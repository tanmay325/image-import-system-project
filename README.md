# Image Import System 

Live site (frontend): https://image-import-system-project.vercel.app/

Import images from a public Google Drive folder, upload them to AWS S3, and store image metadata in a relational database (AWS RDS MySQL supported). A React UI lets you trigger imports and browse the gallery.

## Repository contents (what’s included)

- Source code for all backend services and the frontend (see folders under `services/`, plus `frontend/`).
- Dockerfiles for each service:
  - `services/api-gateway/Dockerfile`
  - `services/import-service/Dockerfile`
  - `services/worker-service/Dockerfile`
  - `services/metadata-service/Dockerfile`
  - `services/storage-service/Dockerfile`
  - `frontend/Dockerfile`

## Architecture and service breakdown

### Services

- **API Gateway** (`services/api-gateway`)
  - Single public REST entrypoint: exposes `/api/*` and proxies to internal services.
  - Handles CORS via `CORS_ORIGINS`.

- **Import Service** (`services/import-service`)
  - Validates a Google Drive folder URL, lists images via Google Drive API.
  - Creates a `job_id` and splits the work into batches sent to the worker.
  - Tracks job status in-memory for `/import/status/{job_id}`.

- **Worker Service** (`services/worker-service`)
  - Downloads each image from Google Drive.
  - Uploads it via the Storage Service.
  - Writes metadata via the Metadata Service.
  - Updates the Import Service with progress (`/import/update-status`).

- **Storage Service** (`services/storage-service`)
  - Upload abstraction for cloud storage (AWS S3 in this project).
  - Returns a public URL for the uploaded object.

- **Metadata Service** (`services/metadata-service`)
  - Stores and serves image metadata.
  - Supports MySQL (RDS) and falls back to SQLite for local/dev if DB env vars aren’t provided.

### High-level flow

```
React UI
   |
   v
API Gateway (/api/*)
   |
   +--> Import Service: lists Drive images, creates job_id
            |
            +--> Worker Service: downloads + uploads + persists metadata
                     |        |
                     |        +--> Storage Service (S3)
                     |
                     +--> Metadata Service (DB)
```

## Setup

### Prerequisites

- Docker (recommended for running all microservices)
- Node.js 18+ (only needed if you run the frontend in dev mode outside Docker)
- AWS S3 bucket + credentials configured in the environment where the containers run
- A public Google Drive folder (shared as “Anyone with the link”)

### 1) Create `.env` in the repo root

Create a file named `.env` in the repo root (this folder):

```env
# Google Drive
GOOGLE_API_KEY=your-google-drive-api-key

# Storage
STORAGE_PROVIDER=aws
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-s3-bucket

# Database (MySQL / RDS)
DB_ENGINE=mysql
DB_SERVER=your-mysql-host
DB_PORT=3306
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password

# Gateway CORS (comma-separated). Use your local + Vercel URLs.
CORS_ORIGINS=https://image-import-system-project.vercel.app

# Optional overrides (defaults shown)
IMPORT_SERVICE_URL=http://import-service:5001
METADATA_SERVICE_URL=http://metadata-service:5002
STORAGE_SERVICE_URL=http://storage-service:5003
WORKER_SERVICE_URL=http://worker-service:5004
REDIS_URL=redis://redis:6379/0
```

### 2) Start all backend services 

From the repo root:

```bash
docker compose -f docker-compose.microservices.yml up --build
```

Health check (gateway):

- `GET http://localhost:8080/health`

API base (gateway):

- `http://localhost:8080/api`

### 3) Start the frontend (local dev)

From the repo root:

```bash
cd frontend
npm install
```

Set the API URL and run the dev server.

PowerShell:

```powershell
$env:REACT_APP_API_URL="http://localhost:8080/api"
npm start
```

Frontend dev URL:

- `http://localhost:3000`

## Cloud setup

### Frontend (Vercel)

- Deploy the `frontend/` project to Vercel.
- Set environment variable:
  - `REACT_APP_API_URL` = `https://metaltroop.cv/api`
- Ensure the gateway allows your Vercel origin via `CORS_ORIGINS`.

Live site : https://image-import-system-project.vercel.app/

### Backend

Common deployment approach:

1. Copy the repo (or build/push images) to the host.
2. Provide `.env` on the host.
3. Run `docker compose -f docker-compose.microservices.yml up --build -d`.
4. Put a reverse proxy / load balancer in front of the API Gateway.

## API documentation

Base URL (local): `http://localhost:8080/api`

All endpoints return JSON. Error responses typically use:

```json
{ "error": "message" }
```

### Health

`GET /health` (gateway, not under `/api`)

Response (200):

```json
{ "status": "healthy", "service": "api-gateway" }
```

### Start an import (Google Drive)

`POST /import/google-drive`

Request:

```json
{ "folder_url": "https://drive.google.com/drive/folders/FOLDER_ID" }
```

### List images (paginated)

`GET /images?page=1&per_page=50`


### List all images

`GET /images/all`


### Get a single image

`GET /images/{image_id}`


### Stats

`GET /stats`


## Scalability notes

- **Batching:** the Import Service splits large folders into batches (default 100 items) and dispatches them to the Worker Service.
- **Concurrency:** the Worker Service processes images concurrently using a thread pool; you can scale further by running multiple worker containers.
- **Recommended upgrades for very large imports:**
  - Persist job state in Redis/DB (current job status is in-memory).
  - Use a real queue with retry/backoff (Redis is already provisioned) instead of HTTP fan-out.
  - Stream uploads instead of base64 payloads to reduce memory and network overhead.
  - Implement Google Drive pagination and rate-limit/backoff handling for extremely large folders.

## Notes

- Google Drive folder must be shared as “Anyone with the link” (Viewer).
- Ensure your S3 bucket policy/IAM allows uploads and that uploaded objects are accessible as intended.