# ZentraChatbot Deployment Guide

This guide explains how to deploy the ZentraChatbot project using Heroku for the backend services and GitHub Pages for the frontend.

## Prerequisites

- GitHub Account with Student Developer Pack
- Heroku Account (with student benefits from GitHub Student Developer Pack)
- MongoDB Atlas Account (free tier)
- Domain Name (optional, from Namecheap through Student Developer Pack)

## Part 1: Set Up MongoDB Atlas

1. Create a free MongoDB Atlas account
2. Create a new cluster
3. Set up a database user with a strong password
4. Configure IP access (Allow access from anywhere for DigitalOcean)
5. Get your MongoDB connection string

## Part 2: Deploy Backend to Heroku

Heroku provides two approaches for deploying our application: deploying the Python Flask backend and Node.js backend separately, or using a combined approach. We'll cover both methods:

### Option A: Deploy Python and Node.js Services Separately (Recommended)

#### Step 1: Deploy Node.js Backend

1. Install the Heroku CLI:
   ```bash
   # For Windows
   winget install --id=Heroku.HerokuCLI -e
   # OR
   npm install -g heroku
   ```

2. Log in to Heroku:
   ```bash
   heroku login
   ```

3. Create a new Heroku app for the Node.js backend:
   ```bash
   cd backend
   heroku create zentrachatbot-node
   ```

4. Add a Procfile for the Node.js backend:
   ```bash
   echo "web: node server.js" > Procfile
   ```

5. Add MongoDB as an add-on or use MongoDB Atlas:
   ```bash
   # If using MongoDB Atlas, skip this step
   # If using Heroku's MongoDB add-on:
   heroku addons:create mongolab:sandbox
   ```

6. Set environment variables:
   ```bash
   heroku config:set JWT_SECRET=your_secure_random_string
   heroku config:set CORS_ORIGIN=https://yourusername.github.io/ZentraChatbot
   # If using MongoDB Atlas:
   heroku config:set MONGODB_URI=your_mongodb_atlas_connection_string
   ```

7. Deploy to Heroku:
   ```bash
   git subtree push --prefix backend heroku main
   ```

#### Step 2: Deploy Python Flask Backend

1. Create a new Heroku app for the Flask backend:
   ```bash
   cd ..  # Return to project root
   heroku create zentrachatbot-flask
   ```

2. Create a runtime.txt file to specify Python version:
   ```bash
   echo "python-3.9.18" > runtime.txt
   ```

3. Set environment variables:
   ```bash
   heroku config:set NODE_BACKEND_URL=https://zentrachatbot-node.herokuapp.com
   heroku config:set FLASK_ENV=production
   ```

4. Deploy to Heroku:
   ```bash
   git push https://git.heroku.com/zentrachatbot-flask.git main
   ```

### Option B: Deploy Combined Services Using Heroku's Container Registry

1. Install Docker on your local machine if you haven't already

2. Create a new Heroku app:
   ```bash
   heroku create zentrachatbot
   ```

3. Log in to Heroku Container Registry:
   ```bash
   heroku container:login
   ```

4. Build and push the Docker image:
   ```bash
   heroku container:push web
   ```

5. Release the container:
   ```bash
   heroku container:release web
   ```

6. Set environment variables:
   ```bash
   heroku config:set MONGODB_URI=your_mongodb_atlas_connection_string
   heroku config:set JWT_SECRET=your_secure_random_string
   heroku config:set CORS_ORIGIN=https://yourusername.github.io/ZentraChatbot
   ```

## Part 3: Deploy Frontend to GitHub Pages

1. Update the frontend environment variables:
   - Edit `.env.production` in the frontend directory:
     ```
     REACT_APP_API_URL=https://zentrachatbot-node.herokuapp.com
     REACT_APP_NODE_API_URL=https://zentrachatbot-node.herokuapp.com
     REACT_APP_FLASK_API_URL=https://zentrachatbot-flask.herokuapp.com
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

1. For the Heroku backend:
   - Go to your Heroku app dashboard
   - Navigate to Settings > Domains and Certificates
   - Click "Add Domain" and follow the instructions
   - Add a CNAME record in your Namecheap DNS settings pointing to your Heroku app URL

2. For GitHub Pages frontend:
   - Configure CNAME for www or another subdomain to point to your GitHub Pages URL
   - Add a CNAME file to your repository containing your domain

3. Update your frontend .env.production file with your custom domain
4. Update CORS settings in the backend to allow your custom domain:
   ```bash
   heroku config:set CORS_ORIGIN=https://yourdomain.com
   ```

## Troubleshooting

- If you encounter CORS errors, check the CORS_ORIGIN in your Heroku config vars
- If the backend is not accessible, check your Heroku logs: `heroku logs --tail --app zentrachatbot-node`
- For MongoDB connection issues, verify your connection string and network access settings
- For deployment issues, try redeploying with `git push heroku main -f`

## Maintenance

- Monitor your application using Heroku's built-in monitoring
- Set up Heroku Scheduler for regular maintenance tasks
- Enable Heroku's Auto-Idle to save dyno hours on free tier
- Set up GitHub Actions for continuous deployment

## Additional Heroku Tips

- To scale your app: `heroku ps:scale web=1:hobby`
- To view logs: `heroku logs --tail`
- To run one-off commands: `heroku run python -c "import nltk; nltk.download('punkt')"`
- To restart the app: `heroku restart`
