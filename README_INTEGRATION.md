# Oceanographic Data Chatbot - Full Stack Integration

This project integrates your existing Python oceanographic data query script with a beautiful, modern React frontend.

## 🌊 Features

- **Natural Language to SQL**: Convert plain English queries to SQL using Gemini AI
- **Real-time Chat Interface**: Beautiful, responsive chatbot UI
- **Data Visualization**: Interactive tables with search, pagination, and export
- **Vector Search**: Context-aware queries using Qdrant embeddings
- **Professional Design**: Ocean-themed design system with smooth animations

## 🚀 Quick Start

### Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the FastAPI server:**
   
   **Windows:**
   ```bash
   start.bat
   ```
   
   **Linux/Mac:**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
   
   **Or manually:**
   ```bash
   python main.py
   ```

   The backend will start on `http://localhost:8000`

### Frontend Setup

1. **Install frontend dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

   The frontend will start on `http://localhost:8080`

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DB_HOST=ep-purple-hall-a1c79c5s-pooler.ap-southeast-1.aws.neon.tech
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=your_db_password
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_api_key
```

### Database Schema

The system expects these tables:
- `public.profiles` - Profile metadata (platform_number, latitude, longitude, etc.)
- `public.measurements` - Measurement data (temperature, salinity, pressure, etc.)

## 🎯 Usage Examples

### Natural Language Queries

- "Show me temperature profiles from platform 5906468"
- "Find salinity measurements in the Pacific Ocean from 2023"
- "Get recent profiles near latitude 35, longitude -120"
- "Show me data from the Mediterranean Sea"

### API Endpoints

- `GET /` - API status and information
- `GET /health` - System health check
- `POST /query` - Process natural language queries
- `GET /conversations/{id}` - Retrieve conversation history

## 🏗️ Architecture

### Backend Components

- **FastAPI Server** (`main.py`) - REST API wrapper around your original script
- **Gemini AI Integration** - Natural language processing
- **PostgreSQL Connection** - Neon database access
- **Qdrant Vector Search** - Context-aware query enhancement
- **SentenceTransformers** - Text embeddings

### Frontend Components

- **ChatInterface** - Main chat component
- **ChatMessage** - Individual message rendering with markdown support
- **ChatHeader** - Header with status indicators and controls
- **DataTable** - Interactive data display with pagination and export

### Design System

- **Ocean Theme** - Professional blue/teal color palette
- **Responsive Layout** - Mobile-first design
- **Smooth Animations** - CSS transitions and keyframes
- **Component Variants** - Consistent styling across components

## 🛠️ Development

### Backend Development

The backend is a FastAPI wrapper around your existing script with these enhancements:

- **Async Support** - Non-blocking request handling
- **Error Handling** - Graceful error responses
- **CORS Configuration** - Frontend integration support
- **Conversation Memory** - Chat history tracking
- **Health Monitoring** - System status endpoints

### Frontend Development

Built with modern React patterns:

- **TypeScript** - Type safety and better DX
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality component library
- **Custom Hooks** - Reusable logic
- **Responsive Design** - Works on all screen sizes

## 📊 Data Features

### Query Capabilities

- **Filter by Platform** - Specific float identifiers
- **Geographic Filtering** - Latitude/longitude ranges
- **Temporal Queries** - Date and time ranges
- **Parameter Selection** - Temperature, salinity, pressure
- **Quality Control** - QC flag filtering

### Data Display

- **Interactive Tables** - Sort, search, paginate
- **CSV Export** - Download query results
- **Column Visibility** - Show/hide columns
- **Data Formatting** - Appropriate number formatting
- **Real-time Updates** - Live query results

## 🔒 Security

- **Input Validation** - SQL injection prevention
- **Query Limits** - Prevent large data dumps
- **Error Sanitization** - Safe error messages
- **CORS Configuration** - Controlled cross-origin access

## 🚀 Deployment

### Backend Deployment

1. **Docker Option:**
   ```dockerfile
   FROM python:3.9-slim
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY main.py .
   CMD ["python", "main.py"]
   ```

2. **Cloud Deployment** - Deploy to Heroku, Railway, or similar

### Frontend Deployment

1. **Build for production:**
   ```bash
   npm run build
   ```

2. **Deploy to Netlify, Vercel, or similar**

## 🐛 Troubleshooting

### Common Issues

1. **Backend not starting:**
   - Check Python version (3.8+ required)
   - Verify all dependencies installed
   - Check API keys and database credentials

2. **Frontend connection errors:**
   - Ensure backend is running on port 8000
   - Check CORS configuration
   - Verify API endpoints are accessible

3. **Database connection issues:**
   - Verify Neon database credentials
   - Check network connectivity
   - Ensure SSL mode is configured

4. **Qdrant connection issues:**
   - Verify Qdrant URL and API key
   - Check vector collection names
   - Ensure embedding model is loaded

## 📝 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project integrates with your existing oceanographic data analysis script. Please ensure compliance with your data usage policies and API terms of service.