import React, { useState, useEffect } from 'react';
import './Navbar.css';

const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [scrollProgress, setScrollProgress] = useState(0);
  const [activeSection, setActiveSection] = useState('hero');

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);

      // Calculate scroll progress
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (window.scrollY / totalHeight) * 100;
      setScrollProgress(progress);

      // Detect active section
      const sections = ['hero', 'about', 'features', 'contact'];
      let currentSection = 'hero';

      for (const section of sections) {
        const el = document.getElementById(section);
        if (el) {
          const rect = el.getBoundingClientRect();
          // If the top of the section is above the middle of the viewport, it's the current section
          if (rect.top <= window.innerHeight / 2) {
            currentSection = section;
          }
        }
      }
      setActiveSection(currentSection);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { id: 'hero', label: 'Home' },
    { id: 'about', label: 'Technology' },
    { id: 'features', label: 'Security' },
    { id: 'contact', label: 'Contact' }
  ];

  return (
    <nav className={`navbar ${isScrolled ? 'scrolled' : ''}`}>
      {/* Scroll progress bar */}
      <div className="scroll-progress" style={{ width: `${scrollProgress}%` }}></div>

      <div className="container nav-container">
        <a href="#hero" className="nav-logo">
          <img src="/logo.svg" alt="NodesCrypt Logo" className="logo-image" />
          <span className="logo-text">
            Nodes<span className="highlight"><em>Crypt</em></span>
          </span>
        </a>

        <ul className="nav-links">
          {navItems.map((item) => (
            <li key={item.id}>
              <a
                href={`#${item.id}`}
                className={activeSection === item.id ? 'active' : ''}
              >
                {item.label}
                <span className="link-glow"></span>
              </a>
            </li>
          ))}
        </ul>

        <div className="nav-actions">
          <a
            href="https://pixel-defender-r_jbiz.thinkroot.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary btn-nav"
          >
            Play Game
            <span className="btn-shine"></span>
          </a>
          <a
            href="https://nodescrypt-zmq5uy.thinkroot.app/"
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-primary btn-nav"
          >
            Simulation Sandbox
            <span className="btn-shine"></span>
          </a>
          <a href="#contact" className="btn btn-glow btn-nav">
            Get Audit
            <span className="btn-shine"></span>
          </a>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
