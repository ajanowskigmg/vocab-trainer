# Vocab Trainer

An AI-powered flashcard learning application that automatically generates study materials using artificial intelligence and helps you learn efficiently with spaced repetition.

## 📋 Table of Contents

- [About](#about)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Available Scripts](#available-scripts)
- [Project Scope](#project-scope)
- [Project Status](#project-status)
- [License](#license)

## About

Vocab Trainer is a web application that leverages artificial intelligence to automatically generate educational flashcards from any text input. The app integrates AI-powered flashcard generation with the proven SM-2 (SuperMemo 2) spaced repetition algorithm, allowing users to learn new content effectively without the time-consuming manual creation of study materials.

### Key Features

- **AI-Powered Generation**: Automatically generate 5-8 flashcards from 10-2000 characters of text using GPT-4o-mini
- **Staging Area**: Review, edit, and reject generated flashcards before adding them to your deck
- **Manual Creation**: Create and manage flashcards manually when needed
- **Spaced Repetition**: SM-2 algorithm for optimal learning session scheduling
- **User Authentication**: Secure authentication with Row Level Security (RLS) via Supabase
- **Single Repository**: Full-stack application without the need for a separate backend

### Target Users

Students, learners, and office workers who use web applications daily and are looking for efficient learning tools without spending time on manual flashcard creation.

## Tech Stack

### Frontend
- **Astro 5** - Fast, efficient pages and applications with minimal JavaScript
- **React 19** - Interactive components where needed
- **TypeScript 5** - Static typing and better IDE support
- **Tailwind 4** - Utility-first CSS framework for styling
- **Shadcn/ui** - Accessible React component library

### Backend
- **Astro API Routes** - Server-side API endpoints
- **Supabase** - Backend-as-a-Service (PostgreSQL database + SDK + authentication)
  - PostgreSQL database
  - Built-in user authentication
  - Row Level Security (RLS) for data protection

### AI Integration
- **OpenRouter.ai** - Access to multiple AI models (OpenAI, Anthropic, Google) with cost control and financial limits

### DevOps
- **GitHub Actions** - CI/CD pipeline
- **DigitalOcean** - Docker container hosting
- **Docker** - Containerized deployment

## Getting Started

### Prerequisites

- **Node.js**: Version 22.14.0 (specified in `.nvmrc`)
- **npm** or **pnpm** (package manager)
- **Supabase Account**: For database and authentication
- **OpenRouter.ai API Key**: For AI-powered flashcard generation

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ajanowskigmg/vocab-trainer.git
   cd vocab-trainer
   ```

2. **Install Node.js version (if using nvm)**
   ```bash
   nvm use
   ```

3. **Install dependencies**
   ```bash
   npm install
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory with the following variables:
   ```env
   PUBLIC_SUPABASE_URL=your_supabase_url
   PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

5. **Set up Supabase**
   - Create a new project in Supabase
   - Run database migrations (create tables: `cards`, `review_history`)
   - Configure Row Level Security policies
   - Enable email authentication

6. **Run the development server**
   ```bash
   npm run dev
   ```

7. **Open your browser**
   
   Navigate to `http://localhost:4321` (or the port specified in the console)

## Available Scripts

- **`npm run dev`** - Start the development server with hot module replacement
- **`npm run build`** - Build the production-ready application
- **`npm run preview`** - Preview the production build locally
- **`npm run astro`** - Run Astro CLI commands
- **`npm run lint`** - Run ESLint to check for code issues
- **`npm run lint:fix`** - Automatically fix ESLint issues where possible
- **`npm run format`** - Format code using Prettier

## Project Scope

### ✅ Included in MVP

- AI flashcard generation (5-8 cards per request, 10-2000 character input)
- Staging area with review, edit, and reject capabilities
- Manual flashcard creation and management
- SM-2 spaced repetition algorithm
- User authentication with email/password (Supabase Auth)
- Row Level Security for data protection
- Single global deck per user
- Study sessions with difficulty rating (Again, Hard, Good, Easy)
- Basic filtering, sorting, and search
- Responsive web design (desktop and mobile)
- Session summary and progress tracking

### ❌ Not Included in MVP

The following features are **not** part of the MVP and may be considered for future iterations:

**Advanced Features:**
- Multiple decks/collections per user
- Tags and advanced categorization
- Flashcards with images, audio, or video
- Multiple choice or fill-in-the-blank formats
- Import/export functionality (PDF, CSV, Anki, Quizlet)
- Public flashcard sets and sharing
- Collaboration features

**Advanced Learning:**
- Algorithms more advanced than SM-2
- Customizable prompt system for users
- Machine learning-based optimization
- Detailed analytics and heatmaps
- Gamification (streaks, achievements, leaderboards)

**Platform Extensions:**
- Native iOS and Android apps
- Offline mode with synchronization
- Progressive Web App (PWA)
- Push notifications

**Other:**
- Dark mode
- Multi-language interface
- A/B testing infrastructure
- Advanced monitoring and alerting

### Limits

- Maximum 500 flashcards per user (training project limitation)
- Maximum 2000 characters per AI generation request
- Monthly budget cap of $10 for AI API costs
- Supabase free tier: 500MB storage, 50K users, 2GB bandwidth

## Project Status

**Current Status**: 🚧 MVP in Development

This is a training/learning initiative developed by a single full-stack developer with a flexible timeframe and focus on the learning experience. The project aims to:

- Practice full-stack development with modern technologies
- Integrate AI capabilities into a real-world application
- Implement proper authentication and security (RLS)
- Deploy a production-ready application using Docker and CI/CD

### Success Metrics

**Key Performance Indicators (KPIs):**
- AI Acceptance Rate: ≥75% (percentage of AI-generated cards not rejected)
- AI Usage Rate: ≥75% (percentage of cards created using AI)

**Target Goals:**
- Minimum 5 active users testing for at least 2 weeks
- Average session: min 10 flashcards per session
- Retention: ≥50% of users return after 1 week
- Cost: AI ≤$10/month, infrastructure ~$5-10/month

## License

License information to be determined. Please contact the repository owner for usage rights and permissions.

---

**Note**: This project is part of a learning initiative and serves as a practical implementation of modern web development practices, AI integration, and deployment workflows.
