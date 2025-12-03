# Playwright Automations Frontend

A Next.js frontend application for the Playwright Automations FastAPI backend.

## Features

- **Authentication**: Login and registration with JWT token management
- **Notebook Management**: Create, list, and delete NotebookLM notebooks
- **Source Management**: Upload, list, delete, rename, and review sources
- **Chat Interface**: Query notebooks and view chat history
- **Artifact Management**: Create and manage various artifacts:
  - Audio Overviews
  - Video Overviews
  - Flashcards
  - Quizzes
  - Infographics
  - Slide Decks
  - Reports

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- FastAPI backend running (default: http://localhost:8000)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
Create a `.env.local` file (optional, defaults are provided):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── notebooks/         # Notebook pages
│   ├── login/             # Login page
│   ├── register/          # Registration page
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page (redirects)
├── components/            # React components
│   ├── ArtifactManager.tsx
│   ├── ArtifactCreateModal.tsx
│   ├── ChatInterface.tsx
│   ├── Navbar.tsx
│   ├── SourceManager.tsx
│   └── SourceReviewModal.tsx
├── contexts/              # React contexts
│   └── AuthContext.tsx    # Authentication context
├── lib/                   # Utilities
│   ├── api.ts            # Axios instance
│   ├── api-client.ts     # API client functions
│   └── types.ts          # TypeScript types
└── package.json
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Configuration

The frontend connects to the FastAPI backend. The API URL can be configured via:
- Environment variable: `NEXT_PUBLIC_API_URL`
- Default: `http://localhost:8000`

## Authentication

The app uses JWT tokens stored in localStorage. Tokens are automatically included in API requests via axios interceptors.

## Technologies

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Axios** - HTTP client
- **React Markdown** - Markdown rendering
- **date-fns** - Date formatting

