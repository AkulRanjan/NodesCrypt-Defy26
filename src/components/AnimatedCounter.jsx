import React, { useEffect, useRef, useState } from 'react';

// Counter component that animates only once when first visible
const AnimatedCounter = ({ end, prefix = '', suffix = '', duration = 1500, isVisible }) => {
    const [count, setCount] = useState(0);
    const [hasCompleted, setHasCompleted] = useState(false);
    const animationRef = useRef(null);
    const startedRef = useRef(false);

    useEffect(() => {
        // If already completed, always show the final value
        if (hasCompleted) {
            setCount(end);
            return;
        }

        // Skip if not visible or animation already started
        if (!isVisible || startedRef.current) {
            return;
        }

        // Mark animation as started
        startedRef.current = true;

        const startTime = performance.now();
        const endValue = end;

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 4);
            const currentCount = Math.round(easeOut * endValue);
            setCount(currentCount);

            if (progress < 1) {
                animationRef.current = requestAnimationFrame(animate);
            } else {
                // Animation complete - mark as completed
                setHasCompleted(true);
            }
        };

        animationRef.current = requestAnimationFrame(animate);

        return () => {
            if (animationRef.current) {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, [isVisible, end, duration, hasCompleted]);

    // Always show final value if completed
    const displayValue = hasCompleted ? end : count;

    return <span>{prefix}{displayValue}{suffix}</span>;
};

export default AnimatedCounter;
