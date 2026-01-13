import React, { useEffect, useRef } from 'react';

const ParticleBackground = () => {
    const canvasRef = useRef(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Configuration
        const PARTICLE_COUNT = 120;
        const CONVERGE_SPEED = 0.15;
        const SCATTER_SPEED = 0.03;
        const MOUSE_IDLE_THRESHOLD = 200;

        // Set canvas size
        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };
        resize();
        window.addEventListener('resize', resize);

        // Mouse state
        let mouseX = canvas.width / 2;
        let mouseY = canvas.height / 2;
        let targetMouseX = mouseX;
        let targetMouseY = mouseY;
        let lastMouseMove = 0;
        let isMouseActive = false;

        // Create particles in a centered area
        const particles = [];
        for (let i = 0; i < PARTICLE_COUNT; i++) {
            const angle = Math.random() * Math.PI * 2;
            const radius = Math.random() * 400 + 100;
            const x = canvas.width / 2 + Math.cos(angle) * radius;
            const y = canvas.height / 2 + Math.sin(angle) * radius;

            particles.push({
                x,
                y,
                originalX: x,
                originalY: y,
                size: 2 + Math.random() * 3,
                opacity: 0.3 + Math.random() * 0.5,
                baseOpacity: 0.3 + Math.random() * 0.5
            });
        }

        // Mouse/touch handlers
        const handleMouseMove = (e) => {
            targetMouseX = e.clientX;
            targetMouseY = e.clientY;
            lastMouseMove = Date.now();
            isMouseActive = true;
        };

        const handleTouchMove = (e) => {
            if (e.touches.length > 0) {
                targetMouseX = e.touches[0].clientX;
                targetMouseY = e.touches[0].clientY;
                lastMouseMove = Date.now();
                isMouseActive = true;
            }
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('touchmove', handleTouchMove);

        // Animation loop
        let animationId;

        const animate = () => {
            animationId = requestAnimationFrame(animate);

            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Smooth mouse interpolation
            mouseX += (targetMouseX - mouseX) * 0.1;
            mouseY += (targetMouseY - mouseY) * 0.1;

            // Check if mouse is idle
            if (Date.now() - lastMouseMove > MOUSE_IDLE_THRESHOLD) {
                isMouseActive = false;
            }

            // Update and draw particles
            for (const p of particles) {
                if (isMouseActive) {
                    // Converge to mouse
                    const dx = mouseX - p.x + (Math.random() - 0.5) * 20;
                    const dy = mouseY - p.y + (Math.random() - 0.5) * 20;
                    p.x += dx * CONVERGE_SPEED;
                    p.y += dy * CONVERGE_SPEED;
                    p.opacity = Math.min(1, p.baseOpacity + 0.4);
                } else {
                    // Scatter back
                    const dx = p.originalX - p.x;
                    const dy = p.originalY - p.y;
                    p.x += dx * SCATTER_SPEED;
                    p.y += dy * SCATTER_SPEED;
                    p.opacity += (p.baseOpacity - p.opacity) * 0.05;
                }

                // Draw blue dot
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(54, 115, 245, ${p.opacity})`;
                ctx.fill();

                // Add glow effect
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size * 2, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(54, 115, 245, ${p.opacity * 0.2})`;
                ctx.fill();
            }
        };

        animate();

        // Cleanup
        return () => {
            cancelAnimationFrame(animationId);
            window.removeEventListener('resize', resize);
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('touchmove', handleTouchMove);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 1
            }}
        />
    );
};

export default ParticleBackground;
