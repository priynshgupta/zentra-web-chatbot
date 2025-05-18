# ZentraChatbot Deployment Guide

This guide explains how to deploy the ZentraChatbot project using DigitalOcean for the backend services and GitHub Pages for the frontend.

## Prerequisites

- GitHub Account with Student Developer Pack
- DigitalOcean Account (with credits from GitHub Student Developer Pack)
- MongoDB Atlas Account (free tier)
- Domain Name (optional, from Namecheap through Student Developer Pack)

## Part 1: Set Up MongoDB Atlas

1. Create a free MongoDB Atlas account
2. Create a new cluster
3. Set up a database user with a strong password
4. Configure IP access (Allow access from anywhere for DigitalOcean)
5. Get your MongoDB connection string

## Part 2: Deploy Backend to DigitalOcean

### Step 1: Create a Droplet or App Platform Project

**Option A: Using DigitalOcean App Platform (Recommended)**

1. Log in to your DigitalOcean account
2. Go to "Apps" and click "Create App"
3. Connect to your GitHub repository
4. Select the "ZentraChatbot" repository
5. Configure as follows:
   - Choose the "Dockerfile" deployment method
   - Set Environment Variables:
     - `MONGODB_URI`: Your MongoDB Atlas connection string
     - `JWT_SECRET`: A secure random string for JWT tokens
     - `CORS_ORIGIN`: Your GitHub Pages URL (e.g., https://yourusername.github.io/ZentraChatbot)
   - Configure Resources:
     - Basic Plan ($5/month)
   - Deploy the app

**Option B: Using a DigitalOcean Droplet**

1. Create a new Droplet (Basic Plan, $5/month)
2. Select Ubuntu as the operating system
3. Add your SSH key
4. Once created, SSH into your Droplet
5. Install Docker and Docker Compose:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo systemctl enable docker
   sudo systemctl start docker
   ```
6. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/ZentraChatbot.git
   cd ZentraChatbot
   ```
7. Create a `.env` file:
   ```bash
   echo "MONGODB_URI=your_mongodb_atlas_connection_string" > .env
   echo "JWT_SECRET=your_secure_random_string" >> .env
   echo "CORS_ORIGIN=https://yourusername.github.io/ZentraChatbot" >> .env
   ```
8. Start the application:
   ```bash
   sudo docker-compose up -d
   ```

## Part 3: Deploy Frontend to GitHub Pages

1. Update the frontend environment variables:
   - Edit `.env.production` in the frontend directory:
     ```
     REACT_APP_API_URL=https://your-digitalocean-app-url
     REACT_APP_NODE_API_URL=https://your-digitalocean-app-url
     REACT_APP_FLASK_API_URL=https://your-digitalocean-app-url
     REACT_APP_GITHUB_PAGES=true
     PUBLIC_URL=https://yourusername.github.io/ZentraChatbot
     ```

2. Deploy to GitHub Pages:
   ```bash
   cd frontend
   npm install
   npm run deploy
   ```

3. Configure GitHub Pages in your repository:
   - Go to your repository on GitHub
   - Go to "Settings" > "Pages"
   - Set the source to "gh-pages" branch
   - Save the settings

## Part 4: Configure Domain Name (Optional)

If you have a domain name from Namecheap:

1. Add an A record pointing to your DigitalOcean Droplet's IP address
2. Configure CNAME for www to point to your GitHub Pages URL
3. Update your frontend .env.production file with your custom domain
4. Update CORS settings in the backend to allow your custom domain

## Troubleshooting

- If you encounter CORS errors, check the CORS_ORIGIN in your .env file
- If the backend is not accessible, check your DigitalOcean firewall settings
- For MongoDB connection issues, verify your connection string and network access settings

## Maintenance

- Monitor your application using DigitalOcean's built-in monitoring
- Set up automatic backups for your Droplet
- Set up GitHub Actions for continuous deployment
