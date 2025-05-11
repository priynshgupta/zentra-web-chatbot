# Zentra Chatbot

![Zentra Chatbot](Screenshots/Chat%20with%20BOB.png)
![Login Page](Screenshots/Login%Page.png)
![Register Page](Screenshots/Register%Page.png)

## About

Zentra Chatbot is an advanced AI-powered conversation tool that transforms how users interact with website content. Unlike basic chatbots that rely on pre-defined responses, Zentra processes and understands the entire content of any website or document, allowing users to ask natural language questions and receive accurate, context-aware answers.

### Why Zentra Chatbot?

Traditional chatbots in banking, education, and e-commerce often frustrate users with limited, scripted responses. Zentra Chatbot solves this by:

- **Understanding entire website contexts**: Processes all pages and content
- **Answering complex queries**: Provides specific information from deep within website content
- **Supporting multiple document types**: Works with PDFs, Word docs, text files, and more
- **Learning from interactions**: Improves responses over time

## Key Features

- **Intelligent Website Processing**:
  - Automatically adapts to different website types (banking, education, e-commerce)
  - Handles JavaScript-heavy websites with dynamic content
  - Processes websites with proper depth control to capture the most relevant information

- **Document Intelligence**:
  - Upload and chat with PDF, DOCX, TXT, MD, CSV, and JSON documents
  - Maintains context across multiple questions about the same document

- **Seamless User Experience**:
  - Modern, responsive interface with real-time responses
  - Chat history management for revisiting previous conversations
  - Dark mode UI for comfortable viewing

- **Enterprise-Ready**:
  - User authentication and session management
  - Secure data handling
  - Conversation history storage

## Technical Stack

- **Frontend**: React with Material UI
- **Backend**: Node.js with Express
- **AI/ML**: Python with LangChain and vector embeddings
- **Database**: MongoDB for user data and chat history
- **Vector Database**: ChromaDB for efficient semantic search

## Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- MongoDB (running locally or a connection string)
- 8GB+ RAM recommended for processing larger websites
- Modern web browser (Chrome, Firefox, Edge, Safari)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/zentrachatbot.git
cd zentrachatbot
```

### 2. Install Dependencies

The project has three main components: Root, Backend, and Frontend.

```bash
# Install all dependencies (Node.js and Python)
npm run install:all

# Or install manually:
# Root dependencies
npm install

# Backend dependencies
cd backend
npm install
cd ..

# Frontend dependencies
cd frontend
npm install
cd ..

# Python dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

- Create a `.env` file in the `backend` directory:

```
MONGODB_URI=mongodb://localhost:27017/zentrachatbot
JWT_SECRET=your_jwt_secret_here
PORT=4000
```

- If using AI models requiring API keys, add them to your environment:

```
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
```

### 4. Set Up MongoDB

Make sure MongoDB is running on your system. If you're using a cloud MongoDB instance, update the MONGODB_URI in your `.env` file.

### 5. Start the Application

```bash
# Start all services with a single command
npm start

# Or start services individually:
# Start frontend
cd frontend
npm start

# Start backend
cd backend
npm start

# Start Python service
python main.py
```

The application will be available at:
- React frontend: http://localhost:3000
- Node.js backend: http://localhost:4000
- Python backend: http://localhost:5000

## Usage Guide

### 1. Login/Register
First, create an account or log in to access the chatbot features.

### 2. Chat with a Website
- Click "New Chat" in the sidebar
- Enter a website URL (e.g., a banking website)
- Wait for processing to complete
- Start asking questions about the website content

### 3. Upload and Chat with Documents
- Click "Upload Document" in the right sidebar
- Select a document file (PDF, DOCX, TXT, etc.)
- Wait for processing to complete
- Start asking questions about the document content

### 4. Manage Conversations
- Access previous chats from the left sidebar
- Rename or delete chats as needed
- View document and website history in the right sidebar

## Project Structure

```
zentrachatbot/
├── app/                  # Python AI service components
│   ├── chatbot.py        # Core chatbot functionality
│   ├── scraper.py        # Website processing functions
│   └── vector_store.py   # Vector database interaction
├── backend/              # Node.js backend
│   ├── middleware/       # Authentication middleware
│   ├── models/           # Database models
│   ├── routes/           # API endpoints
│   └── server.js         # Main server file
├── frontend/             # React frontend
│   ├── public/           # Static assets
│   └── src/              # React components and logic
├── chroma/               # Vector database files
├── uploads/              # Uploaded documents storage
├── main.py               # Python service entry point
├── package.json          # Root package configuration
└── README.md             # This file
```

## Deployment

### Local Deployment
Follow the setup instructions above to run locally.

### Cloud Deployment Options

- **Frontend**: Deploy to Netlify, Vercel, or AWS Amplify
- **Backend**: Deploy to Heroku, AWS Elastic Beanstalk, or Google Cloud Run
- **Python Service**: Deploy to AWS Lambda or Google Cloud Functions
- **Database**: MongoDB Atlas for cloud-hosted database

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- LangChain framework for AI capabilities
- Material UI for frontend components
- All contributors and stakeholders of the project

---
*Last updated: May 5, 2025*
