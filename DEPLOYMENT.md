# 🚀 Production Deployment Guide

This guide will walk you through deploying the YouTube Shorts AI service to production. You'll need to set up cloud infrastructure, configure storage, and deploy the application.

## 📋 Prerequisites

Before starting, make sure you have:
- ✅ AWS account (for S3 storage and optional EC2/ECS deployment)
- ✅ Domain name registered (e.g., `yourapp.com`)
- ✅ Docker installed on your deployment machine
- ✅ Basic knowledge of cloud services

## 🏗️ Infrastructure Setup

### Step 1: AWS S3 Bucket Setup

**Why S3?** For production, you need cloud storage for processed videos since local storage doesn't scale across multiple servers.

1. **Create S3 Bucket:**
   ```bash
   # Log into AWS Console -> S3 -> Create Bucket
   # Bucket name: your-youtube-shorts-videos
   # Region: us-east-1 (or your preferred region)
   # Keep all default settings
   ```

2. **Configure Bucket Policy:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Sid": "PublicReadGetObject",
         "Effect": "Allow",
         "Principal": "*",
         "Action": "s3:GetObject",
         "Resource": "arn:aws:s3:::your-youtube-shorts-videos/*"
       }
     ]
   }
   ```

3. **Enable CORS:**
   ```json
   [
     {
       "AllowedHeaders": ["*"],
       "AllowedMethods": ["GET", "HEAD"],
       "AllowedOrigins": ["https://yourapp.com", "https://www.yourapp.com"],
       "ExposeHeaders": []
     }
   ]
   ```

### Step 2: AWS IAM User & Credentials

1. **Create IAM User:**
   - Go to AWS Console → IAM → Users → Create User
   - User name: `youtube-shorts-app`
   - Access type: Programmatic access

2. **Attach Policy:**
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:GetObject",
           "s3:PutObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::your-youtube-shorts-videos",
           "arn:aws:s3:::your-youtube-shorts-videos/*"
         ]
       }
     ]
   }
   ```

3. **Save Credentials:**
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJalr...`

### Step 3: Configure Bucket Permissions

Since modern S3 buckets have ACLs disabled for security, you need to set up a bucket policy for public access:

1. Go to your bucket → **Permissions** tab
2. Scroll down to **Bucket policy**
3. Add this policy (replace `your-bucket-name` with your actual bucket name):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

**Important Security Notes:**
- This policy makes ALL files in your bucket publicly readable
- Only put video clips and public assets in this bucket
- Never store sensitive data, API keys, or personal information in this bucket
- Consider using CloudFront (CDN) for better security and performance

### Alternative: CloudFront Distribution (Recommended)

For better security and performance, use CloudFront instead of direct S3 public access:

1. Create a CloudFront distribution pointing to your S3 bucket
2. Keep your bucket private (no bucket policy needed)
3. Configure Origin Access Control (OAC) in CloudFront
4. Update your `S3_BUCKET_URL` environment variable to use the CloudFront URL

```bash
S3_BUCKET_URL=https://your-distribution-id.cloudfront.net
```

## 🖥️ Server Deployment Options

Choose one of these deployment methods:

### Option A: Docker Compose (Easiest)

**Best for:** Small to medium applications, single server deployment

1. **Prepare Your Server:**
   ```bash
   # On Ubuntu/Debian
   sudo apt update && sudo apt install docker.io docker-compose git
   
   # On CentOS/RHEL
   sudo yum install docker docker-compose git
   
   # Start Docker
   sudo systemctl start docker
   sudo systemctl enable docker
   ```

2. **Clone and Configure:**
   ```bash
   # Clone your repository
   git clone https://github.com/yourusername/youtube-shorts-ai.git
   cd youtube-shorts-ai
   
   # Copy environment template
   cp env.example .env
   
   # Edit environment variables (see configuration section below)
   nano .env
   ```

3. **Deploy:**
   ```bash
   # Build and start services
   docker-compose up -d
   
   # Check status
   docker-compose ps
   docker-compose logs -f
   ```

### Option B: AWS ECS (Recommended for Scale)

**Best for:** Production applications needing auto-scaling

1. **Create ECS Cluster:**
   ```bash
   # Install AWS CLI
   pip install awscli
   aws configure
   
   # Create cluster
   aws ecs create-cluster --cluster-name youtube-shorts-cluster
   ```

2. **Create Task Definitions:**
   ```bash
   # Register backend task
   aws ecs register-task-definition --cli-input-json file://ecs-backend-task.json
   
   # Register frontend task  
   aws ecs register-task-definition --cli-input-json file://ecs-frontend-task.json
   ```

3. **Deploy Services:**
   ```bash
   # Create backend service
   aws ecs create-service \
     --cluster youtube-shorts-cluster \
     --service-name backend \
     --task-definition youtube-shorts-backend:1 \
     --desired-count 2
   
   # Create frontend service
   aws ecs create-service \
     --cluster youtube-shorts-cluster \
     --service-name frontend \
     --task-definition youtube-shorts-frontend:1 \
     --desired-count 2
   ```

### Option C: DigitalOcean App Platform (Simplest)

**Best for:** Quick deployment without infrastructure management

1. **Connect Repository:**
   - Go to DigitalOcean → Apps → Create App
   - Connect your GitHub repository

2. **Configure Services:**
   ```yaml
   # Backend Service
   name: backend
   source_dir: /backend
   dockerfile_path: backend/Dockerfile
   http_port: 8000
   instance_count: 1
   instance_size_slug: basic-xxs
   
   # Frontend Service
   name: frontend
   source_dir: /frontend
   dockerfile_path: frontend/Dockerfile
   http_port: 3000
   instance_count: 1
   instance_size_slug: basic-xxs
   ```

## ⚙️ Environment Configuration

Edit your `.env` file with these values:

```bash
# Copy the template and edit
cp env.example .env
nano .env
```

**Required Configuration:**
```bash
# Basic settings
ENV=production
DEBUG=false
CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com
NEXT_PUBLIC_API_BASE_URL=https://api.yourapp.com

