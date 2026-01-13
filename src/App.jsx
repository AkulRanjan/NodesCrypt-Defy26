import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import About from './components/About';
import AttackMarquee from './components/AttackMarquee';
import Features from './components/Features';
import RealTimeMonitor from './components/RealTimeMonitor';
import Contact from './components/Contact';
import Footer from './components/Footer';
import FloatingOrbs from './components/FloatingOrbs';
import SecurityModal from './components/SecurityModal';
import ScrollReveal from './components/ScrollReveal';
import LoadingOverlay from './components/LoadingOverlay';

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);

  // Scroll to top on page load
  useEffect(() => {
    window.scrollTo(0, 0);
    // Also clear any hash in URL
    if (window.location.hash) {
      window.history.replaceState(null, '', window.location.pathname);
    }
  }, []);

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => setIsModalOpen(false);
  const handleOverlayDismiss = () => setShowOverlay(false);

  return (
    <div className="app-container">
      {showOverlay && <LoadingOverlay onDismiss={handleOverlayDismiss} />}
      <SecurityModal isOpen={isModalOpen} onClose={closeModal} />
      <FloatingOrbs />
      <Navbar />
      {/* Hero section loads immediately - no scroll animation */}
      <Hero onStartSecuring={openModal} overlayDismissed={!showOverlay} />

      {/* All other sections reveal on scroll */}
      <ScrollReveal animation="fade-up" threshold={0.15}>
        <About />
      </ScrollReveal>

      <ScrollReveal animation="fade-up" threshold={0.15} delay="delay-100">
        <AttackMarquee />
      </ScrollReveal>

      <ScrollReveal animation="fade-up" threshold={0.15} delay="delay-200">
        <Features />
      </ScrollReveal>

      {/* Real-Time Attack Monitor */}
      <ScrollReveal animation="fade-up" threshold={0.15} delay="delay-100">
        <RealTimeMonitor />
      </ScrollReveal>

      <ScrollReveal animation="fade-up" threshold={0.15} delay="delay-100">
        <Contact />
      </ScrollReveal>

      <ScrollReveal animation="fade-up" threshold={0.2}>
        <Footer />
      </ScrollReveal>
    </div>
  );
}

export default App;

