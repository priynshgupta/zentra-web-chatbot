const express = require('express');
const router = express.Router();
const websiteCategorizer = require('../services/websiteCategorizer');
const Website = require('../models/Website');
const axios = require('axios');
const auth = require('../middleware/auth');

// Process a new website
router.post('/process', async (req, res) => {
    try {
        const { url } = req.body;

        if (!url) {
            return res.status(400).json({
                success: false,
                error: 'URL is required'
            });
        }

        // Start processing in background
        websiteCategorizer.processWebsite(url)
            .then(website => {
                // This will be handled by the GET endpoint
            })
            .catch(error => {
                console.error('Error processing website:', error);
            });

        // Return immediately with processing status
        return res.json({
            success: true,
            message: 'Website processing started',
            url
        });
    } catch (error) {
        console.error('Error in /process:', error);
        return res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get website status and categories
router.get('/status/:url', async (req, res) => {
    try {
        const { url } = req.params;
        const website = await Website.findOne({ url });

        if (!website) {
            return res.status(404).json({
                success: false,
                error: 'Website not found'
            });
        }

        return res.json({
            success: true,
            website: {
                url: website.url,
                status: website.status,
                categories: website.categories,
                processed_pages: website.processed_pages,
                last_processed: website.last_processed,
                error_message: website.error_message
            }
        });
    } catch (error) {
        console.error('Error in /status:', error);
        return res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get all processed websites
router.get('/list', async (req, res) => {
    try {
        const websites = await Website.find()
            .select('url status categories.processed_pages last_processed')
            .sort({ last_processed: -1 });

        return res.json({
            success: true,
            websites
        });
    } catch (error) {
        console.error('Error in /list:', error);
        return res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get websites by industry
router.get('/industry/:industry', async (req, res) => {
    try {
        const { industry } = req.params;
        const websites = await Website.find({
            'categories.primary_industry': industry
        }).select('url categories status last_processed');

        return res.json({
            success: true,
            websites
        });
    } catch (error) {
        console.error('Error in /industry:', error);
        return res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Get websites by type
router.get('/type/:type', async (req, res) => {
    try {
        const { type } = req.params;
        const websites = await Website.find({
            'categories.website_type': type
        }).select('url categories status last_processed');

        return res.json({
            success: true,
            websites
        });
    } catch (error) {
        console.error('Error in /type:', error);
        return res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Load a previously processed website
router.post('/load', auth, async (req, res) => {
  try {
    const { websiteUrl } = req.body;

    if (!websiteUrl) {
      return res.status(400).json({
        success: false,
        message: 'Website URL is required'
      });
    }

    // Call the Flask backend to load the website
    const response = await axios.post('http://localhost:5000/load-website', {
      websiteUrl
    });

    if (response.data.success) {
      return res.json({
        success: true,
        message: response.data.message
      });
    } else {
      return res.status(404).json({
        success: false,
        message: response.data.error || 'Failed to load website'
      });
    }
  } catch (error) {
    console.error('Error loading website:', error.message);
    return res.status(500).json({
      success: false,
      message: 'Error loading website',
      error: error.message
    });
  }
});

module.exports = router;