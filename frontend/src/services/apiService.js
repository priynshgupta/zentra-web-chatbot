// API Configuration service for ZentraChatbot
// This file centralizes API endpoint configuration for deployment

const getApiBaseUrl = () => {
  // For production (GitHub Pages)
  if (process.env.REACT_APP_GITHUB_PAGES === 'true') {
    return process.env.REACT_APP_API_URL || 'https://your-digitalocean-domain-or-ip';
  }

  // For local development
  return 'http://localhost:4000';
};

const getFlaskApiUrl = () => {
  if (process.env.REACT_APP_GITHUB_PAGES === 'true') {
    return process.env.REACT_APP_FLASK_API_URL || 'https://your-digitalocean-domain-or-ip:5000';
  }

  return 'http://localhost:5000';
};

const apiService = {
  // Auth endpoints
  auth: {
    login: `${getApiBaseUrl()}/api/auth/login`,
    register: `${getApiBaseUrl()}/api/auth/signup`,
    me: `${getApiBaseUrl()}/api/auth/me`,
  },

  // Chat endpoints
  chat: {
    list: `${getApiBaseUrl()}/api/chat`,
    create: `${getApiBaseUrl()}/api/chat`,
    sendMessage: `${getFlaskApiUrl()}/chat`,
  },

  // Website endpoints
  website: {
    list: `${getApiBaseUrl()}/api/website/list`,
    process: `${getApiBaseUrl()}/api/website/process`,
    load: `${getApiBaseUrl()}/api/website/load`,
    status: (url) => `${getApiBaseUrl()}/api/website/status/${encodeURIComponent(url)}`,
    byIndustry: (industry) => `${getApiBaseUrl()}/api/website/industry/${industry}`,
    byType: (type) => `${getApiBaseUrl()}/api/website/type/${type}`,
  },

  // Miscellaneous
  previousWebsites: `${getApiBaseUrl()}/previous-websites`,
};

export default apiService;
