import React from 'react';
import './AttackMarquee.css';

const AttackMarquee = () => {
    const attackTypes = {
        row1: [
            { name: '51% Attack', icon: '⚠️' },
            { name: 'Selfish Mining Attack', icon: '⛏️' },
            { name: 'Block Withholding Attack', icon: '🧱' },
            { name: 'Timejacking Attack', icon: '⏰' },
            { name: 'Sybil Attack', icon: '👥' },
            { name: 'Eclipse Attack', icon: '🌑' },
            { name: 'Partition Attack', icon: '🔀' },
            { name: 'BGP Hijacking Attack', icon: '🌐' },
        ],
        row2: [
            { name: 'Double-Spending Attack', icon: '💸' },
            { name: 'Replace-By-Fee Abuse', icon: '🔄' },
            { name: 'Transaction Malleability', icon: '🔧' },
            { name: 'Fee Sniping Attack', icon: '🎯' },
            { name: 'DoS Attack', icon: '🚫' },
            { name: 'DDoS Attack', icon: '💥' },
            { name: 'Dust Attack', icon: '🌫️' },
            { name: 'Address Reuse Attack', icon: '🔁' },
        ],
        row3: [
            { name: 'Private Key Theft', icon: '🔑' },
            { name: 'Wallet Malware', icon: '🦠' },
            { name: 'Phishing Attack', icon: '🎣' },
            { name: 'Clipboard Hijacking', icon: '📋' },
            { name: 'Rogue Wallet Attack', icon: '👛' },
            { name: 'Exchange Hack', icon: '🏦' },
            { name: 'Hot Wallet Compromise', icon: '🔥' },
            { name: 'API Exploitation', icon: '🔌' },
        ],
        row4: [
            { name: 'Man-in-the-Middle', icon: '👤' },
            { name: 'Routing Attack', icon: '🛤️' },
            { name: 'Network Isolation', icon: '🔒' },
            { name: 'Quantum Attack', icon: '⚛️' },
            { name: 'Hash Collision', icon: '#️⃣' },
            { name: 'Consensus Manipulation', icon: '🗳️' },
            { name: 'Mempool Flooding', icon: '🌊' },
            { name: 'Governance Attack', icon: '🏛️' },
        ],
    };

    const renderRow = (attacks, direction) => (
        <div className={`marquee-row ${direction}`}>
            <div className="marquee-content">
                {[...attacks, ...attacks].map((attack, index) => (
                    <div key={index} className="attack-tag">
                        <span className="attack-icon">{attack.icon}</span>
                        <span className="attack-name">{attack.name}</span>
                    </div>
                ))}
            </div>
        </div>
    );

    return (
        <section className="attack-marquee-section">
            <div className="container">
                <div className="section-header">
                    <span className="section-tag">PROTECTION</span>
                    <h2>Defending Against <span className="gradient-text">Every Threat</span></h2>
                    <p className="section-subtitle">
                        Real-time protection against 30+ blockchain attack vectors
                    </p>
                </div>
            </div>

            <div className="marquee-container">
                {renderRow(attackTypes.row1, 'scroll-left')}
                {renderRow(attackTypes.row2, 'scroll-right')}
                {renderRow(attackTypes.row3, 'scroll-left')}
                {renderRow(attackTypes.row4, 'scroll-right')}
            </div>
        </section>
    );
};

export default AttackMarquee;
