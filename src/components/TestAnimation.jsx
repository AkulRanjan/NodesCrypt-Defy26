import React, { useEffect, useRef } from 'react';
import './TestAnimation.css';

/**
 * TestAnimation - Exact recreation of the road animation from animation.txt
 * 
 * The "curvy road" effect comes from camera distortion following a winding path,
 * while the light trails themselves are straight tubes that get distorted by the shader.
 */

const TestAnimation = ({
    options = {},
    className = ''
}) => {
    const containerRef = useRef(null);
    const animationRef = useRef(null);

    // Default configuration matching the original animation.txt
    const defaultOptions = {
        length: 400,
        roadWidth: 10,
        islandWidth: 2,
        lanesPerRoad: 4,
        fov: 90,
        fovSpeedUp: 150,
        speedUp: 2,
        carLightsFade: 0.4,
        lightPairsPerRoadWay: 40,
        movingAwaySpeed: [60, 80],
        movingCloserSpeed: [-120, -160],
        carLightsLength: [400 * 0.03, 400 * 0.2],
        carLightsRadius: [0.05, 0.14],
        carWidthPercentage: [0.3, 0.5],
        carShiftX: [-0.8, 0.8],
        carFloorSeparation: [0, 5],

        // Distortion parameters for the winding road effect
        distortionFreq: { x: 4, y: 8, z: 8, w: 1 },
        distortionAmp: { x: 25, y: 5, z: 10, w: 10 },

        // Colors - NodesCrypt theme (neon cyan + purple)
        colors: {
            background: 0x000000,
            leftCars: [0x00f2ff, 0x00d4ff, 0x00b8ff],   // Neon Cyan
            rightCars: [0x7000ff, 0x9000ff, 0x5500cc],  // Purple
        },

        onSpeedUp: null,
        onSlowDown: null
    };

    const config = { ...defaultOptions, ...options };

    useEffect(() => {
        if (!containerRef.current) return;

        let THREE;
        let scene, camera, renderer, clock;
        let leftCarLights, rightCarLights;
        let speedUp = 0, speedUpTarget = 0, timeOffset = 0;
        let fovTarget = config.fov;
        let disposed = false;

        const initAnimation = async () => {
            try {
                THREE = await import('three');

                // Scene setup
                scene = new THREE.Scene();
                scene.background = new THREE.Color(config.colors.background);

                // Fog for depth fade
                const fogNear = config.length * 0.2;
                const fogFar = config.length * 0.5;
                scene.fog = new THREE.Fog(config.colors.background, fogNear, fogFar);

                // Camera - positioned like original
                camera = new THREE.PerspectiveCamera(
                    config.fov,
                    containerRef.current.clientWidth / containerRef.current.clientHeight,
                    0.1,
                    10000
                );
                camera.position.set(0, 8, -5);

                // Renderer
                renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
                renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
                renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
                containerRef.current.appendChild(renderer.domElement);

                clock = new THREE.Clock();

                // Create car lights exactly like original
                leftCarLights = createCarLights(THREE, scene, config, config.colors.leftCars, config.movingAwaySpeed, true);
                rightCarLights = createCarLights(THREE, scene, config, config.colors.rightCars, config.movingCloserSpeed, false);

                // Event handlers
                const handleResize = () => {
                    if (!containerRef.current || disposed) return;
                    camera.aspect = containerRef.current.clientWidth / containerRef.current.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
                };

                const handleSpeedUp = (e) => {
                    if (disposed) return;
                    e.preventDefault();
                    speedUpTarget = config.speedUp;
                    fovTarget = config.fovSpeedUp;
                    config.onSpeedUp?.();
                };

                const handleSlowDown = () => {
                    if (disposed) return;
                    speedUpTarget = 0;
                    fovTarget = config.fov;
                    config.onSlowDown?.();
                };

                window.addEventListener('resize', handleResize);
                containerRef.current.addEventListener('mousedown', handleSpeedUp);
                containerRef.current.addEventListener('mouseup', handleSlowDown);
                containerRef.current.addEventListener('mouseleave', handleSlowDown);
                containerRef.current.addEventListener('touchstart', handleSpeedUp, { passive: false });
                containerRef.current.addEventListener('touchend', handleSlowDown);

                // Animation loop
                const animate = () => {
                    if (disposed) return;

                    const delta = clock.getDelta();
                    const elapsed = clock.getElapsedTime();

                    // Smooth speed transitions
                    const lerpFactor = Math.exp(-60 * Math.log(2) * 0.1 * delta);
                    speedUp += (speedUpTarget - speedUp) * (1 - lerpFactor);
                    timeOffset += speedUp * delta;

                    const time = elapsed + timeOffset;

                    // FOV animation
                    const fovLerp = 1 - Math.pow(0.1, delta);
                    if (Math.abs(fovTarget - camera.fov) > 0.01) {
                        camera.fov += (fovTarget - camera.fov) * fovLerp * 6;
                        camera.updateProjectionMatrix();
                    }

                    // Camera distortion - THIS creates the winding road effect
                    const distortion = getTurbulentDistortion(0.025, time, config);
                    camera.lookAt(
                        camera.position.x + distortion.x,
                        camera.position.y + distortion.y,
                        camera.position.z + distortion.z
                    );

                    // Update light uniforms
                    if (leftCarLights?.material?.uniforms?.uTime) {
                        leftCarLights.material.uniforms.uTime.value = time;
                    }
                    if (rightCarLights?.material?.uniforms?.uTime) {
                        rightCarLights.material.uniforms.uTime.value = time;
                    }

                    renderer.render(scene, camera);
                    animationRef.current = requestAnimationFrame(animate);
                };

                animate();

                // Cleanup
                animationRef.current = {
                    cleanup: () => {
                        disposed = true;
                        window.removeEventListener('resize', handleResize);
                        if (containerRef.current) {
                            containerRef.current.removeEventListener('mousedown', handleSpeedUp);
                            containerRef.current.removeEventListener('mouseup', handleSlowDown);
                            containerRef.current.removeEventListener('mouseleave', handleSlowDown);
                            containerRef.current.removeEventListener('touchstart', handleSpeedUp);
                            containerRef.current.removeEventListener('touchend', handleSlowDown);
                        }
                        renderer?.dispose();
                        scene?.clear();
                        if (containerRef.current && renderer?.domElement) {
                            containerRef.current.removeChild(renderer.domElement);
                        }
                    }
                };

            } catch (error) {
                console.error('Animation init failed:', error);
            }
        };

        initAnimation();

        return () => {
            if (animationRef.current?.cleanup) {
                animationRef.current.cleanup();
            } else if (typeof animationRef.current === 'number') {
                cancelAnimationFrame(animationRef.current);
            }
        };
    }, []);

    return (
        <div
            ref={containerRef}
            className={`test-animation-container ${className}`}
        />
    );
};

