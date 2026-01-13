import React, { useEffect, useRef, useState } from 'react';
import AnimatedCounter from './AnimatedCounter';
import './Features.css';

const Features = () => {
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
            { threshold: 0.05 }
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

    const features = [
        {
            icon: "🛡️",
            title: "Eclipse Attack Defense",
            desc: "Detect and neutralize attacks that isolate your nodes from the legitimate network by monopolizing peer connections.",
            color: "primary"
        },
        {
            icon: "👁️",
            title: "Sybil Attack Protection",
            desc: "Identify and block malicious nodes flooding your peer connections through our 20+ parameter reputation index.",
            color: "secondary"
        },
        {
            icon: "₿",
            title: "Double-Spend Prevention",
            desc: "Real-time mempool monitoring to detect double-spend attempts exploiting network delays and transaction conflicts.",
            color: "primary"
        },
        {
            icon: "⚡",
            title: "98% Accuracy",
            desc: "Industry-leading threat detection accuracy powered by advanced AI models trained on millions of attack simulations.",
            color: "secondary"
        },
        {
            icon: "🔄",
            title: "Node-by-Node Control",
            desc: "Granular per-node security management—surgical control over individual node behavior while maintaining decentralization.",
            color: "primary"
        },
        {
            icon: "🔐",
            title: "Privacy-Preserving Deployment",
            desc: "Containerized plug-and-play service that trains on your private blockchain data locally—no external data transmission.",
            color: "secondary"
        }
    ];

    return (
        <section ref={sectionRef} id="features" className={`section-padding features ${isVisible ? 'visible' : ''}`}>
            <div className="container">
                <div className="section-header">
                    <span className="section-tag animate-bounce">CAPABILITIES</span>
                    <h2 className="animate-split">What Makes Us <span className="gradient-text">Unique?</span></h2>
                    <p className="section-subtitle animate-blur">
                        The only node-level defense platform protecting blockchain infrastructure in real-time
                    </p>
                </div>

                <div className="features-grid">
                    {features.map((item, index) => (
                        <div
                            key={index}
                            className={`feature-card ${item.color} animate-card-${index % 2 === 0 ? 'left' : 'right'}`}
                            style={{ '--index': index }}
                        >
                            <div className="card-bg-effect"></div>
                            <div className="feature-icon">{item.icon}</div>
                            <h3>{item.title}</h3>
                            <p>{item.desc}</p>
                            <div className="card-corner corner-tl"></div>
                            <div className="card-corner corner-br"></div>
                        </div>
                    ))}
                </div>

                <div ref={statsRef} className={`market-stats ${statsVisible ? 'stats-visible' : ''}`}>
                    <div className="stat-box animate-counter" style={{ '--stat-delay': '0s' }}>
                        <h3>
                            <AnimatedCounter
                                end={2}
                                prefix="$"
                                suffix="B+"
                                duration={2000}
                                isVisible={statsVisible}
                            />
                        </h3>
                        <p>Crypto thefts in 2025</p>
                    </div>
                    <div className="stat-box animate-counter" style={{ '--stat-delay': '0.15s' }}>
                        <h3>
                            <AnimatedCounter
                                end={128}
                                prefix="$"
                                suffix="B"
                                duration={2500}
                                isVisible={statsVisible}
                            />
                        </h3>
                        <p>Market by 2032</p>
                    </div>
                    <div className="stat-box animate-counter" style={{ '--stat-delay': '0.3s' }}>
                        <h3>
                            <AnimatedCounter
                                end={55}
                                prefix=""
                                suffix="%"
                                duration={2000}
                                isVisible={statsVisible}
                            />
                        </h3>
                        <p>Annual CAGR</p>
                    </div>
                </div>

                <div className="features-cta animate-zoom">
                    <h3>Protect Your Blockchain Infrastructure</h3>
                    <p>Join enterprises, exchanges, miners, and custody providers securing their networks</p>
                    <button className="btn btn-glow" onClick={() => document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })}>Get Started</button>
                </div>
            </div>
        </section>
    );
};

export default Features;
