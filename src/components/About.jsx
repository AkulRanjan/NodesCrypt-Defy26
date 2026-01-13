import React, { useEffect, useRef, useState } from 'react';
import AnimatedCounter from './AnimatedCounter';
import './About.css';

const About = () => {
    const [isVisible, setIsVisible] = useState(false);
    const [statsVisible, setStatsVisible] = useState(false);
    const sectionRef = useRef(null);
    const statsRef = useRef(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setIsVisible(true);
                }
            },
            { threshold: 0.1 }
        );

        if (sectionRef.current) {
            observer.observe(sectionRef.current);
        }

        return () => observer.disconnect();
    }, []);

    // Observer for stats - triggers only once
    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setStatsVisible(true);
                    observer.disconnect(); // Stop observing after first trigger
                }
            },
            { threshold: 0.3 }
        );

        if (statsRef.current) {
            observer.observe(statsRef.current);
        }

        return () => observer.disconnect();
    }, []);

    return (
        <section ref={sectionRef} id="about" className={`section-padding about ${isVisible ? 'visible' : ''}`}>
            <div className="container">
                <div className="section-header">
                    <span className="section-tag animate-pop">TECHNOLOGY</span>
                    <h2 className="animate-slide-up">World's First <span className="gradient-text">Autonomous</span> Defense System</h2>
                    <p className="section-subtitle animate-fade">
                        Pioneering reinforcement learning-powered node-level security for blockchain infrastructure
                    </p>
                </div>

                {/* Content Tabs - Horizontal Row */}
                <div className="content-tabs">
                    <div className="text-block animate-item" style={{ '--item-delay': '0.1s' }}>
                        <div className="block-icon">🧠</div>
                        <h3>Infrastructure-Level Defense</h3>
                        <p>
                            We protect the core blockchain infrastructure layer where 91% of attacks actually target—not just smart contracts or wallets.
                        </p>
                    </div>

                    <div className="text-block animate-item" style={{ '--item-delay': '0.2s' }}>
                        <div className="block-icon">🔐</div>
                        <h3>Reinforcement Learning</h3>
                        <p>
                            Our RL-powered systems continuously adapt and learn from every attack, trained on 3M+ real-world simulations.
                        </p>
                    </div>

                    <div className="text-block animate-item" style={{ '--item-delay': '0.3s' }}>
                        <div className="block-icon">⚡</div>
                        <h3>Autonomous Response</h3>
                        <p>
                            Execute immediate defensive actions within milliseconds—all autonomously without human intervention.
                        </p>
                    </div>
                </div>

                {/* Stats Row - Below Content with Counting Animation */}
                <div ref={statsRef} className={`stats-row ${statsVisible ? 'stats-visible' : ''}`}>
                    <div className="stat-card animate-card" style={{ '--card-delay': '0.35s' }}>
                        <h3>
                            <AnimatedCounter
                                end={3}
                                suffix="M+"
                                duration={2000}
                                isVisible={statsVisible}
                            />
                        </h3>
                        <p>Attack Simulations</p>
                        <div className="card-graph">
                            <div className="graph-bar" style={{ '--height': '95%' }}></div>
                            <div className="graph-bar" style={{ '--height': '88%' }}></div>
                            <div className="graph-bar" style={{ '--height': '92%' }}></div>
                            <div className="graph-bar" style={{ '--height': '99%' }}></div>
                        </div>
                    </div>

                    <div className="stat-card animate-card" style={{ '--card-delay': '0.45s' }}>
                        <h3>
                            <AnimatedCounter
                                end={91}
                                suffix="%"
                                duration={2000}
                                isVisible={statsVisible}
                            />
                        </h3>
                        <p>Attacks Target Infrastructure</p>
                    </div>

                    <div className="stat-card animate-card" style={{ '--card-delay': '0.55s' }}>
                        <h3>
                            <AnimatedCounter
                                end={10}
                                prefix="<"
                                suffix="ms"
                                duration={1500}
                                isVisible={statsVisible}
                            />
                        </h3>
                        <p>Response Time</p>
                        <div className="speed-meter">
                            <div className="meter-fill"></div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default About;
