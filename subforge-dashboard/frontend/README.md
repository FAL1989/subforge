# SubForge Dashboard Frontend

A modern React/Next.js dashboard for monitoring and managing AI agents in the SubForge orchestration system.

## Features

### 🎯 Core Functionality
- **Real-time Agent Monitoring**: Live status updates for all AI agents
- **Interactive Task Board**: Kanban-style task management with drag-and-drop
- **Advanced Analytics**: Comprehensive metrics and performance insights  
- **Workflow History**: Complete timeline of all system events
- **Settings Management**: Configurable system preferences

### 🎨 User Experience
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Dark/Light Theme**: Automatic and manual theme switching
- **Real-time Updates**: WebSocket integration for live data
- **Interactive Charts**: Rich data visualization with Recharts
- **Smooth Animations**: Polished UI transitions and loading states

### 🔧 Technical Features
- **Next.js 14**: Modern React framework with App Router
- **TypeScript**: Full type safety throughout the application
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Socket.IO**: Real-time WebSocket communication
- **Recharts**: Powerful charting library for analytics
- **DND Kit**: Accessible drag-and-drop functionality

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Running SubForge backend (on port 8000)

### Installation
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

The application will be available at [http://localhost:3001](http://localhost:3001).

## Project Structure

```
src/
├── app/                    # Next.js 14 App Router pages
│   ├── page.tsx           # Dashboard home page
│   ├── agents/            # Agent management page
│   ├── tasks/             # Task board page  
│   ├── metrics/           # Analytics page
│   ├── history/           # Workflow history page
│   └── settings/          # System settings page
├── components/            # Reusable React components
│   ├── dashboard/         # Dashboard-specific components
│   ├── agents/            # Agent management components
│   ├── tasks/             # Task board components
│   ├── metrics/           # Analytics components
│   ├── history/           # History timeline components
│   ├── layout/            # Layout components (sidebar, header)
│   ├── providers/         # React context providers
│   └── ui/                # Generic UI components
├── hooks/                 # Custom React hooks
├── lib/                   # Utility functions
└── styles/                # Global styles and CSS
```

## Pages Overview

### Dashboard (`/`)
- System overview with key metrics
- Agent status cards with real-time updates
- Recent task activity
- System health monitoring

### Agents (`/agents`) 
- Grid view of all agents with detailed cards
- Filter by status, type, and capabilities
- Performance metrics for each agent
- Real-time status indicators

### Tasks (`/tasks`)
- Kanban board with drag-and-drop functionality
- Task filtering and search
- Task statistics and progress tracking
- Priority and assignee management

### Metrics (`/metrics`)
- Task completion trends over time
- Agent performance comparisons
- System health charts
- Productivity analytics

### History (`/history`)
- Complete timeline of workflow events
- Event filtering by type, status, and agent
- Exportable event data
- Detailed event metadata

### Settings (`/settings`)
- System configuration options
- Notification preferences
- Performance tuning
- Security settings

## Real-time Features

The dashboard maintains live connections to the SubForge backend via WebSocket:

- **Agent Status**: Live updates when agents come online/offline
- **Task Updates**: Real-time task progress and completion
- **System Metrics**: Live CPU, memory, and connection stats
- **Event Stream**: Instant workflow event notifications

## API Integration

The frontend communicates with the SubForge backend API:

```typescript
// Example API endpoints
GET /api/dashboard/overview     # Dashboard summary data
GET /api/agents                 # Agent list and status  
GET /api/tasks                  # Task management
GET /api/metrics               # Analytics data
GET /api/history               # Workflow events
WebSocket /ws                  # Real-time updates
```

## Development

### Key Technologies
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first styling  
- **Socket.IO Client**: WebSocket communication
- **@dnd-kit**: Drag and drop functionality
- **Recharts**: Data visualization
- **Lucide React**: Icon library

### Code Standards
- ESLint + Prettier for code formatting
- TypeScript strict mode enabled
- Component-based architecture
- Custom hooks for data fetching
- Responsive design patterns

## Deployment

For production deployment:

```bash
# Build optimized production bundle
npm run build

# Start production server  
npm start
```

The application is optimized for deployment on platforms like Vercel, Netlify, or any Node.js hosting service.

---

**Generated by SubForge v1.0 - AI Agent Orchestration Platform**