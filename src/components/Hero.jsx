import React, { useState, useEffect, useRef } from 'react';
import AnimatedCounter from './AnimatedCounter';
import BlockchainAnimation from './BlockchainAnimation';
import './Hero.css';

const Hero = ({ onStartSecuring, overlayDismissed = false }) => {
    const [statsVisible, setStatsVisible] = useState(false);
    const statsRef = useRef(null);

    // Observer for stats visibility to trigger counter animations
    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                setStatsVisible(entry.isIntersecting);
            },
            { threshold: 0.5 }
        );

        if (statsRef.current) {
            observer.observe(statsRef.current);
        }

        return () => observer.disconnect();
    }, []);

    // Counter animations only start after overlay is dismissed AND stats are visible
    const shouldAnimateCounters = statsVisible && overlayDismissed;

    return (
        <section id="hero" className="hero">
            <div className="hero-layout">
                {/* Left side - content */}
                <div className="hero-left">
                    <div className="hero-badge">
                        <span className="badge-dot"></span>
                        AI-POWERED SECURITY
                    </div>

                    <h1 className="glitch-text" data-text="NodesCrypt">
                        Nodes<span className="gradient-text"><em>Crypt</em></span>
                    </h1>

                    <h2 className="hero-subtitle">
                        First Fully <span className="highlight-text">Autonomous</span>
                        <br />Node-Level Defense Platform
                    </h2>

                    {/* Stats bar */}
                    <div ref={statsRef} className="stats-bar">
                        <div className="stat-item">
                            <div className="stat-value">
                                <AnimatedCounter end={98} suffix="%" duration={1500} isVisible={shouldAnimateCounters} />
                            </div>
                            <div className="stat-label">Threat Detection</div>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat-item">
                            <div className="stat-value">24/7</div>
                            <div className="stat-label">AI Monitoring</div>
                        </div>
                        <div className="stat-divider"></div>
                        <div className="stat-item">
                            <div className="stat-value">
                                <AnimatedCounter end={10} prefix="<" suffix="ms" duration={1500} isVisible={shouldAnimateCounters} />
                            </div>
                            <div className="stat-label">Response Time</div>
                        </div>
                    </div>

                    <div className="hero-btns">
                        <button className="btn btn-glow" onClick={() => document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })}>
                            <span className="btn-icon">🛡️</span>
                            Get Started
                        </button>
                        <button className="btn btn-primary" onClick={() => document.getElementById('about')?.scrollIntoView({ behavior: 'smooth' })}>
                            <span className="btn-icon">⚡</span>
                            View Technology
                        </button>
                    </div>
                </div>

                {/* Right side - Blockchain animation */}
                <div className="hero-right">
                    <BlockchainAnimation />
                </div>
            </div>

            {/* Particle system */}
            <div className="particle-system">
                {[...Array(30)].map((_, i) => (
                    <div
                        key={i}
                        className="particle"
                        style={{
                            '--delay': `${Math.random() * 5}s`,
                            '--duration': `${5 + Math.random() * 10}s`,
                            '--x': `${Math.random() * 100}%`,
                            '--y': `${Math.random() * 100}%`,
                            '--size': `${2 + Math.random() * 4}px`
                        }}
                    ></div>
                ))}
            </div>
        </section>
    );
};

export default Hero;
