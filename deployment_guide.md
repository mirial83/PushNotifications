# PushNotifications Deployment Guide

This guide will walk you through deploying the PushNotifications application to Vercel with MongoDB as the backend database.

## Prerequisites

- [Node.js](https://nodejs.org/) (v18 or later)
- [Vercel CLI](https://vercel.com/cli) installed globally
- [MongoDB Atlas](https://www.mongodb.com/atlas) account (or self-hosted MongoDB instance)
- [Git](https://git-scm.com/) for version control
- A GitHub, GitLab, or Bitbucket account (for Vercel integration)

## Setup Instructions

### 1. MongoDB Database Setup

#### Option A: MongoDB Atlas (Recommended)

1. **Create MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
   - Sign up for a free account
   - Create a new cluster (M0 Sandbox is free)

2. **Configure Database Access**
   - Go to "Database Access" in the Atlas dashboard
   - Click "Add New Database User"
   - Create a user with "Read and write to any database" permissions
   - Note down the username and password

3. **Configure Network Access**
   - Go to "Network Access" in the Atlas dashboard
   - Click "Add IP Address"
   - Select "Allow access from anywhere" (0.0.0.0/0) for Vercel deployment
   - Or add specific IP addresses if you prefer more security

4. **Get Connection String**
   - Go to "Clusters" and click "Connect"
   - Choose "Connect your application"
   - Copy the connection string (it should look like: `mongodb+srv://username:password@cluster.xxx.mongodb.net/`)

#### Option B: Self-Hosted MongoDB

If you have your own MongoDB instance, ensure it's accessible from the internet and get the connection string.

### 2. Environment Variables Setup

1. **Copy the example environment file:**
   ```bash
   copy .env.example .env.local
   ```

2. **Edit `.env.local` with your settings:**
   ```env
   # MongoDB Configuration
   MONGODB_URI=mongodb+srv://doldarina1:Hill26sand@pushnotifications.tkdvxkd.mongodb.net/?retryWrites=true&w=majority&appName=PushNotifications
   DATABASE_NAME=pushnotifications
   
   # Application Settings
   CLIENT_VERSION=2.1.0
   AUTO_UPDATE_ENABLED=true
   FORCE_UPDATE=true
   
   # Optional: Custom Settings
   REFRESH_INTERVAL=30
   MAX_NOTIFICATIONS=100
   ```

   **Important:** The MongoDB credentials are already configured for your cluster:
   - **Username**: `doldarina1`
   - **Password**: `Hill26sand`
   - **Cluster**: `pushnotifications.tkdvxkd.mongodb.net`
   - **Database**: `pushnotifications`
   
   You may need to update:
   - `CLIENT_VERSION`: Update to match your Python client version

### 3. Local Development Setup

1. **Install Dependencies:**
   ```bash
   npm install
   ```

2. **Test Locally:**
   ```bash
   vercel dev
   ```
   This will start a local development server at `http://localhost:3000`

3. **Verify Database Connection:**
   - Open your browser to `http://localhost:3000`
   - The application should automatically initialize the database
   - Check for any connection errors in the browser console or terminal

### 4. Vercel Deployment

#### Option A: Deploy via Vercel CLI (Recommended)

1. **Login to Vercel:**
   ```bash
   vercel login
   ```

2. **Deploy the Application:**
   ```bash
   vercel
   ```
   - Follow the prompts to configure your project
   - Choose your preferred project name
   - Select the appropriate framework preset (should detect automatically)

3. **Set Environment Variables:**
   ```bash
   vercel env add MONGODB_URI
   vercel env add DATABASE_NAME
   vercel env add CLIENT_VERSION
   vercel env add AUTO_UPDATE_ENABLED
   vercel env add FORCE_UPDATE
   ```
   Enter the values for each when prompted.

4. **Deploy to Production:**
   ```bash
   vercel --prod
   ```

#### Option B: Deploy via Vercel Dashboard

1. **Push Code to Git Repository:**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push origin main
   ```

2. **Import Project in Vercel:**
   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your Git repository
   - Vercel will auto-detect the configuration

3. **Configure Environment Variables:**
   - In the project settings, go to "Environment Variables"
   - Add all the variables from your `.env.local` file
   - Make sure to set them for "Production", "Preview", and "Development" environments

4. **Deploy:**
   - Click "Deploy"
   - Vercel will build and deploy your application

### 5. Post-Deployment Configuration

1. **Verify Deployment:**
   - Visit your Vercel URL (e.g., `https://your-project.vercel.app`)
   - Check that the application loads without errors
   - Test the database initialization

2. **Update Python Client Configuration:**
   - Update any existing Python clients to use the new Vercel URL
   - The client should automatically download from: `https://your-project.vercel.app/api/download`

3. **Test API Endpoints:**
   - Test notification sending
   - Verify client registration works
   - Check file download functionality

### 6. Domain Configuration (Optional)

1. **Custom Domain Setup:**
   - In Vercel dashboard, go to your project settings
   - Click "Domains"
   - Add your custom domain
   - Follow Vercel's instructions to update DNS records

2. **SSL Certificate:**
   - Vercel automatically provides SSL certificates
   - Your application will be available over HTTPS

## Monitoring and Maintenance

### Database Monitoring

1. **MongoDB Atlas Dashboard:**
   - Monitor database usage, connections, and performance
   - Set up alerts for high usage or errors

2. **Database Backup:**
   - MongoDB Atlas provides automatic backups
   - For self-hosted MongoDB, set up regular backup procedures

### Application Monitoring

1. **Vercel Analytics:**
   - Enable Vercel Analytics in your project settings
   - Monitor application performance and usage

2. **Error Monitoring:**
   - Check Vercel function logs for errors
   - Monitor API endpoint response times

### Updates and Maintenance

1. **Code Updates:**
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
   Vercel will automatically redeploy on git push.

2. **Environment Variable Updates:**
   - Update variables in Vercel dashboard
   - Redeploy if necessary

3. **Client Version Updates:**
   - Update `CLIENT_VERSION` environment variable
   - Clients will auto-update on next check
   - **Forced Updates**: With `FORCE_UPDATE=true`, clients MUST update before they can continue using the application
   - **Optional Updates**: With `FORCE_UPDATE=false`, clients can choose to delay updates

## Troubleshooting

### Common Issues

1. **Database Connection Errors:**
   - Verify MongoDB URI is correct
   - Check network access settings in MongoDB Atlas
   - Ensure database user has correct permissions

2. **Environment Variables Not Working:**
   - Verify variables are set in Vercel dashboard
   - Check variable names match exactly
   - Redeploy after adding variables

3. **API Endpoints Not Responding:**
   - Check Vercel function logs
   - Verify API routes are correctly structured
   - Test endpoints locally first

4. **Client Connection Issues:**
   - Verify Vercel URL is accessible
   - Check CORS settings in API routes
   - Test API endpoints with curl or Postman

### Getting Help

1. **Vercel Documentation:**
   - [Vercel Docs](https://vercel.com/docs)
   - [Vercel CLI Reference](https://vercel.com/docs/cli)

2. **MongoDB Documentation:**
   - [MongoDB Atlas Docs](https://docs.atlas.mongodb.com/)
   - [MongoDB Node.js Driver](https://mongodb.github.io/node-mongodb-native/)

3. **Debug Information:**
   - Check browser developer console for frontend errors
   - Check Vercel function logs for backend errors
   - Monitor MongoDB Atlas logs for database issues

## Security Considerations

1. **Environment Variables:**
   - Never commit `.env.local` to version control
   - Use strong passwords for database users
   - Regularly rotate database credentials

2. **Network Security:**
   - Consider restricting MongoDB network access to Vercel IP ranges
   - Use MongoDB Atlas built-in security features
   - Enable MongoDB Atlas encryption at rest

3. **Application Security:**
   - Keep dependencies updated
   - Regularly review and update authorized user list
   - Monitor for unusual API usage patterns

4. **Data Privacy:**
   - Ensure compliance with data protection regulations
   - Implement appropriate data retention policies
   - Consider data encryption for sensitive information

## Cost Considerations

### Vercel Pricing
- **Hobby Plan**: Free for personal projects (limited bandwidth and function executions)
- **Pro Plan**: $20/month per user (higher limits, analytics)
- **Enterprise**: Custom pricing for organizations

### MongoDB Atlas Pricing
- **M0 Sandbox**: Free (512MB storage, shared CPU)
- **M2/M5**: $9-25/month (dedicated clusters)
- **Higher tiers**: Based on compute and storage requirements

### Recommendations
- Start with free tiers for development and small deployments
- Monitor usage and upgrade as needed
- Consider reserved capacity for predictable workloads

---

**Next Steps:**
1. Follow this guide step-by-step
2. Test thoroughly in development before production deployment
3. Set up monitoring and alerting
4. Document any customizations specific to your use case

For additional support or questions, refer to the troubleshooting section above or consult the official documentation for Vercel and MongoDB Atlas.