# S3 Storage (REQUIRED)
USE_S3=true
AWS_ACCESS_KEY_ID=AKIA... # From Step 2
AWS_SECRET_ACCESS_KEY=wJalr... # From Step 2
AWS_REGION=us-east-1
S3_BUCKET=your-youtube-shorts-videos

# Optional: CloudFront CDN
S3_BUCKET_URL=https://d111111abcdef8.cloudfront.net

# Security (CHANGE THIS!)
SECRET_KEY=generate-a-random-32-character-string-here

# Optional: OpenAI for AI features
OPENAI_API_KEY=sk-your-openai-key-here
```

## 🌐 Domain & SSL Setup

### Step 1: Domain Configuration

1. **Point Domain to Your Server:**
   ```bash
   # A Records (replace with your server IP)
   yourapp.com      → 1.2.3.4
   www.yourapp.com  → 1.2.3.4
   api.yourapp.com  → 1.2.3.4
   ```

2. **For CloudFlare (Recommended):**
   - Add your domain to CloudFlare
   - Use CloudFlare nameservers
   - Enable "Proxied" for all records
   - SSL/TLS → Full (Strict)

### Step 2: SSL Certificate

**Option A: Let's Encrypt (Free):**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourapp.com -d www.yourapp.com -d api.yourapp.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

**Option B: CloudFlare SSL (Automatic)**
- Enable CloudFlare proxy
- SSL/TLS → Full (Strict)
- Automatic certificate

### Step 3: Nginx Configuration

Create `/etc/nginx/sites-available/youtube-shorts`:
```nginx
# Frontend
server {
    listen 80;
    listen 443 ssl;
    server_name yourapp.com www.yourapp.com;
    
    ssl_certificate /etc/letsencrypt/live/yourapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourapp.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Backend API
server {
    listen 80;
    listen 443 ssl;
    server_name api.yourapp.com;
    
    ssl_certificate /etc/letsencrypt/live/yourapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourapp.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/youtube-shorts /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔐 Security Hardening

### 1. Firewall Setup
```bash
# UFW (Ubuntu/Debian)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Fail2ban (brute force protection)
sudo apt install fail2ban
```

### 2. Environment Security
```bash
# Secure environment file
chmod 600 .env
chown root:root .env

# Remove sensitive files from git
echo ".env" >> .gitignore
echo "*.key" >> .gitignore
echo "*.pem" >> .gitignore
```

### 3. Docker Security
```bash
# Run containers as non-root (already configured in Dockerfiles)
# Limit container resources
docker-compose.yml:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '0.5'
```

## 📊 Monitoring & Maintenance

### 1. Health Checks
```bash
# Check service health
curl https://api.yourapp.com/health
curl https://yourapp.com

# Monitor logs
docker-compose logs -f backend
docker-compose logs -f frontend

# System monitoring
htop
df -h
```

### 2. Backup Strategy
```bash
# S3 videos are automatically backed up by AWS
# Backup job data (JSON files)
tar -czf backup-$(date +%Y%m%d).tar.gz data/jobs/
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

### 3. Updates
```bash
# Update application
git pull origin main
docker-compose build
docker-compose up -d

# Update dependencies
docker-compose pull
docker-compose up -d
```

## 🚨 Troubleshooting

### Common Issues:

**1. Videos not uploading to S3:**
```bash
# Check AWS credentials
aws s3 ls s3://your-youtube-shorts-videos

# Check container logs
docker-compose logs backend | grep S3
```

**2. CORS errors:**
```bash
# Update CORS_ORIGINS in .env
CORS_ORIGINS=https://yourapp.com,https://www.yourapp.com

# Restart backend
docker-compose restart backend
```

**3. Out of disk space:**
```bash
# Check disk usage
df -h

# Clean up old containers
docker system prune -a

# Clear temporary files
rm -rf data/temp/*
```

**4. High memory usage:**
```bash
# Limit video processing
MAX_VIDEO_DURATION=1800  # 30 minutes
MAX_CLIP_COUNT=10

# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 💰 Cost Estimation

**Monthly costs for medium usage (1000 videos/month):**

| Service | Cost |
|---------|------|
| AWS S3 Storage (100GB) | $2.30 |
| AWS S3 Requests | $1.00 |
| CloudFront CDN | $5.00 |
| DigitalOcean Droplet (4GB) | $24.00 |
| Domain (.com) | $1.00 |
| **Total** | **~$33/month** |

**For higher scale:**
- AWS ECS: $50-200/month
- Load Balancer: $20/month  
- RDS Database: $15-50/month

## 📈 Scaling Tips

1. **Enable S3 Transfer Acceleration** for faster uploads
2. **Use CloudFront** for global video delivery
3. **Add Redis** for session management
4. **Use RDS/PostgreSQL** instead of JSON files
5. **Implement auto-scaling** with ECS or Kubernetes
6. **Add CDN** for static assets

## ✅ Deployment Checklist

- [ ] AWS S3 bucket created and configured
- [ ] IAM user created with S3 permissions
- [ ] Environment variables configured
- [ ] Domain pointed to server
- [ ] SSL certificate installed
- [ ] Application deployed and running
- [ ] Health checks passing
- [ ] CORS configured correctly
- [ ] Firewall configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented

## 🆘 Support

If you encounter issues:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables
3. Test health endpoints
4. Check AWS S3 permissions
5. Verify domain DNS settings

---

**🎉 Congratulations!** Your YouTube Shorts AI service is now live in production!

Access your app at: `https://yourapp.com` 