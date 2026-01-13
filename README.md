<div align="center">

# 🛡️ NodesCrypt

### AI-Driven Cryptocurrency Security Platform

[![React](https://img.shields.io/badge/React-18.x-61DAFB?style=for-the-badge&logo=react&logoColor=white)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.x-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Three.js](https://img.shields.io/badge/Three.js-r150-000000?style=for-the-badge&logo=three.js&logoColor=white)](https://threejs.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**Securing Bitcoin and Cryptocurrency infrastructure using advanced Reinforcement Learning and Machine Learning models.**

[Live Demo](https://nodescrypt-defy26.vercel.app) • [Documentation](#features) • [Getting Started](#installation)

</div>

---

## 🌟 Overview

NodesCrypt is a cutting-edge cybersecurity platform designed to protect blockchain infrastructure through AI-powered threat detection and real-time monitoring. Our platform leverages Reinforcement Learning (RL) agents and Machine Learning models to identify and neutralize threats before they can impact the network.

## ✨ Features

### 🎯 Core Capabilities

- **Real-Time Threat Detection** - 24/7 AI-powered monitoring with sub-10ms response time
- **Autonomous Defense System** - RL agents that adapt and learn from new attack patterns
- **Live Dashboard** - Real-time metrics visualization with interactive graphs
- **Mempool Analysis** - Continuous monitoring of transaction pools for anomalies

### 🎨 User Interface

- **Modern Glassmorphism Design** - Premium dark theme with neon accents
- **3D Blockchain Animation** - Interactive Three.js visualization
- **Smooth Animations** - Scroll-triggered reveals and micro-interactions
- **Fully Responsive** - Optimized for all devices

### 📊 Live Monitoring Dashboard

- Mempool Size tracking
- Threats Blocked counter
- Total Threats detected
- RL Decisions made
- System Mode indicator (NORMAL/DEFENSIVE/ACTIVE)
- Real-time graph visualization

## 🛠️ Tech Stack

| Category | Technologies |
|----------|-------------|
| **Frontend** | React 18, Vite 5, CSS3 |
| **3D Graphics** | Three.js |
| **Styling** | CSS Modules, Glassmorphism |
| **State Management** | React Hooks |
| **Data Fetching** | REST API, WebSocket-ready |
| **Backend Integration** | Supabase (Contact Form) |
| **Deployment** | Vercel / Netlify |

## 📦 Installation

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Quick Start

```bash
# Clone the repository
git clone https://github.com/AkulRanjan/NodesCrypt-Defy26.git

# Navigate to project directory
cd NodesCrypt-Defy26

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be running at `http://localhost:5173`

### Build for Production

```bash
# Create optimized production build
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
NodesCrypt/
├── public/
│   ├── logo.svg              # Brand logo
│   └── sequence/             # Animation frames
├── src/
│   ├── components/
│   │   ├── Navbar.jsx        # Navigation bar
│   │   ├── Hero.jsx          # Hero section with 3D animation
│   │   ├── About.jsx         # About section
│   │   ├── Features.jsx      # Features showcase
│   │   ├── RealTimeMonitor.jsx  # Live dashboard
│   │   ├── Contact.jsx       # Contact form
│   │   ├── Footer.jsx        # Footer
│   │   ├── BlockchainAnimation.jsx  # Three.js animation
│   │   └── LoadingOverlay.jsx  # Loading screen
│   ├── hooks/
│   │   └── useScrollAnimation.js  # Scroll animations
│   ├── lib/
│   │   └── supabase.js       # Supabase client
│   ├── App.jsx               # Main app component
│   ├── main.jsx              # Entry point
│   └── index.css             # Global styles
├── index.html
├── vite.config.js
└── package.json
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### API Endpoints

The real-time dashboard fetches data from:
```
https://your-api-endpoint/api/dashboard
```

Update the `API_URL` in `src/components/RealTimeMonitor.jsx` to point to your backend.

## 🎮 Interactive Features

### 3D Blockchain Animation
- **Mouse Drag** - Rotate the 3D scene 360°
- **Auto Rotation** - Continuous ambient rotation
- **Dynamic Shield** - Visual threat defense representation

### Dashboard Interaction
- **Click Metric Cards** - Switch between different metric graphs
- **Real-time Updates** - Data refreshes every second
- **Live Status Indicators** - System health at a glance

## 🚀 Deployment

### Vercel (Recommended)

```bash
npm install -g vercel
vercel
```

### Netlify

```bash
npm run build
# Upload 'dist' folder to Netlify
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

**NodesCrypt** - Developed for **DeFy26 Hackathon**

---

<div align="center">

**Built with ❤️ for a safer blockchain ecosystem**

[⬆ Back to Top](#-nodescrypt)

</div>
