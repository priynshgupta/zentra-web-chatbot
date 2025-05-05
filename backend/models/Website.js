const mongoose = require('mongoose');

const websiteSchema = new mongoose.Schema({
    url: {
        type: String,
        required: true,
        unique: true
    },
    categories: {
        primary_industry: {
            type: String,
            required: true
        },
        industry_confidence: {
            type: Number,
            required: true
        },
        website_type: {
            type: String,
            required: true
        },
        type_confidence: {
            type: Number,
            required: true
        },
        functionality: [{
            type: String
        }],
        target_audience: {
            type: String,
            required: true
        },
        meta_information: {
            title: String,
            description: String,
            keywords: String
        }
    },
    processed_pages: {
        type: Number,
        default: 0
    },
    last_processed: {
        type: Date,
        default: Date.now
    },
    status: {
        type: String,
        enum: ['pending', 'processing', 'completed', 'failed'],
        default: 'pending'
    },
    error_message: String
}, {
    timestamps: true
});

module.exports = mongoose.model('Website', websiteSchema); 