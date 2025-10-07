// API Configuration service for ZentraChatbot
// This file centralizes API endpoint configuration for development

const getApiBaseUrl = () => {
  // For local development (default)
  return 'http://localhost:4000';
};

const getFlaskApiUrl = () => {
  // For local development (default)
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
