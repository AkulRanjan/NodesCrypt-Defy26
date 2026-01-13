const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
const server = http.createServer(app);

// Configure CORS for both Express and Socket.io
app.use(cors({
    origin: '*', // Allow all origins (restrict in production)
    methods: ['GET', 'POST']
}));
app.use(express.json());

// Socket.io server with CORS
const io = new Server(server, {
    cors: {
        origin: '*',
        methods: ['GET', 'POST']
    }
});

// Store connected clients
let connectedClients = 0;

// Socket.io connection handling
io.on('connection', (socket) => {
    connectedClients++;
    console.log(`✅ Client connected. Total clients: ${connectedClients}`);

    // Send connection confirmation
    socket.emit('connected', {
        message: 'Connected to NodesCrypt real-time server',
        timestamp: new Date().toISOString()
    });

    socket.on('disconnect', () => {
        connectedClients--;
        console.log(`❌ Client disconnected. Total clients: ${connectedClients}`);
    });
});

// HTTPS POST endpoint to receive data from your model system
app.post('/api/attack-data', (req, res) => {
    const attackData = req.body;

    console.log('📊 Received attack data:', attackData);

    // Validate data
    if (!attackData || !attackData.timestamp) {
        return res.status(400).json({
            error: 'Invalid data format. Required fields: timestamp'
        });
    }

    // Broadcast to all connected WebSocket clients
    io.emit('attack-update', attackData);

    res.status(200).json({
        success: true,
        message: 'Data broadcasted to clients',
        clients: connectedClients
    });
});

// Generic endpoint for ALL types of live data (attacks, metrics, logs, status, etc.)
app.post('/api/live-data', (req, res) => {
    const liveData = req.body;

    console.log(`📊 Received ${liveData.type || 'unknown'} data:`, liveData);

    // Validate data
    if (!liveData || !liveData.timestamp) {
        return res.status(400).json({
            error: 'Invalid data format. Required fields: timestamp'
        });
    }

    // Broadcast to all connected WebSocket clients
    io.emit('live-data', liveData);

    res.status(200).json({
        success: true,
        message: `${liveData.type || 'Data'} broadcasted to clients`,
        clients: connectedClients
    });
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        clients: connectedClients,
        uptime: process.uptime()
    });
});

// Test endpoint to send mock data
app.post('/api/test-attack', (req, res) => {
    const mockData = {
        timestamp: new Date().toISOString(),
        attack_type: 'DDoS',
        severity: 'high',
        source_ip: '192.168.1.100',
        target: 'node-5',
        status: 'blocked',
        details: 'Test attack detected - 10000 req/s from single source'
    };

    io.emit('attack-update', mockData);
    res.json({ success: true, data: mockData });
});

const PORT = process.env.PORT || 3001;

server.listen(PORT, () => {
    console.log(`🚀 WebSocket server running on port ${PORT}`);
    console.log(`📡 POST endpoint: http://localhost:${PORT}/api/attack-data`);
    console.log(`🏥 Health check: http://localhost:${PORT}/health`);
});
