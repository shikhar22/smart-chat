# Firebase Configuration Setup

This directory contains Firebase service account key files for different companies. Each company should have its own Firebase project and corresponding service account key.

## Setup Instructions

1. **Create Firebase Projects**: Create separate Firebase projects for each company in the Firebase Console.

2. **Generate Service Account Keys**:
   - Go to Firebase Console → Project Settings → Service Accounts
   - Click "Generate new private key"
   - Download the JSON file

3. **Place Configuration Files**: 
   - Rename the downloaded JSON files to match the company name (e.g., `Kalco.json`, `TechCorp.json`)
   - Place them in this `firebase_config/` directory

## File Naming Convention

- File names should match the company names used in the API
- Use the exact case-sensitive company name (e.g., `Kalco.json` not `kalco.json`)
- Files must be in JSON format

## Security Notes

- **Never commit actual service account keys to version control**
- Add `firebase_config/*.json` to your `.gitignore` file (except for example files)
- Store actual keys securely and deploy them through secure channels
- Use environment-specific Firebase projects for development, staging, and production

## Required Firestore Collections

Each Firebase project should have a `leads` collection containing lead documents with the following structure:

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "company": "Example Corp",
  "status": "new",
  "created_at": "2025-01-01T00:00:00Z",
  "source": "website"
}
```

## Testing

You can test the Firebase connection using the `/update-data` endpoint:

```bash
curl -X POST "http://localhost:8008/update-data" \
     -H "Content-Type: application/json" \
     -d '{"company": "Kalco"}'
```

## Example Configuration

The `Kalco.json` file in this directory is an example template. Replace all values with your actual Firebase service account credentials.
