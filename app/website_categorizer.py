from bs4 import BeautifulSoup
import requests
import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class WebsiteCategorizer:
    def __init__(self):
        self.industry_keywords = {
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
        }

        self.website_types = {
            'corporate': ['about', 'company', 'corporate', 'business', 'enterprise'],
            'ecommerce': ['shop', 'store', 'cart', 'checkout', 'product'],
            'informational': ['about', 'info', 'information', 'guide', 'help'],
            'social': ['login', 'signup', 'profile', 'user', 'community', 'forum'],
            'service': ['service', 'support', 'help', 'contact', 'assistance'],
            'blog': ['blog', 'article', 'post', 'news', 'update'],
            'portfolio': ['portfolio', 'work', 'projects', 'gallery', 'showcase'],
            'directory': ['directory', 'listing', 'catalog', 'index', 'search']
        }

    def analyze_content(self, html_content: str) -> Dict:
        """Analyze website content and return categorization results"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text().lower()
            
            # Extract meta tags
            meta_tags = {
                'title': soup.title.string.lower() if soup.title else '',
                'description': soup.find('meta', {'name': 'description'})['content'].lower() if soup.find('meta', {'name': 'description'}) else '',
                'keywords': soup.find('meta', {'name': 'keywords'})['content'].lower() if soup.find('meta', {'name': 'keywords'}) else ''
            }
            
            # Analyze industry
            industry_scores = self._analyze_industry(text_content, meta_tags)
            primary_industry = max(industry_scores.items(), key=lambda x: x[1])[0]
            
            # Analyze website type
            type_scores = self._analyze_website_type(text_content, meta_tags)
            primary_type = max(type_scores.items(), key=lambda x: x[1])[0]
            
            # Analyze functionality
            functionality = self._analyze_functionality(soup)
            
            # Analyze target audience
            audience = self._analyze_target_audience(text_content, meta_tags)
            
            return {
                'primary_industry': primary_industry,
                'industry_confidence': industry_scores[primary_industry],
                'website_type': primary_type,
                'type_confidence': type_scores[primary_type],
                'functionality': functionality,
                'target_audience': audience,
                'meta_information': meta_tags
            }
            
        except Exception as e:
            logger.error(f"Error analyzing website content: {str(e)}")
            return {
                'error': str(e),
                'primary_industry': 'unknown',
                'website_type': 'unknown'
            }

    def _analyze_industry(self, text: str, meta_tags: Dict) -> Dict[str, float]:
        """Analyze and score potential industries"""
        scores = {industry: 0.0 for industry in self.industry_keywords.keys()}
        
        # Combine all text for analysis
        combined_text = f"{text} {meta_tags['title']} {meta_tags['description']} {meta_tags['keywords']}"
        
        for industry, keywords in self.industry_keywords.items():
            for keyword in keywords:
                # Count keyword occurrences
                count = len(re.findall(r'\b' + keyword + r'\b', combined_text))
                scores[industry] += count * 0.1  # Weight factor for each occurrence
        
        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 1
        if max_score > 0:
            scores = {k: v/max_score for k, v in scores.items()}
        
        return scores

    def _analyze_website_type(self, text: str, meta_tags: Dict) -> Dict[str, float]:
        """Analyze and score potential website types"""
        scores = {type_: 0.0 for type_ in self.website_types.keys()}
        
        # Combine all text for analysis
        combined_text = f"{text} {meta_tags['title']} {meta_tags['description']} {meta_tags['keywords']}"
        
        for type_, keywords in self.website_types.items():
            for keyword in keywords:
                # Count keyword occurrences
                count = len(re.findall(r'\b' + keyword + r'\b', combined_text))
                scores[type_] += count * 0.1  # Weight factor for each occurrence
        
        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 1
        if max_score > 0:
            scores = {k: v/max_score for k, v in scores.items()}
        
        return scores

    def _analyze_functionality(self, soup: BeautifulSoup) -> List[str]:
        """Analyze website functionality based on HTML elements"""
        functionality = []
        
        # Check for common functionality indicators
        if soup.find('form'):
            functionality.append('forms')
        if soup.find('input', {'type': 'search'}):
            functionality.append('search')
        if soup.find('a', href=re.compile(r'login|signin|signup|register')):
            functionality.append('user_authentication')
        if soup.find('a', href=re.compile(r'cart|checkout|basket')):
            functionality.append('ecommerce')
        if soup.find('a', href=re.compile(r'blog|news|article')):
            functionality.append('content_management')
        if soup.find('a', href=re.compile(r'social|share|facebook|twitter')):
            functionality.append('social_integration')
        
        return functionality

    def _analyze_target_audience(self, text: str, meta_tags: Dict) -> str:
        """Analyze target audience based on content"""
        combined_text = f"{text} {meta_tags['title']} {meta_tags['description']} {meta_tags['keywords']}"
        
        # Simple keyword-based analysis
        b2b_keywords = ['business', 'enterprise', 'corporate', 'wholesale', 'b2b']
        b2c_keywords = ['consumer', 'customer', 'retail', 'personal', 'individual']
        
        b2b_score = sum(len(re.findall(r'\b' + keyword + r'\b', combined_text)) for keyword in b2b_keywords)
        b2c_score = sum(len(re.findall(r'\b' + keyword + r'\b', combined_text)) for keyword in b2c_keywords)
        
        if b2b_score > b2c_score:
            return 'B2B'
        elif b2c_score > b2b_score:
            return 'B2C'
        else:
            return 'General' 