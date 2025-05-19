# Heroku Setup for ZentraChatbot with GitHub Student Developer Pack

This guide provides specific instructions for setting up your ZentraChatbot backend on Heroku using your GitHub Student Developer Pack benefits.

## Student Pack Benefits for Heroku

With the GitHub Student Developer Pack, you receive:
- One free Dyno for up to 2 years
- Free Hobby Dynos (normally $7/month)
- $13 credit per month for add-ons or databases

## Step 1: Claim Your Student Pack Benefits

1. Go to the [GitHub Student Developer Pack](https://education.github.com/pack) page
2. Find the Heroku offer and click "Get access"
3. Follow the instructions to link your GitHub and Heroku accounts
4. Verify that the benefits have been applied to your Heroku account

## Step 2: Set Up Heroku CLI

1. Install the Heroku CLI:
   ```bash
   # For Windows
   winget install --id=Heroku.HerokuCLI -e
   # OR
   npm install -g heroku
   ```

2. Log in to your Heroku account:
   ```bash
   heroku login
   ```

## Step 3: Deploy Node.js Backend

1. Create a new Heroku app:
   ```bash
   cd backend
   heroku create zentrachatbot-node --buildpack heroku/nodejs
   ```

2. Set up MongoDB:
   ```bash
   # If using MongoDB Atlas:
   heroku config:set MONGODB_URI=your_mongodb_atlas_connection_string

   # OR use Heroku's MongoDB add-on (uses your credits):
   heroku addons:create mongolab:sandbox
   ```

3. Set environment variables:
   ```bash
   heroku config:set JWT_SECRET=your_secure_random_string
   heroku config:set CORS_ORIGIN=https://your-github-username.github.io/ZentraChatbot
   ```

4. Deploy the Node.js backend:
   ```bash
   git subtree push --prefix backend heroku main
   ```

   If you encounter errors, try:
   ```bash
   git push heroku `git subtree split --prefix backend main`:main --force
   ```

## Step 4: Deploy Flask Backend

1. Create another Heroku app:
   ```bash
   cd ..  # Return to project root
   heroku create zentrachatbot-flask --buildpack heroku/python
   ```

2. Set environment variables:
   ```bash
   heroku config:set NODE_BACKEND_URL=https://zentrachatbot-node.herokuapp.com
   heroku config:set FLASK_ENV=production
   ```

3. Deploy to Heroku:
   ```bash
   git push https://git.heroku.com/zentrachatbot-flask.git main
   ```

   If you want to deploy just the Python part:
   ```bash
   heroku git:remote -a zentrachatbot-flask
   git push heroku main
   ```

## Step 5: Verify Deployment

1. Check the Node.js backend:
   ```bash
   heroku open --app zentrachatbot-node
   # OR
   curl https://zentrachatbot-node.herokuapp.com/api/auth/health
   ```

2. Check the Flask backend:
   ```bash
   heroku open --app zentrachatbot-flask
   # OR
   curl https://zentrachatbot-flask.herokuapp.com/health
   ```

## Step 6: Scale Your App (Optional)

With your student credits, you can upgrade to better dynos:

```bash
# For Node.js backend
heroku ps:scale web=1:hobby --app zentrachatbot-node

# For Flask backend
heroku ps:scale web=1:hobby --app zentrachatbot-flask
```

## Troubleshooting

- **Deployment fails with "No default language could be detected"**:
  Make sure you have appropriate buildpacks set:
  ```bash
  heroku buildpacks:set heroku/nodejs --app zentrachatbot-node
  heroku buildpacks:set heroku/python --app zentrachatbot-flask
  ```

- **Application crashes on startup**:
  Check the logs:
  ```bash
  heroku logs --tail --app zentrachatbot-node
  ```

- **MongoDB connection issues**:
  Verify your connection string and that the IP is whitelisted in MongoDB Atlas

## Managing Your Student Credits

To check your usage and remaining credits:
1. Go to your [Heroku Dashboard](https://dashboard.heroku.com/)
2. Click on your account in the top-right corner
3. Select "Billing"
4. You'll see your GitHub Student Pack credits listed there
