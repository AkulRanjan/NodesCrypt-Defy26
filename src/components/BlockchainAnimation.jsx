import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import './BlockchainAnimation.css';

const BlockchainAnimation = () => {
    const containerRef = useRef(null);
    const sceneRef = useRef(null);
    const rendererRef = useRef(null);
    const animationIdRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // Configuration - colors match website theme (#3673f5 blue)
        const CONFIG = {
            colors: {
                gold: 0xFFD700,           // Yellow/gold data packets
                goldEmissive: 0xFFE55C,
                shield: 0x3673f5,
                shieldEmissive: 0x3673f5,
                attack: 0xff3333,
                attackEmissive: 0xff0000,
                wire: 0x3673f5,
                node: 0xffffff,            // White nodes
                nodeCore: 0x3673f5         // Blue core
            },
            spawnRate: 60 // Spawn attack every 60 frames
        };

        let scene, camera, renderer;
        let shieldMesh, networkGroup;
        let attacks = [];
        let particles = [];
        let networkTraffic = [];
        let nodeMeshes = []; // Store actual node meshes for world position
        let wireConnections = []; // Store wire connection info
        let frameCount = 0;

        // Drag controls
        let isDragging = false;
        let previousMouseX = 0;
        let previousMouseY = 0;
        let cameraAngleX = 0.5;
        let cameraAngleY = 0.3;
        const cameraDistance = 50;

        // Initialize scene
        const container = containerRef.current;
        const width = container.clientWidth;
        const height = container.clientHeight;

        // Scene
        scene = new THREE.Scene();
        sceneRef.current = scene;

        // Camera
        const aspect = width / height;
        const d = 60;
        camera = new THREE.OrthographicCamera(-d * aspect, d * aspect, d, -d, 1, 1000);
        camera.position.set(30, 30, 30);
        camera.lookAt(scene.position);

        // Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);
        rendererRef.current = renderer;

        // Lighting - brighter for better visibility
        const ambientLight = new THREE.AmbientLight(0xffffff, 1.0);
        scene.add(ambientLight);

        const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
        dirLight.position.set(20, 40, 20);
        dirLight.castShadow = true;
        scene.add(dirLight);

        const fillLight = new THREE.DirectionalLight(0x00f2ff, 0.4);
        fillLight.position.set(-20, 10, -20);
        scene.add(fillLight);

        // Shield - very subtle, just for impact effects
        function createShield() {
            const radius = 42;
            const geometry = new THREE.SphereGeometry(radius, 32, 32);

            const material = new THREE.MeshBasicMaterial({
                color: CONFIG.colors.shield,
                transparent: true,
                opacity: 0.03,
                side: THREE.DoubleSide,
                depthWrite: false
            });

            shieldMesh = new THREE.Mesh(geometry, material);
            shieldMesh.position.set(0, 0, 0);
            scene.add(shieldMesh);
        }

        // Create Network with proper wire connections
        function createNetworkGrid() {
            networkGroup = new THREE.Group();
            nodeMeshes = [];
            wireConnections = [];

            const nodeGeo = new THREE.BoxGeometry(3, 3, 3);
            const nodeMat = new THREE.MeshStandardMaterial({
                color: CONFIG.colors.node,
                roughness: 0.2,
                metalness: 0.8
            });

            // Create central node
            const centralNode = new THREE.Mesh(nodeGeo, nodeMat);
            centralNode.position.set(0, 0, 0);
            const centralCore = new THREE.Mesh(
                new THREE.BoxGeometry(1.5, 1.5, 1.5),
                new THREE.MeshBasicMaterial({ color: CONFIG.colors.nodeCore })
            );
            centralNode.add(centralCore);
            networkGroup.add(centralNode);
            nodeMeshes.push(centralNode);

            // Create surrounding nodes - spread out more
            const nodeCount = 18;
            for (let i = 0; i < nodeCount; i++) {
                const phi = Math.acos(2 * Math.random() - 1); // Uniform sphere distribution
                const theta = Math.random() * Math.PI * 2;
                const radius = 22 + Math.random() * 16; // Spread out: 22-38 range

                const px = radius * Math.sin(phi) * Math.cos(theta);
                const py = radius * Math.cos(phi);
                const pz = radius * Math.sin(phi) * Math.sin(theta);

                const node = new THREE.Mesh(nodeGeo.clone(), nodeMat.clone());
                node.position.set(px, py, pz);

                const core = new THREE.Mesh(
                    new THREE.BoxGeometry(1.5, 1.5, 1.5),
                    new THREE.MeshBasicMaterial({ color: CONFIG.colors.nodeCore })
                );
                node.add(core);
                networkGroup.add(node);
                nodeMeshes.push(node);
            }

            // Create wire connections and store them
            const wireMat = new THREE.MeshBasicMaterial({
                color: CONFIG.colors.wire,
                transparent: true,
                opacity: 0.5
            });

            for (let i = 0; i < nodeMeshes.length; i++) {
                const node1 = nodeMeshes[i];
                const neighbors = [];

                for (let j = 0; j < nodeMeshes.length; j++) {
                    if (i === j) continue;
                    const node2 = nodeMeshes[j];
                    const dist = node1.position.distanceTo(node2.position);
                    neighbors.push({ idx: j, dist: dist });
                }

                neighbors.sort((a, b) => a.dist - b.dist);

                const maxDist = 45; // Increased to ensure all nodes connect
                const maxConnections = 3;

                for (let k = 0; k < Math.min(neighbors.length, maxConnections); k++) {
                    if (neighbors[k].dist < maxDist) {
                        const j = neighbors[k].idx;

                        // Avoid duplicate connections
                        const exists = wireConnections.some(c =>
                            (c.from === i && c.to === j) || (c.from === j && c.to === i)
                        );

                        if (!exists) {
                            wireConnections.push({ from: i, to: j });

                            // Create visual wire
                            const node2 = nodeMeshes[j];
                            const geo = new THREE.CylinderGeometry(0.2, 0.2, neighbors[k].dist, 6);
                            const wire = new THREE.Mesh(geo, wireMat.clone());

                            wire.position.copy(node1.position).lerp(node2.position, 0.5);
                            wire.lookAt(node2.position);
                            wire.rotateX(Math.PI / 2);
                            networkGroup.add(wire);
                        }
                    }
                }
            }

            scene.add(networkGroup);
        }

        // Create Traffic Coin that follows wire path
        function createTrafficCoin(connectionIdx) {
            const connection = wireConnections[connectionIdx];
            const direction = Math.random() > 0.5 ? 1 : -1; // Random direction

            const geo = new THREE.SphereGeometry(1.2, 12, 12);
            const mat = new THREE.MeshBasicMaterial({
                color: CONFIG.colors.gold,
                transparent: true,
                opacity: 0.9
            });
            const coin = new THREE.Mesh(geo, mat);

            // Add glow effect
            const glowGeo = new THREE.SphereGeometry(1.8, 12, 12);
            const glowMat = new THREE.MeshBasicMaterial({
                color: CONFIG.colors.goldEmissive,
                transparent: true,
                opacity: 0.3
            });
            const glow = new THREE.Mesh(glowGeo, glowMat);
            coin.add(glow);

            const info = {
                mesh: coin,
                connectionIdx: connectionIdx,
                direction: direction,
                progress: direction === 1 ? 0 : 1,
                speed: 0.008 + Math.random() * 0.006
            };

            networkGroup.add(coin); // Add to network group so it rotates with network
            networkTraffic.push(info);
        }

        // Update Traffic - coins follow wire connections
        function updateTraffic() {
            // Spawn new coins
            if (networkTraffic.length < 12 && wireConnections.length > 0) {
                const randomConnection = Math.floor(Math.random() * wireConnections.length);
                createTrafficCoin(randomConnection);
            }

            for (let i = networkTraffic.length - 1; i >= 0; i--) {
                const t = networkTraffic[i];
                const conn = wireConnections[t.connectionIdx];

                t.progress += t.speed * t.direction;

                if (t.progress >= 1 || t.progress <= 0) {
                    // Reached end, find a new connection or remove
                    const currentNode = t.progress >= 1 ? conn.to : conn.from;

                    // Find connections from current node
                    const availableConnections = wireConnections
                        .map((c, idx) => ({ ...c, idx }))
                        .filter(c => c.from === currentNode || c.to === currentNode)
                        .filter(c => c.idx !== t.connectionIdx);

                    if (availableConnections.length > 0 && Math.random() > 0.2) {
                        // Continue to next wire
                        const nextConn = availableConnections[Math.floor(Math.random() * availableConnections.length)];
                        t.connectionIdx = nextConn.idx;

                        // Set direction based on which end we're at
                        if (nextConn.from === currentNode) {
                            t.direction = 1;
                            t.progress = 0;
                        } else {
                            t.direction = -1;
                            t.progress = 1;
                        }
                    } else {
                        // Remove coin
                        networkGroup.remove(t.mesh);
                        networkTraffic.splice(i, 1);
                        continue;
                    }
                }

                // Update position along the wire
                const fromNode = nodeMeshes[conn.from];
                const toNode = nodeMeshes[conn.to];
                t.mesh.position.lerpVectors(fromNode.position, toNode.position, t.progress);
            }
        }

        // Create Attack - tapered projectile
        function spawnAttack() {
            // Tapered cone shape for attacks
            const attackGeo = new THREE.ConeGeometry(1.5, 5, 8);
            const attackMat = new THREE.MeshBasicMaterial({
                color: CONFIG.colors.attack,
                transparent: true,
                opacity: 0.9
            });
            const attack = new THREE.Mesh(attackGeo, attackMat);

            // Add outer glow
            const glowGeo = new THREE.ConeGeometry(2.2, 6, 8);
            const glowMat = new THREE.MeshBasicMaterial({
                color: CONFIG.colors.attackEmissive,
                transparent: true,
                opacity: 0.3
            });
            const glow = new THREE.Mesh(glowGeo, glowMat);
            attack.add(glow);

            // Spawn from random direction around the shield
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            const spawnRadius = 70;

            const x = spawnRadius * Math.sin(phi) * Math.cos(theta);
            const y = spawnRadius * Math.cos(phi);
            const z = spawnRadius * Math.sin(phi) * Math.sin(theta);

            attack.position.set(x, y, z);

            // Point attack toward center (cone tip first)
            attack.lookAt(0, 0, 0);
            attack.rotateX(Math.PI / 2); // Align cone tip toward center

            // Direction toward center
            const targetPos = new THREE.Vector3(0, 0, 0);
            const dir = new THREE.Vector3().subVectors(targetPos, attack.position).normalize();
            const speed = 0.6 + Math.random() * 0.3;

            attack.userData = { velocity: dir.multiplyScalar(speed) };
            scene.add(attack);
            attacks.push(attack);
        }

        // Create Impact particles (no shield flash)
        function createImpact(position) {
            const particleCount = 20;
            const geo = new THREE.SphereGeometry(0.3, 6, 6);
            const mat = new THREE.MeshBasicMaterial({ color: 0xffff00 });

            for (let i = 0; i < particleCount; i++) {
                const p = new THREE.Mesh(geo, mat.clone());
                p.position.copy(position);
                const v = new THREE.Vector3(
                    (Math.random() - 0.5) * 2,
                    (Math.random() - 0.5) * 2,
                    (Math.random() - 0.5) * 2
                ).normalize().multiplyScalar(0.3 + Math.random() * 0.3);
                p.userData = { velocity: v, life: 1.0 };
                scene.add(p);
                particles.push(p);
            }
        }

        // Mouse handlers
        function onMouseDown(event) {
            isDragging = true;
            previousMouseX = event.clientX;
            previousMouseY = event.clientY;
            container.style.cursor = 'grabbing';
        }

        function onMouseUp() {
            isDragging = false;
            container.style.cursor = 'grab';
        }

        function onMouseMove(event) {
            if (isDragging) {
                const deltaX = event.clientX - previousMouseX;
                const deltaY = event.clientY - previousMouseY;

                cameraAngleX += deltaX * 0.005;
                cameraAngleY += deltaY * 0.005;

                previousMouseX = event.clientX;
                previousMouseY = event.clientY;
            }
        }

        function onMouseLeave() {
            isDragging = false;
            container.style.cursor = 'grab';
        }

        // Resize handler
        function onResize() {
            const newWidth = container.clientWidth;
            const newHeight = container.clientHeight;
            const newAspect = newWidth / newHeight;
            const d = 60;

            camera.left = -d * newAspect;
            camera.right = d * newAspect;
            camera.top = d;
            camera.bottom = -d;
            camera.updateProjectionMatrix();
            renderer.setSize(newWidth, newHeight);
        }

        // Animation loop
        function animate() {
            animationIdRef.current = requestAnimationFrame(animate);

            frameCount++;
            const time = Date.now() * 0.001;

            // Smooth camera movement - spherical coordinates for full 360° rotation
            const targetX = Math.sin(cameraAngleX) * Math.cos(cameraAngleY) * cameraDistance;
            const targetY = Math.sin(cameraAngleY) * cameraDistance;
            const targetZ = Math.cos(cameraAngleX) * Math.cos(cameraAngleY) * cameraDistance;

            camera.position.x += (targetX - camera.position.x) * 0.05;
            camera.position.y += (targetY - camera.position.y) * 0.05;
            camera.position.z += (targetZ - camera.position.z) * 0.05;
            camera.lookAt(scene.position);

            // Subtle shield pulse
            if (shieldMesh) {
                const s = 1 + Math.sin(time * 2) * 0.005;
                shieldMesh.scale.set(s, s, s);
            }

            // Slow network rotation
            if (networkGroup) {
                networkGroup.rotation.y = time * 0.05;
            }

            // Update traffic (coins following wires)
            updateTraffic();

            // Spawn attacks
            if (frameCount % CONFIG.spawnRate === 0) {
                spawnAttack();
            }

            // Update attacks
            for (let i = attacks.length - 1; i >= 0; i--) {
                const attack = attacks[i];
                attack.position.add(attack.userData.velocity);
                attack.rotation.x += 0.1;
                attack.rotation.y += 0.1;

                const dist = attack.position.length();

                // Impact at shield radius
                if (dist < 42) {
                    createImpact(attack.position);
                    scene.remove(attack);
                    attacks.splice(i, 1);
                } else if (dist > 100) {
                    // Remove if too far
                    scene.remove(attack);
                    attacks.splice(i, 1);
                }
            }

            // Update particles
            for (let i = particles.length - 1; i >= 0; i--) {
                const p = particles[i];
                p.position.add(p.userData.velocity);
                p.userData.velocity.multiplyScalar(0.95);
                p.userData.life -= 0.03;
                p.scale.setScalar(p.userData.life);
                p.material.opacity = p.userData.life;

                if (p.userData.life <= 0) {
                    scene.remove(p);
                    particles.splice(i, 1);
                }
            }

            renderer.render(scene, camera);
        }

        // Initialize
        createShield();
        createNetworkGrid();

        // Event listeners
        container.style.cursor = 'grab';
        container.addEventListener('mousedown', onMouseDown);
        container.addEventListener('mouseup', onMouseUp);
        container.addEventListener('mousemove', onMouseMove);
        container.addEventListener('mouseleave', onMouseLeave);
        window.addEventListener('resize', onResize);

        animate();

        // Cleanup
        return () => {
            if (animationIdRef.current) {
                cancelAnimationFrame(animationIdRef.current);
            }
            container.removeEventListener('mousedown', onMouseDown);
            container.removeEventListener('mouseup', onMouseUp);
            container.removeEventListener('mousemove', onMouseMove);
            container.removeEventListener('mouseleave', onMouseLeave);
            window.removeEventListener('resize', onResize);

            if (rendererRef.current) {
                rendererRef.current.dispose();
                if (container.contains(rendererRef.current.domElement)) {
                    container.removeChild(rendererRef.current.domElement);
                }
            }
        };
    }, []);

    return <div ref={containerRef} className="blockchain-animation-container"></div>;
};

export default BlockchainAnimation;
