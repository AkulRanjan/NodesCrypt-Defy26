import React, { useEffect, useRef, useState } from 'react';
import './Contact.css';
import { supabase } from '../lib/supabase';

const Contact = () => {
    const [isVisible, setIsVisible] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitStatus, setSubmitStatus] = useState(null); // 'success' | 'error' | null
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        industry: '',
        message: ''
    });
    const sectionRef = useRef(null);

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

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);
        setSubmitStatus(null);

        try {
            const { error } = await supabase
                .from('contact_submissions')
                .insert([{
                    name: formData.name,
                    email: formData.email,
                    industry: formData.industry,
                    message: formData.message
                }]);

            if (error) throw error;

            setSubmitStatus('success');
            setFormData({ name: '', email: '', industry: '', message: '' });

            // Reset success message after 5 seconds
            setTimeout(() => setSubmitStatus(null), 5000);
        } catch (error) {
            console.error('Error submitting form:', error);
            setSubmitStatus('error');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <section ref={sectionRef} id="contact" className={`section-padding contact ${isVisible ? 'visible' : ''}`}>
            <div className="container">
                <div className="section-header">
                    <span className="section-tag animate-slide-down">GET IN TOUCH</span>
                    <h2 className="animate-expand">Ready to <span className="gradient-text">Secure</span> Your Infrastructure?</h2>
                    <p className="section-subtitle animate-fade-up">
                        Deploy enterprise-grade blockchain security in hours, not months
                    </p>
                </div>

                <div className="contact-grid">
                    <div className="contact-info">
                        <div className="info-card animate-card-slide" style={{ '--card-index': 0 }}>
                            <div className="info-icon">📧</div>
                            <div className="info-content">
                                <h4>Email Us</h4>
                                <a href="mailto:www.nodescrypt@gmail.com">www.nodescrypt@gmail.com</a>
                            </div>
                        </div>

                        <div className="info-card animate-card-slide" style={{ '--card-index': 1 }}>
                            <div className="info-icon">🏢</div>
                            <div className="info-content">
                                <h4>Enterprise Solutions</h4>
                                <p>Custom deployments for exchanges, miners, and custody providers</p>
                            </div>
                        </div>

                        <div className="info-card animate-card-slide" style={{ '--card-index': 2 }}>
                            <div className="info-icon">⚡</div>
                            <div className="info-content">
                                <h4>Quick Deployment</h4>
                                <p>Plug-and-play containerized service - operational within hours</p>
                            </div>
                        </div>

                        <div className="target-clients animate-clients">
                            <h4>Who We Serve</h4>
                            <div className="client-tags">
                                {['Enterprises', 'Exchanges', 'Miners', 'Custody Providers', 'DeFi Protocols'].map((tag, index) => (
                                    <span
                                        key={index}
                                        className="client-tag animate-tag"
                                        style={{ '--tag-index': index }}
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="contact-form-wrapper animate-form">
                        <form className="contact-form" onSubmit={handleSubmit}>
                            <div className="form-group">
                                <input
                                    type="text"
                                    name="name"
                                    placeholder="Your Name"
                                    value={formData.name}
                                    onChange={handleChange}
                                    required
                                    disabled={isSubmitting}
                                />
                            </div>
                            <div className="form-group">
                                <input
                                    type="email"
                                    name="email"
                                    placeholder="Email Address"
                                    value={formData.email}
                                    onChange={handleChange}
                                    required
                                    disabled={isSubmitting}
                                />
                            </div>
                            <div className="form-group">
                                <select
                                    name="industry"
                                    value={formData.industry}
                                    onChange={handleChange}
                                    disabled={isSubmitting}
                                >
                                    <option value="">Select Your Industry</option>
                                    <option value="exchange">Cryptocurrency Exchange</option>
                                    <option value="mining">Mining Operation</option>
                                    <option value="custody">Custody Provider</option>
                                    <option value="defi">DeFi Protocol</option>
                                    <option value="enterprise">Enterprise</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>
                            <div className="form-group">
                                <textarea
                                    name="message"
                                    placeholder="Tell us about your security needs..."
                                    rows="4"
                                    value={formData.message}
                                    onChange={handleChange}
                                    disabled={isSubmitting}
                                ></textarea>
                            </div>

                            <button
                                type="submit"
                                className={`btn btn-glow ${isSubmitting ? 'submitting' : ''}`}
                                disabled={isSubmitting}
                            >
                                {isSubmitting ? 'Sending...' : 'Request Demo'}
                            </button>

                            {submitStatus === 'success' && (
                                <div className="form-message success">
                                    ✓ Thank you! We'll be in touch soon.
                                </div>
                            )}
                            {submitStatus === 'error' && (
                                <div className="form-message error">
                                    ✗ Something went wrong. Please try again.
                                </div>
                            )}
                        </form>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default Contact;

