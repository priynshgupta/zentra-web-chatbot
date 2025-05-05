const express = require('express');
const router = express.Router();
const Chat = require('../models/Chat');
const auth = require('../middleware/auth');

// Get all chats for a user
router.get('/', auth, async (req, res) => {
  try {
    const chats = await Chat.find({ user: req.user.userId })
      .sort({ updatedAt: -1 });
    res.json(chats);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching chats', error: error.message });
  }
});

// Get a specific chat
router.get('/:chatId', auth, async (req, res) => {
  try {
    const chat = await Chat.findOne({
      _id: req.params.chatId,
      user: req.user.userId
    });

    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }

    res.json(chat);
  } catch (error) {
    res.status(500).json({ message: 'Error fetching chat', error: error.message });
  }
});

// Create a new chat
router.post('/', auth, async (req, res) => {
  try {
    const { websiteUrl } = req.body;
    if (!websiteUrl) {
      return res.status(400).json({ success: false, message: 'websiteUrl is required' });
    }
    const chat = new Chat({
      user: req.user.userId,
      websiteUrl,
      messages: []
    });
    await chat.save();
    res.status(201).json({ success: true, ...chat.toObject(), _id: chat._id });
  } catch (error) {
    res.status(500).json({ success: false, message: 'Error creating chat', error: error.message });
  }
});

// Add a message to a chat
router.post('/:chatId/messages', auth, async (req, res) => {
  try {
    const { role, content } = req.body;
    if (!role || !content) {
      return res.status(400).json({ success: false, message: 'role and content are required' });
    }
    const chat = await Chat.findOne({
      _id: req.params.chatId,
      user: req.user.userId
    });
    if (!chat) {
      console.error('Chat not found for chatId:', req.params.chatId, 'and user:', req.user.userId);
      return res.status(404).json({ success: false, message: 'Chat not found' });
    }
    chat.messages.push({ role, content });
    await chat.save();
    console.log('Message saved to chat:', chat._id, 'Role:', role, 'Content:', content);
    res.json({ success: true, chat });
  } catch (error) {
    console.error('Error saving chat message:', error);
    res.status(500).json({ success: false, message: 'Error adding message', error: error.message });
  }
});

// Clear all chat history for the authenticated user
router.delete('/history', auth, async (req, res) => {
  try {
    await Chat.deleteMany({ user: req.user.userId });
    res.json({ message: 'Chat history cleared' });
  } catch (error) {
    res.status(500).json({ message: 'Error clearing chat history', error: error.message });
  }
});

// Delete a chat
router.delete('/:chatId', auth, async (req, res) => {
  try {
    const chat = await Chat.findOneAndDelete({
      _id: req.params.chatId,
      user: req.user.userId
    });

    if (!chat) {
      return res.status(404).json({ message: 'Chat not found' });
    }

    res.json({ message: 'Chat deleted successfully' });
  } catch (error) {
    res.status(500).json({ message: 'Error deleting chat', error: error.message });
  }
});

// PUT /api/chat/:chatId/rename
router.put('/:chatId/rename', auth, async (req, res) => {
  try {
    const { newTitle } = req.body;
    const { chatId } = req.params;
    // Validate chatId
    if (!chatId || chatId === "null") {
      return res.status(400).json({ message: 'Invalid chat ID' });
    }
    // Find and update only if the chat belongs to the user
    const chat = await Chat.findOneAndUpdate(
      { _id: chatId, user: req.user.userId },
      { websiteUrl: newTitle },
      { new: true }
    );
    if (!chat) return res.status(404).json({ message: 'Chat not found' });
    res.json({ success: true, chat });
  } catch (error) {
    res.status(500).json({ message: 'Error renaming chat', error: error.message });
  }
});

module.exports = router;