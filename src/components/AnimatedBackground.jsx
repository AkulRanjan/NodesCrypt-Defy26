import React, { useState, useEffect } from 'react';
import './AnimatedBackground.css';

const AnimatedBackground = () => {
    const [currentFrame, setCurrentFrame] = useState(1);
    const totalFrames = 40;
    const frameRate = 60; // milliseconds per frame (adjust for speed)

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentFrame((prev) => (prev >= totalFrames ? 1 : prev + 1));
        }, frameRate);

        return () => clearInterval(interval);
    }, []);

    // Pad frame number with zeros (e.g., 1 -> 001)
    const getFramePath = (frameNum) => {
        const paddedNum = String(frameNum).padStart(3, '0');
        return `/sequence/ezgif-frame-${paddedNum}.jpg`;
    };

    return (
        <div className="animated-background">
            <img
                src={getFramePath(currentFrame)}
                alt="Background animation"
                className="background-frame"
            />
            <div className="background-overlay"></div>
        </div>
    );
};

export default AnimatedBackground;
