const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');
const authRoutes = require('./routes/auth');
const chatRoutes = require('./routes/chat');
const fs = require('fs');
const path = require('path');
const websiteRoutes = require('./routes/website');

// Load environment variables from .env file
dotenv.config();

const app = express();

// Middleware
app.use(cors({
  origin: process.env.CORS_ORIGIN || '*',
  credentials: true
}));
app.use(express.json());

// MongoDB Connection - Use environment variable or fallback to local
const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/zentraChatbot';
console.log('\n=== Environment Variables Check ===');
console.log('Using MongoDB URI:', mongoUri.replace(/mongodb\+srv:\/\/([^:]+):[^@]+@/, 'mongodb+srv://$1:****@')); // Hide password in logs
console.log('================================\n');

// Remove any existing MongoDB connection
mongoose.disconnect();

// Clear mongoose connection cache
mongoose.connection.close();

// Connect to MongoDB
mongoose.connect(mongoUri, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
  serverSelectionTimeoutMS: 5000, // Timeout after 5s instead of 30s
  forceServerObjectId: true
})
.then(async () => {
  console.log('\n=== MongoDB Connection Status ===');
  console.log('✅ MongoDB connected successfully');
  console.log('Using URI:', mongoUri);

  // Get database information
  const db = mongoose.connection.db;
  const collections = await db.listCollections().toArray();

  console.log('\n=== Database Information ===');
  console.log('Current Database:', db.databaseName);
  console.log('Available Collections:');
  collections.forEach(collection => {
    console.log(`- ${collection.name}`);
  });

  // Check for required collections
  const hasUsers = collections.some(col => col.name === 'users');
  const hasChats = collections.some(col => col.name === 'chats');

  console.log('\n=== Collection Status ===');
  console.log('users collection:', hasUsers ? '✅ Found' : '❌ Missing');
  console.log('chats collection:', hasChats ? '✅ Found' : '❌ Missing');

  // Get document counts
  if (hasUsers) {
    const userCount = await db.collection('users').countDocuments();
    console.log('Total users:', userCount);
  }
  if (hasChats) {
    const chatCount = await db.collection('chats').countDocuments();
    console.log('Total chats:', chatCount);
  }

  console.log('================================\n');
})
.catch(err => {
  console.error('\n=== MongoDB Connection Error ===');
  console.error('❌ Connection failed:', err.message);
  console.error('Attempted URI:', mongoUri);
  console.error('================================\n');
  process.exit(1);
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/chat', chatRoutes);
app.use('/api/website', websiteRoutes);

// Adjust this to your actual vector store path
const VECTOR_STORE_PATH = path.join(__dirname, '..', 'chroma');
const MAPPING_FILE = path.join(VECTOR_STORE_PATH, 'vector_store_map.json');

app.get('/previous-websites', (req, res) => {
  try {
    if (!fs.existsSync(MAPPING_FILE)) {
      return res.json({ success: true, websites: [] });
    }
    const mapping = JSON.parse(fs.readFileSync(MAPPING_FILE));
    // Return an array of { url, collection_name, timestamp }
    const websites = Object.entries(mapping).map(([url, value]) => {
      if (typeof value === 'string') {
        // Backward compatibility: old format
        return { url, collection_name: value, timestamp: undefined };
      } else {
        return { url, collection_name: value.collection_name, timestamp: value.timestamp };
      }
    });
    res.json({ success: true, websites });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Helper function to add a new website with timestamp
function addWebsiteToMapping(newUrl, newCollectionName) {
  let mapping = {};
  if (fs.existsSync(MAPPING_FILE)) {
    mapping = JSON.parse(fs.readFileSync(MAPPING_FILE));
  }
  mapping[newUrl] = {
    collection_name: newCollectionName,
    timestamp: new Date().toISOString()
  };
  fs.writeFileSync(MAPPING_FILE, JSON.stringify(mapping, null, 2));
}

app.delete('/api/remove-website', (req, res) => {
  const { url } = req.body;
  if (!url) {
    return res.status(400).json({ success: false, message: 'url is required' });
  }
  let mapping = {};
  if (fs.existsSync(MAPPING_FILE)) {
    mapping = JSON.parse(fs.readFileSync(MAPPING_FILE));
  }
  if (mapping[url]) {
    delete mapping[url];
    fs.writeFileSync(MAPPING_FILE, JSON.stringify(mapping, null, 2));
    return res.json({ success: true, message: 'Website removed' });
  } else {
    return res.status(404).json({ success: false, message: 'Website not found' });
  }
});

const PORT = process.env.NODE_PORT || 4000;
const server = app.listen(PORT, () => {
  console.log(`Node backend running on port ${PORT}`);
}).on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.warn(`⚠️ Port ${PORT} is already in use. Trying port ${PORT + 1}...`);
    // Try a different port
    const newPort = PORT + 1;
    server.close();
    app.listen(newPort, () => {
      console.log(`Node backend running on port ${newPort} (fallback)`);
    });
  } else {
    console.error('Server error:', err);
  }
});

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('\n🛑 Received SIGINT (CTRL+C). Shutting down gracefully...');
  server.close(() => {
    console.log('✅ Express server closed.');
    mongoose.connection.close(false, () => {
      console.log('✅ MongoDB connection closed.');
      // Try to kill any lingering processes on our ports
      try {
        console.log('🔫 Attempting to kill any processes still using our ports...');
        require('child_process').execSync('node ../kill-ports.js');
      } catch (err) {
        console.error('⚠️ Error running port kill script:', err.message);
      }
      process.exit(0);
    });
  });

  // Safety timeout - force exit if graceful shutdown takes too long
  setTimeout(() => {
    console.error('⚠️ Shutdown is taking too long. Forcing exit.');
    process.exit(1);
  }, 5000);
});