# MongoDB Data API Setup Guide

You have these MongoDB Atlas credentials:
- **Public Key**: `xrscwgfy`  
- **Private Key**: `a3c344f0-602c-4653-9ca1-01e9bcf1726a`
- **Project ID**: `68c47cbf735a77007674b50b`
- **Cluster**: `pushnotifications.tkdvxkd.mongodb.net`

## Step 1: Enable MongoDB Data API

1. Go to [https://cloud.mongodb.com](https://cloud.mongodb.com)
2. Make sure you're in your "PushNotifications" project
3. In the left sidebar, look for **"App Services"** and click it
4. If you don't have an app yet:
   - Click **"Create a New App"**
   - Name: `PushNotificationsAPI`
   - Link to Data Source: `pushnotifications` (your cluster)
   - Click **"Create App"**

## Step 2: Enable Data API

1. In your App Services application, look in the left sidebar for **"Data API"**
2. Click **"Data API"**
3. Toggle **"Enable Data API"** to ON
4. **Copy the Data API Base URL** that appears (should look like):
   ```
   https://data.mongodb-api.com/app/YOUR-APP-ID/endpoint/data/v1
   ```

## Step 3: Create API Key

1. In App Services, go to **"Authentication"** → **"API Keys"**
2. Click **"Create API Key"**
3. Name: `WebAPIKey`
4. **Copy the generated API key** (you won't be able to see it again!)

## Step 4: Set Vercel Environment Variables

Go to your Vercel project settings and add:

```
MONGODB_DATA_API_URL=https://data.mongodb-api.com/app/YOUR-ACTUAL-APP-ID/endpoint/data/v1
MONGODB_DATA_API_KEY=your-generated-api-key-here
MONGODB_DATA_SOURCE=pushnotifications
DATABASE_NAME=pushnotifications
```

## Alternative: Quick Test with Admin API

If you can't find the Data API, I can modify the code to use your existing Atlas Admin API credentials instead.

## Test Your Setup

After setting the environment variables:
1. Deploy to Vercel  
2. Test: `https://your-domain.vercel.app/api/index.php?action=testConnection`

The API will automatically use MongoDB when configured, or fall back to simple storage otherwise.
