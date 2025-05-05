const axios = require('axios');
const cheerio = require('cheerio');
const Website = require('../models/Website');

class WebsiteCategorizer {
    constructor() {
        this.industry_keywords = {
            'banking': ['bank', 'loan', 'mortgage', 'credit', 'debit', 'account', 'finance', 'investment'],
            'healthcare': ['hospital', 'clinic', 'doctor', 'medical', 'health', 'patient', 'treatment', 'medicine'],
            'education': ['school', 'university', 'college', 'course', 'student', 'teacher', 'education', 'learning'],
            'ecommerce': ['shop', 'store', 'product', 'cart', 'checkout', 'price', 'sale', 'buy'],
            'technology': ['software', 'hardware', 'tech', 'digital', 'computer', 'internet', 'app', 'mobile'],
            'government': ['gov', 'government', 'official', 'public', 'service', 'department', 'ministry'],
            'entertainment': ['movie', 'music', 'game', 'entertainment', 'show', 'media', 'stream'],
            'news': ['news', 'article', 'report', 'journal', 'press', 'media', 'headline'],
            'travel': ['travel', 'tourism', 'hotel', 'flight', 'booking', 'vacation', 'trip'],
            'real_estate': ['property', 'real estate', 'house', 'apartment', 'rent', 'sale', 'home']
        };

        this.website_types = {
            'corporate': ['about', 'company', 'corporate', 'business', 'enterprise'],
            'ecommerce': ['shop', 'store', 'cart', 'checkout', 'product'],
            'informational': ['about', 'info', 'information', 'guide', 'help'],
            'social': ['login', 'signup', 'profile', 'user', 'community', 'forum'],
            'service': ['service', 'support', 'help', 'contact', 'assistance'],
            'blog': ['blog', 'article', 'post', 'news', 'update'],
            'portfolio': ['portfolio', 'work', 'projects', 'gallery', 'showcase'],
            'directory': ['directory', 'listing', 'catalog', 'index', 'search']
        };
    }

    async fetchWebsiteContent(url) {
        try {
            const response = await axios.get(url, {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            });
            return response.data;
        } catch (error) {
            throw new Error(`Failed to fetch website content: ${error.message}`);
        }
    }

    analyzeContent(htmlContent) {
        try {
            const $ = cheerio.load(htmlContent);
            
            // Extract text content
            const textContent = $('body').text().toLowerCase();
            
            // Extract meta tags
            const metaTags = {
                title: $('title').text().toLowerCase(),
                description: $('meta[name="description"]').attr('content')?.toLowerCase() || '',
                keywords: $('meta[name="keywords"]').attr('content')?.toLowerCase() || ''
            };
            
            // Analyze industry
            const industryScores = this.analyzeIndustry(textContent, metaTags);
            const primaryIndustry = Object.entries(industryScores)
                .reduce((a, b) => a[1] > b[1] ? a : b)[0];
            
            // Analyze website type
            const typeScores = this.analyzeWebsiteType(textContent, metaTags);
            const primaryType = Object.entries(typeScores)
                .reduce((a, b) => a[1] > b[1] ? a : b)[0];
            
            // Analyze functionality
            const functionality = this.analyzeFunctionality($);
            
            // Analyze target audience
            const audience = this.analyzeTargetAudience(textContent, metaTags);
            
            return {
                primary_industry: primaryIndustry,
                industry_confidence: industryScores[primaryIndustry],
                website_type: primaryType,
                type_confidence: typeScores[primaryType],
                functionality,
                target_audience: audience,
                meta_information: metaTags
            };
        } catch (error) {
            throw new Error(`Error analyzing website content: ${error.message}`);
        }
    }

    analyzeIndustry(text, metaTags) {
        const scores = {};
        const combinedText = `${text} ${metaTags.title} ${metaTags.description} ${metaTags.keywords}`;
        
        for (const [industry, keywords] of Object.entries(this.industry_keywords)) {
            scores[industry] = keywords.reduce((score, keyword) => {
                const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
                return score + (combinedText.match(regex) || []).length * 0.1;
            }, 0);
        }
        
        // Normalize scores
        const maxScore = Math.max(...Object.values(scores));
        if (maxScore > 0) {
            Object.keys(scores).forEach(key => {
                scores[key] = scores[key] / maxScore;
            });
        }
        
        return scores;
    }

    analyzeWebsiteType(text, metaTags) {
        const scores = {};
        const combinedText = `${text} ${metaTags.title} ${metaTags.description} ${metaTags.keywords}`;
        
        for (const [type, keywords] of Object.entries(this.website_types)) {
            scores[type] = keywords.reduce((score, keyword) => {
                const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
                return score + (combinedText.match(regex) || []).length * 0.1;
            }, 0);
        }
        
        // Normalize scores
        const maxScore = Math.max(...Object.values(scores));
        if (maxScore > 0) {
            Object.keys(scores).forEach(key => {
                scores[key] = scores[key] / maxScore;
            });
        }
        
        return scores;
    }

    analyzeFunctionality($) {
        const functionality = [];
        
        if ($('form').length) functionality.push('forms');
        if ($('input[type="search"]').length) functionality.push('search');
        if ($('a[href*="login"], a[href*="signin"], a[href*="signup"], a[href*="register"]').length) {
            functionality.push('user_authentication');
        }
        if ($('a[href*="cart"], a[href*="checkout"], a[href*="basket"]').length) {
            functionality.push('ecommerce');
        }
        if ($('a[href*="blog"], a[href*="news"], a[href*="article"]').length) {
            functionality.push('content_management');
        }
        if ($('a[href*="social"], a[href*="share"], a[href*="facebook"], a[href*="twitter"]').length) {
            functionality.push('social_integration');
        }
        
        return functionality;
    }

    analyzeTargetAudience(text, metaTags) {
        const combinedText = `${text} ${metaTags.title} ${metaTags.description} ${metaTags.keywords}`;
        
        const b2bKeywords = ['business', 'enterprise', 'corporate', 'wholesale', 'b2b'];
        const b2cKeywords = ['consumer', 'customer', 'retail', 'personal', 'individual'];
        
        const b2bScore = b2bKeywords.reduce((score, keyword) => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            return score + (combinedText.match(regex) || []).length;
        }, 0);
        
        const b2cScore = b2cKeywords.reduce((score, keyword) => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            return score + (combinedText.match(regex) || []).length;
        }, 0);
        
        if (b2bScore > b2cScore) return 'B2B';
        if (b2cScore > b2bScore) return 'B2C';
        return 'General';
    }

    async processWebsite(url) {
        try {
            // Check if website already exists
            let website = await Website.findOne({ url });
            
            if (!website) {
                website = new Website({ url });
            }
            
            website.status = 'processing';
            await website.save();
            
            // Fetch and analyze website content
            const htmlContent = await this.fetchWebsiteContent(url);
            const categories = this.analyzeContent(htmlContent);
            
            // Update website with categories
            website.categories = categories;
            website.status = 'completed';
            website.processed_pages = 1; // For now, we're only processing the main page
            website.last_processed = new Date();
            
            await website.save();
            
            return website;
        } catch (error) {
            if (website) {
                website.status = 'failed';
                website.error_message = error.message;
                await website.save();
            }
            throw error;
        }
    }
}

module.exports = new WebsiteCategorizer(); 