import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Divider,
  AppBar,
  Toolbar,
  IconButton,
  CircularProgress,
  Drawer,
  Menu,
  MenuItem,
  Snackbar,
  Alert,
  Tooltip,
  Fade,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress
} from '@mui/material';
import {
  Send as SendIcon,
  Logout as LogoutIcon,
  History as HistoryIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  Upload as UploadIcon,
  Language as WebIcon,
  AccountCircle as AccountCircleIcon,
  Settings as SettingsIcon,
  ContactMail as ContactMailIcon,
  MoreVert as MoreVertIcon,
  Edit as EditIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ListItemIcon from '@mui/material/ListItemIcon';
import BotLogo from '../assets/bot-logo.png';
import apiService from '../services/apiService';

const TypingDots = () => (
  <Box sx={{ display: 'flex', alignItems: 'center', height: 24 }}>
    <Box
      component="span"
      sx={{
        display: 'inline-block',
        width: 8,
        height: 8,
        bgcolor: 'primary.main',
        borderRadius: '50%',
        mx: 0.5,
        animation: 'typingDot 1.2s infinite',
        '@keyframes typingDot': {
          '0%': { opacity: 0.2, transform: 'scale(1)' },
          '20%': { opacity: 1, transform: 'scale(1.3)' },
          '100%': { opacity: 0.2, transform: 'scale(1)' }
        }
      }}
    />
    <Box
      component="span"
      sx={{
        display: 'inline-block',
        width: 8,
        height: 8,
        bgcolor: 'primary.main',
        borderRadius: '50%',
        mx: 0.5,
        animation: 'typingDot 1.2s infinite',
        animationDelay: '0.2s'
      }}
    />
    <Box
      component="span"
      sx={{
        display: 'inline-block',
        width: 8,
        height: 8,
        bgcolor: 'primary.main',
        borderRadius: '50%',
        mx: 0.5,
        animation: 'typingDot 1.2s infinite',
        animationDelay: '0.4s'
      }}
    />
  </Box>
);

const Chat = () => {
  const { user, isAuthenticated, loading: authLoading, logout } = useAuth();
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [chatId, setChatId] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [anchorEl, setAnchorEl] = useState(null);
  const [error, setError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [currentPreview, setCurrentPreview] = useState(null);
  const [contentType, setContentType] = useState(null);
  const [previewTitle, setPreviewTitle] = useState(null);
  const [showWebsiteDialog, setShowWebsiteDialog] = useState(false);
  const [previousWebsites, setPreviousWebsites] = useState([]);
  const [showProgress, setShowProgress] = useState(false);
  const [progressMessage, setProgressMessage] = useState('');
  const [scrapingLink, setScrapingLink] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const messagesEndRef = useRef(null);
  const [sid, setSid] = useState(null);
  const [profileAnchorEl, setProfileAnchorEl] = useState(null);
  const openProfileMenu = Boolean(profileAnchorEl);
  const [menuAnchorEls, setMenuAnchorEls] = useState({});
  const [renameDialogOpen, setRenameDialogOpen] = useState(false);
  const [renameValue, setRenameValue] = useState('');
  const [renameChatId, setRenameChatId] = useState(null);
  const [showNewChatDialog, setShowNewChatDialog] = useState(false);
  const cancelRequestRef = useRef(null);

  // Profile menu state
  const [profileMenuAnchorEl, setProfileMenuAnchorEl] = useState(null);
  const profileMenuOpen = Boolean(profileMenuAnchorEl);

  const handleProfileMenuClick = (event) => {
    setProfileMenuAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setProfileMenuAnchorEl(null);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    if (user) {
      fetchChatHistory();
    }
  }, [user]);
  const fetchChatHistory = async () => {
    try {
      const response = await axios.get(apiService.chat.list);
      setChatHistory(response.data);
    } catch (error) {
      showError('Failed to fetch chat history', error.response?.data?.message);
    }
  };

  const showError = (message, details = null, severity = 'error') => {
    setError({
      message,
      details,
      severity
    });
    setTimeout(() => setError(null), 5000);
  };

  const fetchPreviousWebsites = async () => {
    try {
      const response = await axios.get(`http://localhost:4000/previous-websites`);
      if (response.data.success) {
        setPreviousWebsites(response.data.websites);
      } else {
        showError(response.data.error || 'Failed to fetch previous websites');
      }
    } catch (error) {
      console.error('Error fetching previous websites:', error);
      showError('Failed to fetch previous websites', error.response?.data?.error);
    }
  };

  const isValidObjectId = (id) => typeof id === 'string' && id.length === 24 && /^[a-fA-F0-9]+$/.test(id);

  const handleWebsiteSelect = async (website) => {
    setShowWebsiteDialog(false);
    setWebsiteUrl(website.url);
    setLoading(true);
    setScrapingLink('');
    setProgressMessage('');
    setShowProgress(true);
    setProgressMessage('⏳ Loading previous website, please wait...');

    try {
      // Set proper authentication headers
      const config = {
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        }
      };

      // First, load the website in the Flask server
      console.log('Loading website in Flask server:', website.url);
      const loadResponse = await axios.post('http://localhost:4000/api/website/load',
        { websiteUrl: website.url },
        config
      );

      if (!loadResponse.data.success) {
        throw new Error(loadResponse.data.message || 'Failed to load website in backend');
      }

      console.log('Website loaded in Flask successfully');

      // Then create a chat for this website
      const response = await axios.post('http://localhost:4000/api/chat',
        { websiteUrl: website.url },
        config
      );

      if (response.data && response.data._id) {
        // Set chat ID and load the chat
        const chatId = response.data._id;
        setChatId(chatId);

        // Close any dialogs
        setShowNewChatDialog(false);

        // Show welcome messages
        setMessages([
          { role: 'assistant', content: `✅ Website loaded: ${website.url}` },
          { role: 'assistant', content: 'You can now ask questions about this website.' }
        ]);

        setShowProgress(false);
        setProgressMessage('');
        setSuccessMessage('✅ Website loaded successfully.');
        setTimeout(() => setSuccessMessage(''), 5000);

        // Refresh chat history
        fetchChatHistory();
      } else {
        setShowProgress(false);
        setProgressMessage('');
        showError('Failed to create new chat for website');
      }
    } catch (error) {
      console.error('Failed to load website:', error);
      setShowProgress(false);
      setProgressMessage('');
      showError(`Failed to load website: ${error.response?.data?.message || error.message}`);
    }

    setLoading(false);
  };

  const handleWebsiteSubmit = async (e) => {
    e.preventDefault();
    if (!user?.id) {
      showError('Please login to continue');
      return;
    }
    if (!websiteUrl) {
      showError('Please enter a website URL');
      return;
    }
    if (!websiteUrl.startsWith('http://') && !websiteUrl.startsWith('https://')) {
      showError('Invalid URL format. URL must start with http:// or https://');
      return;
    }

    setShowProgress(true);
    setProgressMessage("⏳ Hang tight, I'm processing your website!");
    setLoading(true);
    setError(null);
    setMessages(prev => prev.concat({ role: 'user', content: websiteUrl }));
    setScrapingLink('');

    const source = axios.CancelToken.source();
    cancelRequestRef.current = source;

    try {
      // Store user ID for session
      setSid(user.id);

      // Create request with Authorization header
      const config = {
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        },
        cancelToken: source.token
      };

      const response = await axios.post(
        `http://localhost:5000/process-website?sid=${user.id}`,
        { websiteUrl, userId: user.id },
        config
      );

      if (response.data.success) {
        // Rest of the code remains the same
        setWebsiteUrl('');
        setShowProgress(false);
        setProgressMessage('');
        setContentType('Website');
        setCurrentPreview(`Website processed successfully. Scraped ${response.data.pages_processed} pages.`);
        setPreviewTitle(response.data.website_url);
        setPreviewOpen(true);
        setSuccessMessage(`✅ Website processed! Scraped ${response.data.pages_processed} pages.`);
        setTimeout(() => setSuccessMessage(''), 5000);
        showError('Website processed successfully. You can now start chatting!', null, 'success');
        const newChatId = await createNewChat(response.data.website_url);
        setChatId(newChatId);
      } else {
        setShowProgress(false);
        setProgressMessage('');
        showError(response.data.error || 'Failed to process website', response.data.details);
      }
    } catch (error) {
      if (axios.isCancel(error)) {
        showError('Website processing cancelled by user.');
      } else {
        setShowProgress(false);
        setProgressMessage('');
        setLoading(false);
        showError('Failed to process website. Please check your network connection and try again.');
        console.error('Website processing error:', error);
      }
    } finally {
      setLoading(false);
      cancelRequestRef.current = null;
    }
  };

  // Update website URL input handling
  const handleWebsiteUrlChange = (e) => {
    const url = e.target.value;
    setWebsiteUrl(url);

    // Clear any existing errors when user starts typing
    if (error && error.message.includes('URL')) {
      setError(null);
    }
  };

  const getAuthConfig = () => user?.token ? { headers: { Authorization: `Bearer ${user.token}` } } : {};

  const handleMessageSubmit = async (e) => {
    e.preventDefault();
    if (!user?.id) {
      showError('Please login to continue');
      return;
    }
    if (!message) return;

    // If chatId is null, treat the message as a website URL submission
    if (!chatId) {
      setWebsiteUrl(message);
      setMessage('');
      handleWebsiteSubmit({ preventDefault: () => {} });
      return;
    }

    // Only allow valid MongoDB ObjectId as chatId
    if (!isValidObjectId(chatId)) {
      showError('Chat is not initialized. Please start a new chat.');
      return;
    }

    const userMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);
    setMessage('');
    setIsTyping(true);
    try {
      setLoading(true);
      // Get assistant response from Flask
      const response = await axios.post('http://localhost:5000/chat', {
        query: userMessage.content,
        userId: user.id,
        chatId
      });
      if (response.data.success) {
        const assistantMessage = { role: 'assistant', content: response.data.response };
        setMessages(prev => [...prev, assistantMessage]);

        // Get auth config with token
        const config = {
          headers: {
            'Authorization': `Bearer ${user.token}`,
            'Content-Type': 'application/json'
          }
        };

        // Append both user and assistant messages to Node backend chat
        await axios.post(`http://localhost:4000/api/chat/${chatId}/messages`, userMessage, config);
        await axios.post(`http://localhost:4000/api/chat/${chatId}/messages`, assistantMessage, config);
        fetchChatHistory();
      } else {
        showError(response.data.error, response.data.details);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to send message';
      const errorDetails = error.response?.data?.details;
      showError(errorMessage, errorDetails);
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  };

  const handleCopyMessage = (content) => {
    navigator.clipboard.writeText(content);
    showError('Message copied to clipboard');
  };

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleChatMenuClose = () => {
    setMenuAnchorEls(prev => ({ ...prev, [chatId]: null }));
  };

  const handleNewChat = () => {
    setShowNewChatDialog(true);
    setChatId(null);
    // Clear website URL field
    setWebsiteUrl('');
    // Don't show the error message about providing a URL in the chat area
    setMessages([]);
    setShowProgress(false);
    setProgressMessage('');

    // Ensure token is available for future requests
    if (user && user.id) {
      setSid(user.id);
    }

    handleChatMenuClose();
  };

  const handleClearHistory = async () => {
    try {
      await axios.delete('http://localhost:4000/api/chat/history');
      setChatHistory([]);
      handleChatMenuClose();
    } catch (error) {
      showError('Failed to clear history');
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('userId', user.id);

      const response = await axios.post('http://localhost:5000/upload-document', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });

      if (response.data.success) {
        setMessages([]);
        setCurrentPreview(response.data.preview);
        setPreviewTitle(file.name);
        setContentType(response.data.message.split(' ')[0]);
        setPreviewOpen(true);
        setSuccessMessage('✅ Document processed successfully. You can now start chatting!');
        setTimeout(() => setSuccessMessage(''), 5000);
        const newChatId = await createNewChat(file.name);
        setChatId(newChatId);
      } else {
        showError(response.data.error, response.data.details);
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error || 'Failed to upload document';
      const errorDetails = error.response?.data?.details;
      showError(errorMessage, errorDetails);
    } finally {
      setUploading(false);
    }
  };

  const renderMessage = (msg) => {
    const isCode = msg.content.includes('```');
    const isQuote = msg.content.startsWith('>');
    const isContentType = msg.content.startsWith('[');

    return (
      <Box sx={{ width: '100%' }}>
        {isContentType && (
          <Chip
            label={msg.content.split(']')[0].replace('[', '')}
            size="small"
            sx={{ mb: 1 }}
          />
        )}
        {isCode ? (
          <SyntaxHighlighter
            language="javascript"
            style={vscDarkPlus}
            customStyle={{ margin: 0, borderRadius: '4px' }}
          >
            {msg.content.replace(/```/g, '')}
          </SyntaxHighlighter>
        ) : isQuote ? (
          <Box sx={{ borderLeft: '4px solid #1976d2', pl: 2, py: 1 }}>
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </Box>
        ) : (
          <ReactMarkdown>{msg.content}</ReactMarkdown>
        )}
      </Box>
    );
  };

  // Create a new chat after website is processed
  const createNewChat = async (websiteUrl) => {
    try {
      // Ensure we have the token from user object
      if (!user || !user.token) {
        console.error('Cannot create chat: No authentication token available');
        showError('Authentication failed. Please try logging in again.');
        return null;
      }

      // Create config with authorization header
      const config = {
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        }
      };

      console.log('Creating new chat for website:', websiteUrl);
      console.log('Using auth token:', user.token.substring(0, 15) + '...');

      const response = await axios.post('http://localhost:4000/api/chat', { websiteUrl }, config);

      if (!response.data || !response.data._id) {
        console.error('Invalid response when creating chat:', response.data);
        showError('Failed to create chat: Invalid server response');
        return null;
      }

      console.log('Chat created successfully with ID:', response.data._id);
      setChatId(response.data._id);
      setMessages([{ role: 'assistant', content: '✅ Done! You can now ask questions about the website or Document.' }]);
      return response.data._id;
    } catch (error) {
      console.error('Create chat error:', error.response?.data || error.message);
      showError('Failed to create chat: ' + (error.response?.data?.message || error.message));
      return null;
    }
  };

  const removeWebsite = async (url) => {
    try {
      await axios.delete('http://localhost:4000/api/remove-website', { data: { url } });
      setPreviousWebsites(prev => prev.filter(site => site.url !== url));
      setSuccessMessage('Website removed successfully!');
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (error) {
      showError('Failed to remove website');
    }
  };

  const loadChat = async (id) => {
    try {
      setLoading(true); // Show loading state while switching chats
      setError(''); // Clear any previous errors
      setChatId(id);
      setShowNewChatDialog(false); // Close any open new chat dialog

      // Set proper authentication headers
      const config = {
        headers: {
          'Authorization': `Bearer ${user.token}`,
          'Content-Type': 'application/json'
        }
      };

      console.log('Loading chat with ID:', id);
      console.log('Using config:', config);
      const response = await axios.get(`http://localhost:4000/api/chat/${id}`, config);

      // Check if response exists and is valid
      if (!response || !response.data) {
        console.error('Invalid response:', response);
        throw new Error('No response data received from server');
      }

      console.log('Raw response:', response.data);

      if (response.data && response.data.messages) {
        console.log('Chat loaded successfully with', response.data.messages.length, 'messages');
        setMessages(response.data.messages);

        // ✅ FIX: Set the websiteUrl from the loaded chat data
        if (response.data.websiteUrl) {
          setWebsiteUrl(response.data.websiteUrl);
          console.log('Website context restored:', response.data.websiteUrl);
        }

        // If there are no messages yet, add a welcome message
        if (response.data.messages.length === 0 && response.data.websiteUrl) {
          setMessages([
            { role: 'assistant', content: `✅ Website loaded: ${response.data.websiteUrl}` },
            { role: 'assistant', content: 'You can now ask questions about this website.' }
          ]);
        } else if (response.data.websiteUrl && response.data.messages.length > 0) {
          // Chat already has messages and website context - ready to continue conversation
          console.log('Chat ready with website context:', response.data.websiteUrl);
        }
      } else {
        console.error('Invalid chat response:', response.data);
        setError('Failed to load chat: Invalid response data');
      }
    } catch (error) {
      console.error('Failed to load chat:', error);
      setError('Failed to load chat: ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false); // Hide loading state
    }
  };

  const handleMenuOpen = (event, chatId) => {
    setMenuAnchorEls(prev => ({ ...prev, [chatId]: event.currentTarget }));
  };

  const handleMenuClose = (chatId) => {
    setMenuAnchorEls(prev => ({ ...prev, [chatId]: null }));
  };

  const handleRenameOpen = (chat) => {
    if (!chat || !chat._id) return;
    setRenameValue(chat.websiteUrl || 'Chat');
    setRenameChatId(chat._id);
    setRenameDialogOpen(true);
    handleMenuClose(chat._id);
  };

  const handleRenameSave = async () => {
    if (!renameChatId) {
      setError('No chat selected for renaming');
      return;
    }
    try {
      await axios.put(`http://localhost:4000/api/chat/${renameChatId}/rename`, { newTitle: renameValue });
      setChatHistory(prev =>
        prev.map(chat =>
          chat._id === renameChatId ? { ...chat, websiteUrl: renameValue } : chat
        )
      );
      setRenameDialogOpen(false);
      setSuccessMessage('Chat renamed!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch {
      setError('Failed to rename chat');
    }
  };

  const handleRenameDialogClose = () => {
    setRenameDialogOpen(false);
    setRenameChatId(null);
  };

  const removeChat = async (chatIdToRemove) => {
    try {
      await axios.delete(`http://localhost:4000/api/chat/${chatIdToRemove}`);
      setChatHistory(prev => prev.filter(chat => chat._id !== chatIdToRemove));
      if (chatId === chatIdToRemove) {
        setChatId(null);
        setMessages([]);
      }
      setSuccessMessage('Chat removed successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setError('Failed to remove chat');
    }
  };

  if (authLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Please login to continue
          </Typography>
          <Button variant="contained" onClick={() => window.location.href = '/login'}>
            Go to Login
          </Button>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', height: '100vh', bgcolor: 'background.default' }}>
      {/* Sidebar */}
      <Box sx={{
        width: 300,
        bgcolor: '#23262F',
        color: '#fff',
        display: 'flex',
        flexDirection: 'column',
        borderRight: '1px solid #222',
        p: 2,
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 10
      }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 700, letterSpacing: 1 }}>Zentra</Typography>
        {/* Chat List and New Chat */}
        <Button
          variant="contained"
          color="primary"
          sx={{ mb: 2, borderRadius: 2 }}
          fullWidth
          onClick={handleNewChat}
        >
          New chat
        </Button>
        <Box sx={{
          flexGrow: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          direction: 'rtl', // Right to left to move scrollbar to left
          '& > *': { direction: 'ltr' }, // Reset content direction
          '&::-webkit-scrollbar': {
            width: '8px',
            backgroundColor: '#181A20',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: '#2A2D34',
            borderRadius: '6px',
            border: '2px solid #181A20',
            minHeight: '40px',
            '&:hover': {
              backgroundColor: '#343841'
            }
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: '#181A20',
            borderRadius: '6px'
          },
          scrollbarColor: '#2A2D34 #181A20',
          scrollbarWidth: 'auto',
        }}>
          {chatHistory.map((chat, idx) => (
            <Box key={idx} sx={{ position: 'relative', mb: 1 }}>
              <Button
                fullWidth
                sx={{
                  justifyContent: 'flex-start',
                  color: '#fff',
                  bgcolor: chatId === chat._id ? 'primary.main' : 'transparent',
                  borderRadius: 2,
                  textTransform: 'none',
                  alignItems: 'flex-start',
                  pr: 5
                }}
                onClick={() => loadChat(chat._id)}
              >
                <Box sx={{ textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', width: '100%' }}>
                  <Typography variant="body1" sx={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {chat.websiteUrl || 'Chat'}
                  </Typography>
                  <Typography variant="caption" color="grey.400">
                    {chat.updatedAt
                      ? new Date(chat.updatedAt).toLocaleString()
                      : chat.createdAt
                      ? new Date(chat.createdAt).toLocaleString()
                      : ''}
                  </Typography>
                </Box>
              </Button>
              <IconButton
                size="small"
                sx={{
                  position: 'absolute',
                  right: 4,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: '#fff',
                  bgcolor: 'rgba(255,255,255,0.08)',
                  '&:hover': { bgcolor: '#333', color: '#fff' }
                }}
                onClick={e => {
                  e.stopPropagation();
                  handleMenuOpen(e, chat._id);
                }}
              >
                <MoreVertIcon />
              </IconButton>
              <Menu
                anchorEl={menuAnchorEls[chat._id]}
                open={Boolean(menuAnchorEls[chat._id])}
                onClose={() => handleMenuClose(chat._id)}
                PaperProps={{
                  sx: {
                    bgcolor: '#23262F',
                    color: '#fff',
                    minWidth: 140,
                    borderRadius: 2,
                    boxShadow: 3,
                    mt: 1
                  }
                }}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
              >
                <MenuItem onClick={() => handleRenameOpen(chat)}>
                  <ListItemIcon>
                    <EditIcon fontSize="small" sx={{ color: '#fff' }} />
                  </ListItemIcon>
                  Rename
                </MenuItem>
                <MenuItem
                  onClick={async () => {
                    await removeChat(chat._id);
                    handleMenuClose(chat._id);
                  }}
                  sx={{ color: 'error.main' }}
                >
                  <ListItemIcon>
                    <DeleteIcon fontSize="small" sx={{ color: 'error.main' }} />
                  </ListItemIcon>
                  Delete
                </MenuItem>
              </Menu>
            </Box>
          ))}
          {/* Rename Dialog */}
          <Dialog open={renameDialogOpen} onClose={handleRenameDialogClose}>
            <DialogTitle>Rename Chat</DialogTitle>
            <DialogContent>
              <TextField
                autoFocus
                margin="dense"
                label="Chat Title"
                type="text"
                fullWidth
                value={renameValue}
                onChange={e => setRenameValue(e.target.value)}
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={handleRenameDialogClose}>Cancel</Button>
              <Button onClick={handleRenameSave} variant="contained" disabled={!renameChatId}>Save</Button>
            </DialogActions>
          </Dialog>
        </Box>
        {/* Bottom actions: Profile with dropdown menu */}
        <Box sx={{ mt: 2 }}>
          <Divider sx={{ bgcolor: '#333', mb: 2 }} />
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              px: 1
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <IconButton
                size="small"
                sx={{ color: '#fff' }}
                onClick={handleProfileMenuClick}
                aria-controls={profileMenuOpen ? 'profile-menu' : undefined}
                aria-haspopup="true"
                aria-expanded={profileMenuOpen ? 'true' : undefined}
              >
                <AccountCircleIcon />
              </IconButton>
              <Typography variant="body2" sx={{ ml: 1 }}>
                {user?.username || 'User'}
              </Typography>
            </Box>
            <IconButton
              size="small"
              sx={{ color: '#fff' }}
              onClick={logout}
              aria-label="logout"
            >
              <LogoutIcon />
            </IconButton>
          </Box>
          <Menu
            id="profile-menu"
            anchorEl={profileMenuAnchorEl}
            open={profileMenuOpen}
            onClose={handleProfileMenuClose}
            MenuListProps={{
              'aria-labelledby': 'profile-button',
            }}
            PaperProps={{
              sx: {
                bgcolor: '#23262F',
                color: '#fff',
                minWidth: 200,
                borderRadius: 2,
                boxShadow: 3,
                mt: 1
              }
            }}
            transformOrigin={{ horizontal: 'left', vertical: 'top' }}
            anchorOrigin={{ horizontal: 'left', vertical: 'bottom' }}
          >
            <MenuItem onClick={handleProfileMenuClose}>
              <ListItemIcon>
                <AccountCircleIcon fontSize="small" sx={{ color: '#fff' }} />
              </ListItemIcon>
              My Profile
            </MenuItem>
            <MenuItem onClick={handleProfileMenuClose}>
              <ListItemIcon>
                <SettingsIcon fontSize="small" sx={{ color: '#fff' }} />
              </ListItemIcon>
              Settings
            </MenuItem>
            <Divider sx={{ bgcolor: '#333' }} />
            <MenuItem onClick={logout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" sx={{ color: '#fff' }} />
              </ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Box>
      {/* Main Chat Area or Placeholder */}
      <Box sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        position: 'fixed',
        left: 300,
        right: 350,
        top: 0,
        bottom: 0,
        overflow: 'hidden'
      }}>
        {showNewChatDialog
          ? <Box sx={{ flexGrow: 1 }} />
          : (
            <Box sx={{
              display: 'flex',
              flexDirection: 'column',
              width: '100%',
              height: '100vh',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative'
            }}>
              {/* Chat messages */}
              <Box
                sx={{
                  flex: 1,
                  overflowY: 'auto',
                  width: '100%',
                  maxWidth: '800px',
                  height: 'calc(100vh - 100px)',
                  display: 'flex',
                  flexDirection: 'column',
                  bgcolor: 'background.default',
                  '&::-webkit-scrollbar': {
                    width: '12px',
                    backgroundColor: '#181A20',
                  },
                  '&::-webkit-scrollbar-thumb': {
                    backgroundColor: '#2A2D34',
                    borderRadius: '6px',
                    border: '2px solid #181A20',
                    minHeight: '40px',
                    '&:hover': {
                      backgroundColor: '#343841'
                    }
                  },
                  '&::-webkit-scrollbar-track': {
                    backgroundColor: '#181A20',
                    borderRadius: '6px'
                  },
                  scrollbarColor: '#2A2D34 #181A20',
                  scrollbarWidth: 'auto',

                }}
              >
                <Box sx={{ p: 3, width: '100%', maxWidth: '800px', mx: 'auto', flex: 1 }}>
                  {/* Website Context Indicator */}
                  {websiteUrl && chatId && (
                    <Box sx={{
                      mb: 2,
                      p: 2,
                      bgcolor: 'rgba(90, 107, 255, 0.1)',
                      border: '1px solid rgba(90, 107, 255, 0.3)',
                      borderRadius: 2,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1
                    }}>
                      <WebIcon sx={{ color: '#5A6BFF', fontSize: 20 }} />
                      <Typography variant="body2" sx={{ color: '#5A6BFF', fontWeight: 500 }}>
                        ✅ Website loaded: {websiteUrl}
                      </Typography>
                      <Chip
                        label="You can now ask questions about this website"
                        size="small"
                        sx={{
                          bgcolor: 'rgba(90, 107, 255, 0.2)',
                          color: '#5A6BFF',
                          fontSize: '0.75rem',
                          height: 24
                        }}
                      />
                    </Box>
                  )}

                  {messages.map((msg, idx) => (
                    <Box
                      key={idx}
                      sx={{
                        mb: 2,
                        display: 'flex',
                        justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                        alignItems: 'flex-end',
                        width: '100%',
                      }}
                    >
                      {/* Bot avatar for bot messages */}
                      {msg.role !== 'user' && (
                        <Box sx={{ mr: 1, display: 'flex', alignItems: 'flex-end' }}>
                          <img
                            src={BotLogo}
                            alt="Bot"
                            style={{
                              width: 36,
                              height: 36,
                              borderRadius: '50%',
                              background: 'rgba(100, 108, 255, 0.08)',
                              border: '1px solid #5A6BFF22',
                              padding: 4,
                              boxSizing: 'border-box',
                              objectFit: 'cover',
                            }}
                          />
                        </Box>
                      )}
                      <Box
                        sx={{
                          bgcolor: msg.role === 'user' ? '#23262F' : 'background.default',
                          color: '#fff',
                          px: 2,
                          py: 1.5,
                          borderRadius: 2,
                          maxWidth: '80%',
                          boxShadow: 0,
                          fontSize: '1rem',
                          wordBreak: 'break-word',
                          textAlign: 'left',
                          mx: msg.role === 'user' ? 2 : 0,
                          display: 'flex',
                          alignItems: 'center',
                          border: msg.role !== 'user' ? '1px solid #23262F' : 'none',
                          '& .blur-dots': {
                            color: 'rgba(255, 255, 255, 0.5)',
                            filter: 'blur(1px)',
                            display: 'inline',
                            letterSpacing: '2px',
                          }
                        }}
                      >
                        <Box
                          sx={{ whiteSpace: 'pre-line' }}
                          dangerouslySetInnerHTML={{
                            __html: msg.role !== 'user'
                              ? msg.content.replace(/^[]?website[\]]?[:\s-]*/i, '').replace(/\.{3}/g, '<span class="blur-dots">...</span>')
                              : msg.content.replace(/\.{3}/g, '<span class="blur-dots">...</span>')
                          }}
                        />
                      </Box>
                    </Box>
                  ))}
                  {/* Typing animation for bot */}
                  {isTyping && messages.length > 0 && messages[messages.length - 1].role === 'user' && (
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                      <Box sx={{ mr: 0.5, display: 'flex', alignItems: 'center' }}>
                        <img
                          src={BotLogo}
                          alt="Bot"
                          style={{
                            width: 36,
                            height: 36,
                            borderRadius: '50%',
                            background: 'rgba(100, 108, 255, 0.08)',
                            border: '1px solid #5A6BFF22',
                            padding: 4,
                            boxSizing: 'border-box',
                            objectFit: 'cover',
                          }}
                        />
                      </Box>
                      <Box
                        sx={{
                          bgcolor: 'background.default',
                          color: '#fff',
                          px: 2,
                          py: 1.5,
                          borderRadius: 2,
                          maxWidth: '70%',
                          boxShadow: 0,
                          fontSize: '1rem',
                          wordBreak: 'break-word',
                          textAlign: 'left',
                          mx: 2,
                          display: 'flex',
                          alignItems: 'center',
                        }}
                      >
                        <TypingDots />
                      </Box>
                    </Box>
                  )}
                  <div ref={messagesEndRef} />
                </Box>
              </Box>
              {/* Chat input */}
              <Box
                component="form"
                onSubmit={handleMessageSubmit}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  bgcolor: '#23262F',
                  borderRadius: 2,
                  p: 1,
                  mt: 2,
                  width: '100%',
                  maxWidth: 700,
                  mb: 3,
                  ml: 'auto',
                  mr: 'auto',
                }}
              >
                <TextField
                  fullWidth
                  variant="standard"
                  placeholder="Type your message..."
                  value={message}
                  onChange={e => setMessage(e.target.value)}
                  InputProps={{
                    disableUnderline: true,
                    sx: { color: '#fff', px: 1 }
                  }}
                  sx={{ bgcolor: 'transparent' }}
                />
                <IconButton type="submit" color="primary">
                  <SendIcon />
                </IconButton>
              </Box>
            </Box>
          )}
      </Box>
      {/* Right Panel */}
      <Box sx={{
        width: 300,
        bgcolor: '#23262F',
        color: '#fff',
        display: 'flex',
        flexDirection: 'column',
        borderLeft: '1px solid #222',
        p: 2,
        height: '100vh',
        position: 'fixed',
        right: 0,
        top: 0,
        zIndex: 10,
        overflow: 'hidden'
      }}>
        {/* Top Half: Load Previous Websites */}
        <Box sx={{ height: '50%', display: 'flex', flexDirection: 'column', mb: 2 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Load Previous Website</Typography>
          <Button
            variant="contained"
            color="primary"
            fullWidth
            sx={{ mb: 2, borderRadius: 2 }}
            onClick={fetchPreviousWebsites}
          >
            REFRESH LIST
          </Button>
          <Box sx={{
            flexGrow: 1,
            overflowY: 'auto',
            overflowX: 'hidden',
            maxHeight: 'calc(50vh - 130px)',
            direction: 'rtl', // Right to left to move scrollbar to left
            '& > *': { direction: 'ltr' }, // Reset content direction
            '&::-webkit-scrollbar': {
              width: '8px',
              backgroundColor: '#181A20',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: '#2A2D34',
              borderRadius: '6px',
              border: '2px solid #181A20',
              minHeight: '40px',
              '&:hover': {
                backgroundColor: '#343841'
              }
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: '#181A20',
              borderRadius: '6px'
            },
            scrollbarColor: '#2A2D34 #181A20',
            scrollbarWidth: 'thin',
          }}>
            {previousWebsites.length === 0 && (
              <Typography variant="body2" color="grey.400">No previous websites.</Typography>
            )}
            {previousWebsites.map((website, idx) => (
              <Box
                key={idx}
                sx={{
                  bgcolor: '#181A20',
                  borderRadius: 2,
                  p: 1,
                  mb: 1,
                  display: 'flex',
                  alignItems: 'center',
                  position: 'relative',
                  overflow: 'hidden',
                  '&:hover': {
                    bgcolor: '#1F222A',
                    '& .website-url': {
                      transform: 'translateX(-80px)', // Reduced distance - move text left when hovered
                      transition: 'transform 0.6s ease-in-out' // Slower animation - reduced speed
                    },
                    '& .action-buttons': {
                      opacity: 1,
                      visibility: 'visible'
                    }
                  }
                }}
              >
                <Box
                  className="website-url"
                  sx={{
                    flex: 1,
                    transition: 'transform 0.6s ease-in-out', // Slower animation - reduced speed
                    pr: 2
                  }}
                >
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: 500,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      maxWidth: '200px'
                    }}
                  >
                    {website.url}
                  </Typography>
                  <Typography variant="caption" color="grey.400">
                    {website.timestamp ? new Date(website.timestamp).toLocaleString() : 'Timestamp not available'}
                  </Typography>
                </Box>
                <Box
                  className="action-buttons"
                  sx={{
                    position: 'absolute',
                    right: 8,
                    top: '50%',
                    transform: 'translateY(-50%)',
                    opacity: 1, // Always visible
                    visibility: 'visible',
                    display: 'flex',
                    flexDirection: 'column', // Stack buttons vertically
                    gap: 0.3, // Reduced gap for stacked layout
                    bgcolor: '#181A20',
                    borderRadius: 1,
                    p: 0.4 // Slightly reduced padding
                  }}
                >
                  <Button
                    size="small"
                    variant="contained"
                    color="primary"
                    sx={{
                      minWidth: '60px', // Increased width for stacked layout
                      fontSize: '0.65rem',
                      py: 0.3, // Reduced padding for compact stacked buttons
                      px: 1
                    }}
                    onClick={() => handleWebsiteSelect(website)}
                  >
                    LOAD
                  </Button>
                  <Button
                    size="small"
                    variant="contained"
                    color="error"
                    sx={{
                      minWidth: '60px', // Consistent width
                      fontSize: '0.65rem',
                      py: 0.3, // Reduced padding for compact stacked buttons
                      px: 1
                    }}
                    onClick={() => removeWebsite(website.url)}
                  >
                    REMOVE
                  </Button>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
        <Divider sx={{ my: 2, bgcolor: '#333' }} />
        {/* Bottom Half: Upload Document */}
        <Box sx={{ height: '45%', display: 'flex', flexDirection: 'column' }}>
          <Typography variant="h6" sx={{ mb: 1 }}>Upload Document</Typography>
          <Button
            variant="contained"
            color="secondary"
            fullWidth
            sx={{ mb: 2, borderRadius: 2 }}
            onClick={() => fileInputRef.current?.click()}
          >
            UPLOAD DOCUMENT
          </Button>
          <input
            type="file"
            accept=".pdf,.docx,.txt,.md,.csv,.json"
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            ref={fileInputRef}
          />

          {/* List of uploaded documents - similar to previous websites */}
          <Box sx={{
            flexGrow: 1,
            overflowY: 'auto',
            overflowX: 'hidden',
            maxHeight: 'calc(45vh - 130px)',
            '&::-webkit-scrollbar': {
              width: '8px',
              backgroundColor: '#181A20',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: '#2A2D34',
              borderRadius: '6px',
              border: '2px solid #181A20',
              minHeight: '40px',
              '&:hover': {
                backgroundColor: '#343841'
              }
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: '#181A20',
              borderRadius: '6px'
            },
            scrollbarColor: '#2A2D34 #181A20',
            scrollbarWidth: 'thin',
          }}>
            {chatHistory.filter(chat => chat.websiteUrl && (
              chat.websiteUrl.endsWith('.pdf') ||
              chat.websiteUrl.endsWith('.docx') ||
              chat.websiteUrl.endsWith('.txt') ||
              chat.websiteUrl.endsWith('.md') ||
              chat.websiteUrl.endsWith('.csv') ||
              chat.websiteUrl.endsWith('.json')
            )).length === 0 && (
              <Typography variant="body2" color="grey.400" sx={{ textAlign: 'center', mt: 2 }}>
                No documents uploaded yet.
              </Typography>
            )}

            {chatHistory
              .filter(chat => chat.websiteUrl && (
                chat.websiteUrl.endsWith('.pdf') ||
                chat.websiteUrl.endsWith('.docx') ||
                chat.websiteUrl.endsWith('.txt') ||
                chat.websiteUrl.endsWith('.md') ||
                chat.websiteUrl.endsWith('.csv') ||
                chat.websiteUrl.endsWith('.json')
              ))
              .map((document, idx) => (
                <Box
                  key={idx}
                  sx={{
                    bgcolor: '#181A20',
                    borderRadius: 2,
                    p: 1,
                    mb: 1,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between'
                  }}
                >
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {document.websiteUrl}
                    </Typography>
                    <Typography variant="caption" color="grey.400">
                      {document.updatedAt
                        ? new Date(document.updatedAt).toLocaleString()
                        : document.createdAt
                          ? new Date(document.createdAt).toLocaleString()
                          : ''}
                    </Typography>
                  </Box>
                  <Box>
                    <Button
                      size="small"
                      color="primary"
                      sx={{ mr: 1 }}
                      onClick={() => loadChat(document._id)}
                    >
                      OPEN
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      onClick={() => removeChat(document._id)}
                    >
                      REMOVE
                    </Button>
                  </Box>
                </Box>
            ))}
          </Box>
        </Box>
      </Box>

      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {previewTitle || 'Content Preview'}
          {contentType && (
            <Chip
              label={contentType}
              size="small"
              sx={{ ml: 2 }}
            />
          )}
        </DialogTitle>
        <DialogContent
          sx={{
            bgcolor: '#23262F',
            color: '#fff'
          }}
        >
          <Box
            sx={{
              bgcolor: '#2A2D34',
              color: '#fff',
              p: 2,
              borderRadius: 1,
              fontFamily: 'monospace',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              maxHeight: '60vh',
              overflow: 'auto'
            }}
          >
            {currentPreview}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={showWebsiteDialog}
        onClose={() => setShowWebsiteDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Choose Website</DialogTitle>
        <DialogContent>
          {(websiteUrl || progressMessage) && (
            <Box sx={{ mb: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
              <Typography variant="subtitle1" color="primary">
                {progressMessage
                  ? `Processing: ${websiteUrl || 'N/A'}`
                  : `Current Website: ${websiteUrl}`}
              </Typography>
            </Box>
          )}
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Previous Websites
            </Typography>
            <List>
              {previousWebsites.map((website, index) => (
                <ListItem
                  key={index}
                  secondaryAction={
                    <Button
                      color="error"
                      size="small"
                      onClick={async (e) => {
                        e.stopPropagation();
                        await removeWebsite(website.url);
                      }}
                    >
                      Remove
                    </Button>
                  }
                  button
                  onClick={() => handleWebsiteSelect(website)}
                >
                  <ListItemText
                    primary={website.url}
                    secondary={website.timestamp ? `Last processed: ${new Date(website.timestamp).toLocaleString()}` : 'Timestamp not available'}
                  />
                </ListItem>
              ))}
            </List>
            <Divider sx={{ my: 2 }} />
            <Button
              fullWidth
              variant="contained"
              onClick={() => {
                setShowWebsiteDialog(false);
                setWebsiteUrl('');
              }}
            >
              Process New Website
            </Button>
          </Box>
        </DialogContent>
      </Dialog>

      <Snackbar
        open={!!error}
        autoHideDuration={5000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setError(null)}
          severity={error?.severity || 'error'}
          sx={{ width: '100%' }}
        >
          <Typography variant="subtitle2">{error?.message}</Typography>
          {error?.details && (
            <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
              {error.details}
            </Typography>
          )}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!successMessage}
        autoHideDuration={5000}
        onClose={() => setSuccessMessage('')}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        TransitionComponent={Fade}
      >
        <Alert onClose={() => setSuccessMessage('')} severity="success" sx={{ width: '100%' }}>
          <Typography variant="subtitle2">{successMessage}</Typography>
        </Alert>
      </Snackbar>

      {scrapingLink && (
        <Box sx={{ p: 2, textAlign: 'center' }}>
          <Typography variant="subtitle1" color="primary">
            Scraping: {scrapingLink}
          </Typography>
        </Box>
      )}

      <Dialog
        open={showProgress}
        onClose={() => {}}
        maxWidth="xs"
        fullWidth
        PaperProps={{
          sx: { textAlign: 'center', p: 3, borderRadius: 3 }
        }}
      >
        <DialogTitle sx={{ pb: 0 }}>Processing...</DialogTitle>
        <DialogContent>
          <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', my: 2 }}>
            <LinearProgress color="primary" sx={{ width: '100%', mb: 2 }} />
            <Typography color="primary" variant="body1" sx={{ mb: 2 }}>{progressMessage}</Typography>
            <Button
              variant="outlined"
              color="error"
              onClick={async () => {
                setShowProgress(false);
                setProgressMessage('');
                if (cancelRequestRef.current) {
                  cancelRequestRef.current.cancel();
                }
                // Send abort request to Flask backend
                try {
                  await axios.post('http://localhost:5000/abort-processing', { user_id: sid });
                } catch (err) {
                  console.error('Failed to send abort signal:', err);
                }
              }}
            >
              Abort
            </Button>
          </Box>
        </DialogContent>
      </Dialog>

      {/* New Chat Dialog */}
      <Dialog
        open={showNewChatDialog}
        onClose={() => setShowNewChatDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Start New Chat</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Enter Website URL
            </Typography>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="https://example.com"
              value={websiteUrl}
              onChange={handleWebsiteUrlChange}
              sx={{ mb: 3 }}
            />
            <Typography variant="h6" gutterBottom>
              Or Upload Document
            </Typography>
            <Button
              variant="contained"
              color="secondary"
              fullWidth
              sx={{ mb: 2, borderRadius: 2 }}
              onClick={() => fileInputRef.current?.click()}
            >
              Upload Document
            </Button>
            <input
              type="file"
              accept=".pdf,.docx,.txt,.md,.csv,.json"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              ref={fileInputRef}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowNewChatDialog(false)}>Cancel</Button>
          <Button
            onClick={() => {
              if (websiteUrl) {
                handleWebsiteSubmit({ preventDefault: () => {} });
              }
              setShowNewChatDialog(false);
            }}
            variant="contained"
            disabled={!websiteUrl}
          >
            Start Chat
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
};

export default Chat;