// ============================================
// Turbulent Distortion - Creates the winding road camera effect
// ============================================

function nsin(val) {
    return Math.sin(val) * 0.5 + 0.5;
}

function getTurbulentDistortion(progress, time, config) {
    const PI = Math.PI;
    const freq = config.distortionFreq;
    const amp = config.distortionAmp;

    const getX = (p) =>
        Math.cos(PI * p * freq.x + time) * amp.x +
        Math.pow(Math.cos(PI * p * freq.y + time * (freq.y / freq.x)), 2) * amp.y;

    const getY = (p) =>
        -nsin(PI * p * freq.z + time) * amp.z -
        Math.pow(nsin(PI * p * freq.w + time / (freq.z / freq.w)), 5) * amp.w;

    return {
        x: (getX(progress) - getX(progress + 0.007)) * -2,
        y: (getY(progress) - getY(progress + 0.007)) * -5,
        z: -10
    };
}

// ============================================
// Helper Functions
// ============================================

function randomInRange(range) {
    if (Array.isArray(range)) {
        return Math.random() * (range[1] - range[0]) + range[0];
    }
    return Math.random() * range;
}

function pickRandom(arr) {
    if (Array.isArray(arr)) {
        return arr[Math.floor(Math.random() * arr.length)];
    }
    return arr;
}

// ============================================
// Car Lights - Exact recreation from animation.txt
// Uses TubeGeometry along a line path (straight tubes)
// The distortion shader makes them appear to curve
// ============================================

