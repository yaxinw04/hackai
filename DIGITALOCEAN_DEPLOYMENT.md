# 🌊 DigitalOcean App Platform Deployment (Fixed)

The error you encountered is because DigitalOcean App Platform was trying to run the local development script instead of the production configuration. Here's the correct way to deploy:

## 🚨 Quick Fix

The issue was that DigitalOcean detected the root `package.json` and tried to run `npm start` which calls `./start.sh` - a local development script that doesn't work in production containers.

## 🎯 **Option 1: Simple Manual Setup (Recommended)**

### Step 1: Deploy Backend Service

1. **Go to DigitalOcean Apps**: https://cloud.digitalocean.com/apps
2. **Create New App** → **Connect GitHub**
3. **Configure Backend Service:**
   ```
   Service Name: backend
   Source Directory: /backend
   Environment: Python
   Build Command: pip install -e .
   Run Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
   HTTP Port: 8000
   Instance Size: Basic ($5/month)
   ```

4. **Add Environment Variables** (in the DigitalOcean dashboard):
   ```bash
   ENV=production
   DEBUG=false
   USE_S3=true
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   AWS_REGION=us-east-1
   S3_BUCKET=your-bucket-name
   SECRET_KEY=your-secret-key-32-chars
   OPENAI_API_KEY=sk-your-openai-key
   USE_SYSTEM_FFMPEG=1
   ```

### Step 2: Deploy Frontend Service

1. **Add Another Service** to the same app
2. **Configure Frontend Service:**
   ```
   Service Name: frontend
   Source Directory: /frontend  
   Environment: Node.js
   Build Command: npm ci && npm run build
   Run Command: npm start
   HTTP Port: 3000
   Instance Size: Basic ($5/month)
   ```

3. **Add Environment Variable:**
   ```bash
   NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.ondigitalocean.app
   ```

### Step 3: Configure Routes

1. **Frontend Routes:**
   ```
   Path: /
   ```

2. **Backend Routes:**
   ```
   Path: /api
   Rewrite: /
   ```

## 🎯 **Option 2: Using App Spec (Advanced)**

If you prefer configuration-as-code, use the `.do/app.yaml` file I created:

1. **Push to GitHub:**
   ```bash
   git add .do/app.yaml
   git commit -m "Add DigitalOcean app spec"
   git push
   ```

2. **Create App with Spec:**
   - DigitalOcean Apps → Create App
   - Choose "App Spec" option
   - Upload the `.do/app.yaml` file
   - Add your secret environment variables through the dashboard

## 🎯 **Option 3: Docker Deployment (Most Reliable)**

If the buildpack approach keeps failing, use Docker:

1. **Create DigitalOcean Droplet** (Virtual Server):
   ```bash
   # Create $20/month droplet with Docker pre-installed
   # SSH into the droplet
   ```

2. **Deploy with Docker Compose:**
   ```bash
   git clone your-repo
   cd your-repo
   cp env.example .env
   nano .env  # Add your AWS credentials
   docker-compose up -d
   ```

3. **Configure Domain:**
   ```bash
   # Point your domain to the droplet's IP
   # Configure SSL with Let's Encrypt
   sudo certbot --nginx -d yourapp.com
   ```

## 🔧 **Fixing Your Current Deployment**

If you want to fix your current failing deployment:

### Quick Fix:
1. **Go to your app settings** in DigitalOcean
2. **Change the Run Command** from `npm start` to:
   - **Backend**: `./backend/start-production.sh` 
   - **Frontend**: `cd frontend && npm start`

### Or Redeploy:
1. **Delete the current app**
2. **Follow Option 1 above** (deploy backend and frontend as separate services)

## 📋 **Environment Variables You Need**

For DigitalOcean App Platform, add these in the dashboard:

### Backend Service:
```bash
# Required
ENV=production
USE_S3=true
AWS_ACCESS_KEY_ID=AKIA... (from AWS)
AWS_SECRET_ACCESS_KEY=wJalr... (from AWS)
S3_BUCKET=your-bucket-name
SECRET_KEY=generate-random-32-chars

# Optional
OPENAI_API_KEY=sk-your-key
AWS_REGION=us-east-1
RATE_LIMIT_ENABLED=true
```

### Frontend Service:
```bash
NEXT_PUBLIC_API_BASE_URL=https://your-backend-url.ondigitalocean.app
```

## 🎯 **Why This Happens**

- DigitalOcean App Platform auto-detects the root `package.json`
- It tries to run `npm start` which calls `./start.sh`
- `start.sh` is for local development and tries to install system packages
- Container environments don't allow `apt install` commands
- The solution is to deploy backend/frontend separately or use proper production scripts

## ✅ **Success Checklist**

- [ ] Backend service deploys successfully
- [ ] Frontend service deploys successfully  
- [ ] Environment variables are set
- [ ] Health checks pass
- [ ] Frontend can connect to backend API
- [ ] S3 bucket is accessible

## 🆘 **If You Still Have Issues**

1. **Check the build logs** in DigitalOcean dashboard
2. **Verify AWS S3 credentials** are correct
3. **Make sure S3 bucket exists** and has proper permissions
4. **Use the runtime logs** to debug connection issues
5. **Try Option 3 (Docker)** if buildpacks keep failing

The Docker approach (Option 3) is most reliable and gives you full control!

## 💰 **Cost for DigitalOcean**

- **App Platform**: $5/month per service (backend + frontend = $10/month)
- **Droplet + Docker**: $20/month for both services combined + more control
- **Plus**: S3 storage costs (~$3/month for moderate usage)

**Recommended**: Start with Option 1 (App Platform) for simplicity, upgrade to Docker droplet if you need more control. 