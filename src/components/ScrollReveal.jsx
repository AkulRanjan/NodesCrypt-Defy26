import React from 'react';
import { useScrollAnimation } from '../hooks/useScrollAnimation';
import './ScrollReveal.css';

/**
 * ScrollReveal Component - Wraps content to reveal on scroll
 * @param {Object} props
 * @param {React.ReactNode} props.children - Content to reveal
 * @param {string} props.animation - Animation type: 'fade-up', 'fade-down', 'fade-left', 'fade-right', 'scale-in', 'zoom-in'
 * @param {string} props.delay - Delay class: 'delay-100', 'delay-200', etc.
 * @param {number} props.threshold - Visibility threshold (0-1)
 * @param {boolean} props.triggerOnce - Whether to trigger only once
 */
const ScrollReveal = ({
    children,
    animation = 'fade-up',
    delay = '',
    threshold = 0.1,
    triggerOnce = true,
    className = '',
}) => {
    const { ref, isVisible } = useScrollAnimation({
        threshold,
        triggerOnce,
        rootMargin: '-50px',
    });

    const classes = [
        'scroll-reveal',
        animation,
        delay,
        isVisible ? 'visible' : '',
        className,
    ]
        .filter(Boolean)
        .join(' ');

    return (
        <div ref={ref} className={classes}>
            {children}
        </div>
    );
};

export default ScrollReveal;