function createCarLights(THREE, scene, config, colors, speeds, isLeft) {
    const count = config.lightPairsPerRoadWay * 2;

    // Create a straight line path (like LineCurve3 in original)
    const path = new THREE.LineCurve3(
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, 0, -1)
    );

    // TubeGeometry along the path - this is how the original works
    const baseGeometry = new THREE.TubeGeometry(path, 40, 1, 8, false);
    const instancedGeometry = new THREE.InstancedBufferGeometry().copy(baseGeometry);
    instancedGeometry.instanceCount = count;

    const laneWidth = config.roadWidth / config.lanesPerRoad;
    const colorArray = colors.map(c => new THREE.Color(c));

    const offsets = [];
    const metrics = [];
    const colorData = [];

    for (let i = 0; i < config.lightPairsPerRoadWay; i++) {
        const radius = randomInRange(config.carLightsRadius);
        const length = randomInRange(config.carLightsLength);
        const speed = randomInRange(speeds);

        // Lane positioning - exactly like original
        let lanePos = (i % config.lanesPerRoad) * laneWidth - config.roadWidth / 2 + laneWidth / 2;
        const carWidth = randomInRange(config.carWidthPercentage) * laneWidth;
        const shiftX = randomInRange(config.carShiftX) * laneWidth;
        lanePos += shiftX;

        const floor = randomInRange(config.carFloorSeparation) + radius * 1.3;
        const zOffset = -randomInRange(config.length);

        // Left headlight of car
        offsets.push(lanePos - carWidth / 2, floor, zOffset);
        metrics.push(radius, length, speed);
        const color = pickRandom(colorArray);
        colorData.push(color.r, color.g, color.b);

        // Right headlight of car
        offsets.push(lanePos + carWidth / 2, floor, zOffset);
        metrics.push(radius, length, speed);
        colorData.push(color.r, color.g, color.b);
    }

    instancedGeometry.setAttribute('aOffset', new THREE.InstancedBufferAttribute(new Float32Array(offsets), 3));
    instancedGeometry.setAttribute('aMetrics', new THREE.InstancedBufferAttribute(new Float32Array(metrics), 3));
    instancedGeometry.setAttribute('aColor', new THREE.InstancedBufferAttribute(new Float32Array(colorData), 3));

    // Fade direction based on which side (approaching vs leaving)
    const fadeVec = isLeft
        ? new THREE.Vector2(0, 1 - config.carLightsFade)  // Fade out at end
        : new THREE.Vector2(1, 0 + config.carLightsFade); // Fade out at start

    const material = new THREE.ShaderMaterial({
        uniforms: {
            uTime: { value: 0 },
            uTravelLength: { value: config.length },
            uFade: { value: fadeVec },
            // Distortion uniforms for winding road effect
            uDistortFreq: {
                value: new THREE.Vector4(
                    config.distortionFreq.x,
                    config.distortionFreq.y,
                    config.distortionFreq.z,
                    config.distortionFreq.w
                )
            },
            uDistortAmp: {
                value: new THREE.Vector4(
                    config.distortionAmp.x,
                    config.distortionAmp.y,
                    config.distortionAmp.z,
                    config.distortionAmp.w
                )
            }
        },
        vertexShader: `
            attribute vec3 aOffset;
            attribute vec3 aMetrics;
            attribute vec3 aColor;
            
            uniform float uTime;
            uniform float uTravelLength;
            uniform vec4 uDistortFreq;
            uniform vec4 uDistortAmp;
            
            varying vec3 vColor;
            varying vec2 vUv;
            
            #define PI 3.14159265359
            
            float nsin(float val) {
                return sin(val) * 0.5 + 0.5;
            }
            
            // Turbulent distortion - creates the winding road effect
            float getDistortionX(float progress) {
                return (
                    cos(PI * progress * uDistortFreq.x + uTime) * uDistortAmp.x +
                    pow(cos(PI * progress * uDistortFreq.y + uTime * (uDistortFreq.y / uDistortFreq.x)), 2.0) * uDistortAmp.y
                );
            }
            
            float getDistortionY(float progress) {
                return (
                    -nsin(PI * progress * uDistortFreq.z + uTime) * uDistortAmp.z +
                    -pow(nsin(PI * progress * uDistortFreq.w + uTime / (uDistortFreq.z / uDistortFreq.w)), 5.0) * uDistortAmp.w
                );
            }
            
            vec3 getDistortion(float progress) {
                return vec3(
                    getDistortionX(progress) - getDistortionX(0.0125),
                    getDistortionY(progress) - getDistortionY(0.0125),
                    0.0
                );
            }
            
            void main() {
                vec3 pos = position;
                float radius = aMetrics.x;
                float len = aMetrics.y;
                float speed = aMetrics.z;
                
                // Scale the tube
                pos.xy *= radius;
                pos.z *= len;
                
                // Movement along the road
                pos.z += len - mod(uTime * speed + aOffset.z, uTravelLength);
                pos.xy += aOffset.xy;
                
                // Apply distortion based on progress along road
                float progress = abs(pos.z / uTravelLength);
                pos.xyz += getDistortion(progress);
                
                vColor = aColor;
                vUv = uv;
                
                gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
            }
        `,
        fragmentShader: `
            varying vec3 vColor;
            varying vec2 vUv;
            uniform vec2 uFade;
            
            void main() {
                float alpha = smoothstep(uFade.x, uFade.y, vUv.x);
                gl_FragColor = vec4(vColor, alpha);
                if (gl_FragColor.a < 0.0001) discard;
            }
        `,
        transparent: true,
        depthWrite: false,
        blending: THREE.AdditiveBlending
    });

    const mesh = new THREE.Mesh(instancedGeometry, material);

    // Position on left or right side of road
    mesh.position.x = isLeft
        ? (-config.roadWidth / 2 - config.islandWidth / 2)
        : (config.roadWidth / 2 + config.islandWidth / 2);

    mesh.frustumCulled = false;
    scene.add(mesh);

    return mesh;
}

export default TestAnimation;
