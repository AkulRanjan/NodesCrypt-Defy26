import React, { useState } from 'react';
import './SecurityModal.css';

const SecurityModal = ({ isOpen, onClose }) => {
    const [step, setStep] = useState(1);
    const [selectedPlan, setSelectedPlan] = useState('full'); // 'full' or 'custom'
    const [isDeploying, setIsDeploying] = useState(false);

    if (!isOpen) return null;

    const handleDeploy = () => {
        setIsDeploying(true);
        // Simulate deployment for 3 seconds
        setTimeout(() => {
            setIsDeploying(false);
            setStep(3); // Success step
        }, 3000);
    };

    return (
        <div className="modal-overlay">
            <div className={`modal-container ${isDeploying ? 'deploying' : ''}`}>
                <button className="modal-close" onClick={onClose}>×</button>

                {step === 1 && (
                    <div className="modal-content animate-fade-in">
                        <div className="modal-header">
                            <h2>Deploy NodesCrypt Defense</h2>
                            <p>Select your security configuration level</p>
                        </div>

                        <div className="security-options">
                            <div
                                className={`security-card ${selectedPlan === 'full' ? 'selected' : ''}`}
                                onClick={() => setSelectedPlan('full')}
                            >
                                <div className="card-header">
                                    <span className="card-icon">🛡️</span>
                                    <div className="card-title">
                                        <h3>Include All Essentials</h3>
                                        <span className="tag-recommended">RECOMMENDED</span>
                                    </div>
                                </div>
                                <p>Comprehensive protection against all known infrastructure threats.</p>
                                <ul className="feature-list">
                                    <li>✅ Eclipse Attack Prevention</li>
                                    <li>✅ Sybil Attack Defense</li>
                                    <li>✅ Double-Spend Protection</li>
                                    <li>✅ 51% Attack Mitigation</li>
                                    <li>✅ Real-time Anomaly Detection</li>
                                </ul>
                            </div>
                        </div>

                        <div className="modal-actions">
                            <button className="btn btn-glow full-width" onClick={handleDeploy}>
                                Initialize Deployment
                            </button>
                        </div>
                    </div>
                )}

                {isDeploying && (
                    <div className="modal-content deployment-status">
                        <div className="scanner-animation">
                            <div className="scan-line"></div>
                        </div>
                        <h3>Establishing Secure Node Link...</h3>
                        <div className="terminal-logs">
                            <p>&gt; Initializing RL Agent...</p>
                            <p>&gt; Verifying Blockchain Integrity...</p>
                            <p>&gt; Loading Threat Models (v4.2.0)...</p>
                            <p>&gt; Securing P2P Layer...</p>
                            <p className="success">&gt; SYSTEM SECURED</p>
                        </div>
                    </div>
                )}

                {step === 3 && (
                    <div className="modal-content success-view animate-scale-in">
                        <div className="success-icon">✨</div>
                        <h2>Deployment Successful</h2>
                        <p>Your infrastructure is now monitored by NodesCrypt Autonomous Defense.</p>
                        <button className="btn btn-primary" onClick={onClose}>Return to Dashboard</button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SecurityModal;
