# FloatChat Demo 🚢💬

Welcome to **FloatChat Demo** – an oceanographic data chatbot platform that lets you explore, query, and visualize ocean data with the power of AI and modern web technologies.

---

## 🌊 What is FloatChat?

FloatChat is a full-stack application designed for interactive exploration of oceanographic datasets. Ask natural language questions, get instant answers, and visualize data – all in one place. Powered by FastAPI, NeonDB, Qdrant, Google Gemini, and a modern React frontend.

---

## 🏗️ Project Structure

```
app/
│
├── backend/           # FastAPI backend, database, embeddings, API
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── start.bat / start.sh
│
├── public/            # Static assets (favicon, robots.txt, etc.)
│
├── src/               # React frontend source code
│   ├── components/    # UI components (Chat, DataTable, etc.)
│   ├── hooks/         # Custom React hooks
│   ├── lib/           # Utility functions
│   ├── pages/         # App pages (Index, NotFound)
│   └── App.tsx        # Main app entry
│
├── index.html         # Frontend entry point
├── dashboard.html     # Optional dashboard
├── package.json       # Frontend dependencies
├── tailwind.config.ts # Tailwind CSS config
└── README.md          # You're reading it!
```

---

## 🚀 Getting Started

### 1. **Clone the Repo**

```bash
git clone https://github.com/yourusername/floatchat-demo.git
cd floatchat-demo/app
```

### 2. **Backend Setup**

- Install Python dependencies:
  ```bash
  pip install -r backend/requirements.txt
  ```
- Copy `.env.example` to `.env` and fill in your API/database keys.

- Start the FastAPI backend:
  ```bash
  cd backend
  uvicorn main:app --reload
  ```
  Or use `start.bat` / `start.sh` for quick launch.

### 3. **Frontend Setup**

- Install Node.js dependencies:
  ```bash
  npm install
  ```
- Start the frontend dev server:
  ```bash
  npm run dev
  ```
- Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧠 Features

- **Natural Language to SQL**: Ask questions, get SQL queries and answers.
- **Ocean Data Visualization**: View profiles, measurements, and more.
- **Embeddings & Search**: Semantic search powered by Qdrant and Sentence Transformers.
- **Conversational UI**: Modern chat interface with React + Tailwind.
- **Multi-platform**: Works on Windows, Mac, Linux.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI, NeonDB (PostgreSQL), Qdrant, Google Gemini, Sentence Transformers
- **Frontend**: React, TypeScript, Vite, Tailwind CSS
- **Dev Tools**: Bun, ESLint, PostCSS

---

## 📦 Environment Variables

Create a `.env` file in `backend/` with:

```
GEMINI_API_KEY=your_google_gemini_api_key
QDRANT_API_KEY=your_qdrant_api_key
DB_HOST=your_neondb_host
DB_USER=your_neondb_user
DB_PASSWORD=your_neondb_password
DB_NAME=your_neondb_dbname
```

---

## 🧪 Testing

- Backend: Use `pytest` for Python tests.
- Frontend: Use `npm test` or your favorite React testing library.

---

## 🤝 Contributing

Pull requests, issues, and suggestions are welcome!  
See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📚 Documentation

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [NeonDB Docs](https://neon.tech/docs)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Google Gemini](https://ai.google.dev/)
- [React](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

## 🏄‍♂️ License

MIT License.  
See [LICENSE](LICENSE) for details.

---

**Dive in, ask questions, and let FloatChat help you explore the depths of your data!**