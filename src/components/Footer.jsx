import React from 'react';
import './Footer.css';
import TestAnimation from './TestAnimation';

const Footer = () => {
    return (
        <footer className="footer">
            {/* 3D Road Animation background */}
            <div className="footer-animation-wrapper">
                <TestAnimation className="footer-animation" />
                <div className="footer-glow-overlay"></div>
                <div className="footer-overlay"></div>
            </div>

            <div className="container footer-content">
                <div className="footer-main">
                    <div className="footer-brand">
                        <div className="footer-logo">
                            <img src="/logo.svg" alt="NodesCrypt Logo" className="logo-image" />
                            <span className="logo-text">
                                Nodes<span className="highlight"><em>Crypt</em></span>
                            </span>
                        </div>
                        <p className="footer-tagline">
                            Autonomous node-level defense for blockchain infrastructure
                        </p>
                    </div>

                    <div className="footer-links">
                        <div className="footer-column">
                            <h4>Product</h4>
                            <a href="#about">Technology</a>
                            <a href="#features">Security</a>
                            <a href="#contact">Enterprise</a>
                        </div>
                        <div className="footer-column">
                            <h4>Company</h4>
                            <a href="#about">About</a>
                            <a href="#contact">Contact</a>
                            <a href="#">Careers</a>
                        </div>
                    </div>

                    <div className="footer-contact">
                        <h4>Get in Touch</h4>
                        <a href="mailto:www.nodescrypt@gmail.com" className="email-link">
                            <svg className="email-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M4 4H20C21.1 4 22 4.9 22 6V18C22 19.1 21.1 20 20 20H4C2.9 20 2 19.1 2 18V6C2 4.9 2.9 4 4 4Z"
                                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                <path d="M22 6L12 13L2 6"
                                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                            www.nodescrypt@gmail.com
                        </a>
                    </div>
                </div>

                <div className="footer-bottom">
                    <div className="footer-glow-line"></div>
                    <p>&copy; 2025 NodesCrypt. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;

