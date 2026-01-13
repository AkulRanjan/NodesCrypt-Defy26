import React, { useState, useEffect } from 'react';
import BlurText from './BlurText';
import ParticleBackground from './ParticleBackground';
import './LoadingOverlay.css';

const LoadingOverlay = ({ onDismiss }) => {
    const [isVisible, setIsVisible] = useState(true);
    const [isExiting, setIsExiting] = useState(false);
    const [progress, setProgress] = useState(0);
    const [showSubtitle, setShowSubtitle] = useState(false);
    const [loadingComplete, setLoadingComplete] = useState(false);

    // Auto-increment counter from 0 to 100
    useEffect(() => {
        if (progress >= 100) {
            // When counter reaches 100, show the button
            setTimeout(() => {
                setLoadingComplete(true);
            }, 300);
            return;
        }

        // Increment progress with varying speed for realistic feel
        const timeout = setTimeout(() => {
            // Faster at start, slower near the end
            const increment = progress < 70 ? 2 : progress < 90 ? 1 : 0.5;
            setProgress(prev => Math.min(prev + increment, 100));
        }, 30);

        return () => clearTimeout(timeout);
    }, [progress]);

    const handleDismiss = () => {
        if (isExiting) return;
        setIsExiting(true);

        setTimeout(() => {
            setIsVisible(false);
            if (onDismiss) onDismiss();
        }, 800);
    };

    const handleTitleComplete = () => {
        // Show subtitle after title animation completes
        setShowSubtitle(true);
    };

    if (!isVisible) return null;

    return (
        <div className={`loading-overlay ${isExiting ? 'exiting' : ''}`}>
            <ParticleBackground />
            <div className="loading-content">
                <div className={`loading-title-wrapper ${showSubtitle ? 'moved-up' : ''}`}>
                    <BlurText
                        text="Thinking Blockchain?"
                        delay={50}
                        animateBy="characters"
                        direction="top"
                        onAnimationComplete={handleTitleComplete}
                        className="loading-title"
                    />
                </div>
                {showSubtitle && (
                    <div className="loading-subtitle-container">
                        <BlurText
                            text="Think"
                            delay={50}
                            animateBy="characters"
                            direction="top"
                            className="loading-subtitle"
                        />
                        <BlurText
                            text="NodesCrypt"
                            delay={50}
                            animateBy="characters"
                            direction="top"
                            className="loading-subtitle loading-highlight"
                        />
                    </div>
                )}
            </div>
            <div className={`loading-progress ${loadingComplete ? 'transform-to-button' : ''}`}>
                {!loadingComplete ? (
                    <svg className="progress-ring" width="60" height="60">
                        <circle
                            className="progress-ring-bg"
                            cx="30"
                            cy="30"
                            r="26"
                            fill="none"
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth="4"
                        />
                        <circle
                            className="progress-ring-fill"
                            cx="30"
                            cy="30"
                            r="26"
                            fill="none"
                            stroke="#3673F5"
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeDasharray={`${2 * Math.PI * 26}`}
                            strokeDashoffset={`${2 * Math.PI * 26 * (1 - progress / 100)}`}
                            style={{ transition: 'stroke-dashoffset 0.1s ease-out' }}
                        />
                    </svg>
                ) : (
                    <button className="enter-button" onClick={handleDismiss}>
                        Enter
                    </button>
                )}
            </div>
        </div>
    );
};

export default LoadingOverlay;
