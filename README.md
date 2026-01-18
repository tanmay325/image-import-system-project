# Image Import System (Microservices)

Import images from a **public Google Drive folder**, upload them to **AWS S3**, and store image metadata in **RDS MySQL**. A small **React** UI lets you trigger imports and view the gallery.

## What’s inside

- **api-gateway**: Public REST API (`/api/*`)
- **import-service**: Reads Google Drive folder and creates an import job
- **worker-service**: Downloads images, uploads to S3, saves metadata
- **metadata-service**: Metadata database API
- **redis**: Queue/broker used by import flow

## Quick start

### 1) Create `.env` in the repo root

Create a file named `.env` in `image-import-system/`:

```env
# Google Drive
GOOGLE_API_KEY=your-google-drive-api-key

# Storage
STORAGE_PROVIDER=aws
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-s3-bucket

# Database 
DB_ENGINE=mysql
DB_SERVER=your-mysql-host
DB_PORT=3306
DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password

# CORS for the gateway
CORS_ORIGINS=http://vercel.app
```

### 2) Start the backend (all services)

```bash
docker compose -f docker-compose.microservices.yml up --build
```

Health check:

- `GET http://localhost:8080/health`

### 3) Start the frontend (dev)

```bash
cd frontend
npm install
# Sets Environment also on vercel
set REACT_APP_API_URL=url used in vercel of ssl cert
npm start
```

Frontend runs at vercel.

## API (via gateway)

Base URL: `http://metaltroop.cv/api`

### Start import

`POST /import/google-drive`

```json
{
  "folder_url": "https://drive.google.com/drive/folders/FOLDER_ID"
}
```

### List all images

`GET /images/all`

### Stats

`GET /stats`

## How it works (high level)

```
React UI
   |
   v
API Gateway  --->  Import Service  --->  Worker Service
                                  |           |
                                  |           +--> Storage Service (S3)
                                  |           +--> Metadata Service (DB)
                                  +--> Redis
```

## Notes

- Google Drive folder must be shared as “Anyone with the link” (Viewer).
- S3 bucket allow uploads and objects are uploaded with `public-read`.