# AWS EC2 Deployment Guide - IRA Workflow Builder

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [EC2 Instance Setup](#ec2-instance-setup)
4. [Initial Server Configuration](#initial-server-configuration)
5. [Application Deployment](#application-deployment)
6. [Configuration](#configuration)
7. [Accessing Your Application](#accessing-your-application)
8. [Managing the Application](#managing-the-application)
9. [Troubleshooting](#troubleshooting)
10. [Production Best Practices](#production-best-practices)

---

## Overview

This guide walks you through deploying the IRA Workflow Builder application on an AWS EC2 Ubuntu instance. The application will be accessible via the EC2 instance's public IP address.

**Architecture**:
- **Backend**: FastAPI (Python 3.11) running on port 8000
- **Frontend**: Next.js (Node.js 20) running on port 3000
- **Process Management**: PM2 for both backend and frontend
- **Communication**: Frontend auto-detects backend via hostname

---

## Prerequisites

### AWS Requirements
- AWS account with EC2 access
- SSH key pair (.pem file) for EC2 access
- Basic familiarity with AWS Console and SSH

### EC2 Instance Requirements
- **OS**: Ubuntu 20.04 LTS or later (Ubuntu 22.04 recommended)
- **Instance Type**: Minimum t3.medium (2 vCPUs, 4GB RAM)
  - Recommended: t3.large (2 vCPUs, 8GB RAM) for better performance
- **Storage**: Minimum 20GB EBS volume (30GB recommended)
- **Security Group**: Must allow the following inbound traffic:
  - Port 22 (SSH) - Your IP only
  - Port 3000 (Frontend) - 0.0.0.0/0 or your IP range
  - Port 8000 (Backend API) - 0.0.0.0/0 or your IP range

### API Keys Required
- **OpenAI API Key** (required): Get from https://platform.openai.com/api-keys
- **Groq API Key** (recommended for hybrid mode): Get from https://console.groq.com/keys

---

## EC2 Instance Setup

### Step 1: Launch EC2 Instance

1. **Go to AWS EC2 Console**
   - Navigate to EC2 → Instances → Launch Instance

2. **Configure Instance**:
   ```
   Name: ira-workflow-builder
   AMI: Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
   Instance type: t3.medium (or t3.large)
   Key pair: Select or create a new key pair (download .pem file)
   ```

3. **Configure Network Settings**:
   - Create or select a security group
   - Add the following inbound rules:

   | Type | Protocol | Port Range | Source | Description |
   |------|----------|------------|--------|-------------|
   | SSH | TCP | 22 | My IP | SSH access |
   | Custom TCP | TCP | 3000 | 0.0.0.0/0 | Frontend |
   | Custom TCP | TCP | 8000 | 0.0.0.0/0 | Backend API |

4. **Configure Storage**:
   - Root volume: 30 GB gp3 (recommended)

5. **Launch Instance**
   - Click "Launch Instance"
   - Wait for instance state to be "Running"
   - Note the **Public IPv4 address** (e.g., 54.123.45.67)

### Step 2: Connect to Your EC2 Instance

1. **Set permissions on your key file** (first time only):
   ```bash
   chmod 400 /path/to/your-key.pem
   ```

2. **SSH into your instance**:
   ```bash
   ssh -i /path/to/your-key.pem ubuntu@<EC2_PUBLIC_IP>
   ```

   Example:
   ```bash
   ssh -i ~/.ssh/ira-key.pem ubuntu@54.123.45.67
   ```

---

## Initial Server Configuration

### Option 1: Automated Setup (Recommended)

If you're deploying from your local machine, the script will automatically upload files and run setup:

```bash
# On your local machine, from the project root directory:
chmod +x deploy_ec2.sh
./deploy_ec2.sh <EC2_PUBLIC_IP> /path/to/your-key.pem ubuntu
```

Example:
```bash
./deploy_ec2.sh 54.123.45.67 ~/.ssh/ira-key.pem ubuntu
```

This will:
1. Upload all application files (excluding node_modules, venv, .git)
2. Connect to EC2 and run the setup automatically
3. Install all dependencies
4. Start the application

**Skip to [Accessing Your Application](#accessing-your-application) section if using automated setup.**

---

### Option 2: Manual Setup

If you prefer manual control or automated setup fails:

#### Step 1: Upload Application Files

From your local machine:

```bash
# Upload files using rsync
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '.git' --exclude '__pycache__' \
  -e "ssh -i /path/to/your-key.pem" \
  . ubuntu@<EC2_PUBLIC_IP>:~/ira_workflow_builder/
```

Or using SCP:
```bash
scp -i /path/to/your-key.pem -r /path/to/project ubuntu@<EC2_PUBLIC_IP>:~/ira_workflow_builder/
```

#### Step 2: Run System Setup on EC2

SSH into your EC2 instance:
```bash
ssh -i /path/to/your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

Upload and run the setup script:
```bash
cd ~/ira_workflow_builder
chmod +x deploy_ec2.sh
./deploy_ec2.sh setup
```

This will install:
- Python 3.11
- Node.js 20.x
- PM2 (process manager)
- Git, curl, wget, build-essential

**Installation time**: Approximately 10-15 minutes

---

## Application Deployment

### Step 1: Configure Environment Variables

On your EC2 instance, create the `.env` file from the production template:

```bash
cd ~/ira_workflow_builder
cp .env.production .env
nano .env
```

**Required Changes**:

1. **Add your OpenAI API Key**:
   ```bash
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   ```

2. **Add your Groq API Key** (if using hybrid mode):
   ```bash
   GROQ_API_KEY=gsk-your-actual-groq-key-here
   ```

3. **Configure CORS** (choose one option):

   **Option A - For Testing (Allow All)**:
   ```bash
   CORS_ORIGINS=["*"]
   ```

   **Option B - For Production (Specific IP - RECOMMENDED)**:
   ```bash
   CORS_ORIGINS=["http://54.123.45.67:3000", "http://54.123.45.67:8000"]
   ```
   Replace `54.123.45.67` with your actual EC2 public IP.

   **Option C - For Custom Domain**:
   ```bash
   CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
   ```

4. **Change Admin Password**:
   ```bash
   ADMIN_PASSWORD=your-secure-password-here
   ```

5. **Generate Secret Key** (run this command):
   ```bash
   openssl rand -hex 32
   ```
   Copy the output and update:
   ```bash
   SECRET_KEY=<paste-generated-key-here>
   ```

Save and exit (Ctrl+X, then Y, then Enter).

### Step 2: Configure Frontend Environment (Optional)

By default, the frontend auto-detects the hostname. If you want to specify explicit API URL:

```bash
cd ~/ira_workflow_builder/frontend
nano .env.production
```

Uncomment and set:
```bash
NEXT_PUBLIC_API_URL=http://<EC2_PUBLIC_IP>:8000
```

### Step 3: Start the Application

```bash
cd ~/ira_workflow_builder
./deploy_ec2.sh start
```

This will:
1. Create Python virtual environment
2. Install Python dependencies (~5-10 minutes)
3. Install frontend dependencies (~5-10 minutes)
4. Build frontend for production (~2-5 minutes)
5. Start backend with PM2
6. Start frontend with PM2
7. Save PM2 configuration for auto-restart

**Total deployment time**: Approximately 15-25 minutes

---

## Configuration

### Frontend Configuration Options

The frontend automatically detects the backend URL based on the hostname. This is configured in `frontend/src/lib/api/client.ts`:

```typescript
// Auto-detection logic (default behavior)
const getApiBaseUrl = () => {
  // 1. If NEXT_PUBLIC_API_URL is set, use it
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  // 2. If running in browser and not localhost, use hostname:8000
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return `http://${hostname}:8000`;
    }
  }

  // 3. Fallback to localhost
  return "http://localhost:8000";
};
```

**What this means**:
- If you access the app via `http://54.123.45.67:3000`, the frontend will automatically use `http://54.123.45.67:8000` for the backend
- No manual configuration needed for EC2 deployment with public IP
- Works seamlessly with custom domains too

### Backend Configuration

Key backend settings in `.env`:

```bash
# API Server
API_HOST=0.0.0.0          # Binds to all interfaces (publicly accessible)
API_PORT=8000             # Backend port
API_RELOAD=false          # Disable auto-reload in production

# Security
DEBUG=false               # Disable debug mode
LOG_LEVEL=INFO           # Production log level

# CORS (CRITICAL)
CORS_ORIGINS=["*"]       # Configure based on your needs
```

### LLM Provider Configuration

The application supports **hybrid mode** for optimal performance:

```bash
# Primary provider
LLM_PROVIDER=openai

# Phase-specific providers (Hybrid Mode - Recommended)
PLANNER_PROVIDER=openai    # Better reasoning for planning
CODER_PROVIDER=groq        # Faster execution for coding
INTENT_AGENT_PROVIDER=groq
```

**Models**:
```bash
# OpenAI
OPENAI_MODEL=gpt-4o
OPENAI_CHAT_MODEL_ID=gpt-4o

# Groq
GROQ_MODEL=openai/gpt-oss-120b
```

---

## Accessing Your Application

Once deployment completes, you'll see:

```
✅ Application started successfully!

Application is now accessible at:
  Frontend: http://54.123.45.67:3000
  Backend:  http://54.123.45.67:8000
  API Docs: http://54.123.45.67:8000/docs
```

### Access Points

1. **Frontend Application**:
   ```
   http://<EC2_PUBLIC_IP>:3000
   ```
   Main user interface for creating and managing workflows

2. **Backend API**:
   ```
   http://<EC2_PUBLIC_IP>:8000
   ```
   REST API endpoint

3. **API Documentation**:
   ```
   http://<EC2_PUBLIC_IP>:8000/docs
   ```
   Interactive Swagger/OpenAPI documentation

### First Time Setup

1. Open `http://<EC2_PUBLIC_IP>:3000` in your browser
2. You should see the IRA Workflow Builder welcome page
3. Click "Create New Workflow" to start
4. Upload a sample CSV file and begin the conversation flow

---

## Managing the Application

### Check Application Status

```bash
cd ~/ira_workflow_builder
./deploy_ec2.sh status
```

This shows PM2 process list and monitoring dashboard.

Or use PM2 directly:
```bash
pm2 list
```

Expected output:
```
┌─────┬────────────────┬─────────┬─────────┬──────────┐
│ id  │ name           │ mode    │ status  │ cpu      │
├─────┼────────────────┼─────────┼─────────┼──────────┤
│ 0   │ ira-backend    │ fork    │ online  │ 0%       │
│ 1   │ ira-frontend   │ fork    │ online  │ 0%       │
└─────┴────────────────┴─────────┴─────────┴──────────┘
```

### View Logs

**All logs**:
```bash
./deploy_ec2.sh logs
```

**Backend logs only**:
```bash
./deploy_ec2.sh logs backend
```

**Frontend logs only**:
```bash
./deploy_ec2.sh logs frontend
```

Or use PM2 directly:
```bash
pm2 logs ira-backend --lines 100
pm2 logs ira-frontend --lines 100
```

### Stop Application

```bash
./deploy_ec2.sh stop
```

### Restart Application

```bash
./deploy_ec2.sh restart
```

### Update Application Code

If you make changes and need to redeploy:

1. **From local machine** (upload and restart):
   ```bash
   ./deploy_ec2.sh <EC2_PUBLIC_IP> /path/to/your-key.pem ubuntu
   ```

2. **Manual update on EC2**:
   ```bash
   # SSH into EC2
   ssh -i /path/to/your-key.pem ubuntu@<EC2_PUBLIC_IP>

   # Pull latest code (if using git)
   cd ~/ira_workflow_builder
   git pull

   # Restart application
   ./deploy_ec2.sh restart
   ```

### Auto-Start on Reboot

PM2 is configured to auto-start on system reboot:

```bash
pm2 startup
pm2 save
```

This ensures your application restarts automatically if the EC2 instance reboots.

---

## Troubleshooting

### Issue 1: Cannot Connect to Frontend (Port 3000)

**Symptoms**: Browser shows "This site can't be reached" when accessing `http://<IP>:3000`

**Solutions**:
1. Check security group allows port 3000:
   ```bash
   # In AWS Console: EC2 → Security Groups → Inbound rules
   # Ensure port 3000 is open to 0.0.0.0/0 (or your IP)
   ```

2. Check if frontend is running:
   ```bash
   pm2 list
   pm2 logs ira-frontend
   ```

3. Check if port is listening:
   ```bash
   sudo netstat -tulpn | grep 3000
   ```

### Issue 2: Cannot Connect to Backend (Port 8000)

**Symptoms**: Frontend shows "Failed to fetch" or API errors

**Solutions**:
1. Check security group allows port 8000
2. Check if backend is running:
   ```bash
   pm2 logs ira-backend
   ```

3. Check backend is bound to 0.0.0.0:
   ```bash
   sudo netstat -tulpn | grep 8000
   ```
   Should show: `0.0.0.0:8000` (not `127.0.0.1:8000`)

4. Test API directly:
   ```bash
   curl http://localhost:8000/api/v1/health
   ```

### Issue 3: CORS Errors

**Symptoms**: Browser console shows CORS policy errors

**Solutions**:
1. Check `.env` file has correct CORS configuration:
   ```bash
   cat ~/ira_workflow_builder/.env | grep CORS_ORIGINS
   ```

2. For testing, use:
   ```bash
   CORS_ORIGINS=["*"]
   ```

3. For production, use exact IP/domain:
   ```bash
   CORS_ORIGINS=["http://54.123.45.67:3000", "http://54.123.45.67:8000"]
   ```

4. Restart backend after changing:
   ```bash
   pm2 restart ira-backend
   ```

### Issue 4: Out of Memory

**Symptoms**: PM2 shows process crashed, logs show memory errors

**Solutions**:
1. Check memory usage:
   ```bash
   free -h
   htop
   ```

2. Increase swap space:
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

3. Or upgrade to larger instance type (t3.large or t3.xlarge)

### Issue 5: Dependencies Installation Fails

**Symptoms**: `./deploy_ec2.sh start` fails during npm install or pip install

**Solutions**:
1. Check disk space:
   ```bash
   df -h
   ```

2. Clear npm cache:
   ```bash
   cd ~/ira_workflow_builder/frontend
   rm -rf node_modules package-lock.json
   npm cache clean --force
   npm install
   ```

3. Clear pip cache:
   ```bash
   pip cache purge
   ```

### Issue 6: PM2 Processes Not Starting

**Symptoms**: PM2 shows processes in "error" or "stopped" state

**Solutions**:
1. Check logs for errors:
   ```bash
   pm2 logs
   ```

2. Delete PM2 processes and restart:
   ```bash
   pm2 delete all
   pm2 flush
   ./deploy_ec2.sh start
   ```

3. Check file permissions:
   ```bash
   ls -la ~/ira_workflow_builder
   # Should be owned by ubuntu:ubuntu
   ```

### Issue 7: API Keys Not Working

**Symptoms**: Backend logs show "Invalid API key" or authentication errors

**Solutions**:
1. Verify API keys are correctly set in `.env`:
   ```bash
   cat ~/ira_workflow_builder/.env | grep API_KEY
   # Should NOT show the actual keys if properly set
   ```

2. Test OpenAI key:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. Test Groq key:
   ```bash
   curl https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY"
   ```

4. Ensure no extra spaces or quotes in `.env` file

### Issue 8: Frontend Build Fails

**Symptoms**: `npm run build` fails during deployment

**Solutions**:
1. Check Node.js version:
   ```bash
   node --version  # Should be v20.x
   ```

2. Increase Node memory:
   ```bash
   export NODE_OPTIONS="--max-old-space-size=4096"
   cd frontend
   npm run build
   ```

3. Check for TypeScript errors:
   ```bash
   cd frontend
   npm run type-check
   ```

---

## Production Best Practices

### 1. Security Hardening

#### Restrict Security Group Rules
Instead of `0.0.0.0/0`, use specific IP ranges:
```
Port 22:   Your office/home IP only
Port 3000: Specific user IP ranges
Port 8000: Only from port 3000 (or specific ranges)
```

#### Use HTTPS with SSL/TLS
Set up SSL certificate using:
- **Let's Encrypt** (free): Use Certbot for automatic SSL
- **AWS Certificate Manager**: For custom domains
- **Nginx/Caddy**: As reverse proxy with SSL termination

Example with Nginx:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Change Default Ports
Consider using standard ports (80/443) with reverse proxy instead of 3000/8000.

#### Enable Firewall
```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

### 2. Monitoring and Logging

#### Set up CloudWatch
Enable CloudWatch monitoring for EC2 metrics:
- CPU utilization
- Memory usage
- Disk I/O
- Network traffic

#### Application Logging
Configure log rotation:
```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 100M
pm2 set pm2-logrotate:retain 10
```

#### Health Checks
Set up automated health checks:
```bash
# Create health check script
cat > ~/health_check.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/api/v1/health || exit 1
curl -f http://localhost:3000 || exit 1
EOF

chmod +x ~/health_check.sh

# Add to crontab (every 5 minutes)
crontab -e
# Add: */5 * * * * ~/health_check.sh || systemctl restart pm2-ubuntu
```

### 3. Backups

#### Automated Data Backups
```bash
# Backup script
cat > ~/backup_data.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/backups
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/ira_data_$DATE.tar.gz \
  ~/ira_workflow_builder/data \
  ~/ira_workflow_builder/storage \
  ~/ira_workflow_builder/logs

# Keep only last 7 days
find $BACKUP_DIR -name "ira_data_*.tar.gz" -mtime +7 -delete
EOF

chmod +x ~/backup_data.sh

# Schedule daily backups at 2 AM
crontab -e
# Add: 0 2 * * * ~/backup_data.sh
```

#### AWS EBS Snapshots
Create automated EBS snapshots:
- AWS Console → EC2 → Volumes → Create Snapshot
- Set up snapshot lifecycle policy

### 4. Performance Optimization

#### Enable Production Mode
Ensure `.env` has:
```bash
APP_ENV=production
DEBUG=false
API_RELOAD=false
```

#### Use Process Clustering
For higher traffic, use PM2 cluster mode:
```bash
pm2 start backend/main.py --name ira-backend -i 2 --interpreter python3.11
```

#### Enable Caching
Configure API response caching for frequently accessed endpoints.

#### Database Optimization
If using PostgreSQL:
- Enable connection pooling
- Configure appropriate `max_connections`
- Set up read replicas for high traffic

### 5. Domain and DNS Setup

#### Using Custom Domain

1. **Purchase domain** (e.g., from Route 53, Namecheap, GoDaddy)

2. **Create DNS A records**:
   ```
   Type: A
   Name: @
   Value: <EC2_PUBLIC_IP>
   TTL: 300

   Type: A
   Name: www
   Value: <EC2_PUBLIC_IP>
   TTL: 300
   ```

3. **Update CORS settings** in `.env`:
   ```bash
   CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
   ```

4. **Update frontend `.env.production`**:
   ```bash
   NEXT_PUBLIC_API_URL=https://api.yourdomain.com
   ```

5. **Set up SSL** (Let's Encrypt with Certbot):
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

### 6. Cost Optimization

#### Use Reserved Instances
For long-term deployment, purchase Reserved Instances (up to 75% savings).

#### Implement Auto-Scaling
Set up Auto Scaling groups for variable traffic:
- Scale up during business hours
- Scale down during off-hours

#### Monitor Costs
Enable AWS Cost Explorer and set up billing alerts.

### 7. Disaster Recovery

#### Create AMI Image
Create custom AMI from your configured instance:
```
EC2 Console → Instances → Actions → Image and templates → Create image
```

#### Multi-AZ Deployment
For high availability:
- Deploy in multiple Availability Zones
- Use Elastic Load Balancer
- Configure failover routing

#### Document Recovery Procedures
Maintain runbook for:
- Instance failure recovery
- Data restore procedures
- Configuration rollback steps

---

## Additional Resources

### Helpful Commands

```bash
# Check Python version
python3.11 --version

# Check Node version
node --version

# Check PM2 processes
pm2 list
pm2 monit

# Check disk usage
df -h
du -sh ~/ira_workflow_builder/*

# Check memory usage
free -h

# Check running processes
ps aux | grep python
ps aux | grep node

# Check open ports
sudo netstat -tulpn

# View system logs
sudo journalctl -u pm2-ubuntu

# Check EC2 public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4
```

### File Locations

```
Application root:    ~/ira_workflow_builder/
Backend:            ~/ira_workflow_builder/backend/
Frontend:           ~/ira_workflow_builder/frontend/
Data directory:     ~/ira_workflow_builder/data/
Storage:            ~/ira_workflow_builder/storage/
Logs:               ~/ira_workflow_builder/logs/
Environment:        ~/ira_workflow_builder/.env
PM2 logs:           ~/.pm2/logs/
```

### Documentation Links

- **IRA Workflow Builder**: See project README.md
- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/docs
- **PM2**: https://pm2.keymetrics.io/docs/
- **AWS EC2**: https://docs.aws.amazon.com/ec2/
- **Ubuntu**: https://help.ubuntu.com/

---

## Support and Maintenance

### Regular Maintenance Tasks

**Weekly**:
- Check PM2 logs for errors
- Monitor disk usage
- Review CloudWatch metrics

**Monthly**:
- Update system packages: `sudo apt update && sudo apt upgrade`
- Review and rotate logs
- Check backup integrity
- Update application dependencies

**Quarterly**:
- Review security group rules
- Update SSL certificates (if not auto-renewed)
- Review and optimize costs
- Create new AMI backup

### Getting Help

If you encounter issues not covered in this guide:

1. **Check logs**: `pm2 logs` and application logs in `~/ira_workflow_builder/logs/`
2. **Review backend API docs**: `http://<EC2_IP>:8000/docs`
3. **Check GitHub issues**: For application-specific problems
4. **AWS Support**: For infrastructure issues

---

## Summary

You now have:
- ✅ EC2 instance configured with Ubuntu, Python 3.11, Node.js 20
- ✅ Application deployed and running via PM2
- ✅ Frontend accessible at `http://<EC2_IP>:3000`
- ✅ Backend API accessible at `http://<EC2_IP>:8000`
- ✅ Auto-restart configured for system reboots
- ✅ Comprehensive troubleshooting guide
- ✅ Production best practices for security, monitoring, and optimization

Your IRA Workflow Builder is now production-ready on AWS EC2!
