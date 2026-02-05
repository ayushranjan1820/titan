/**
 * Watch3DRenderer Component
 * Handles 3D watch rendering with Three.js for realistic virtual try-on
 */

import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { calculateWristPose } from '../utils/wristPose';
import { deformStrapToWrist, findStrapMeshes } from '../utils/strapDeformation';

const Watch3DRenderer = ({ landmarks, canvasRef, productId, modelPath }) => {
    const sceneRef = useRef(null);
    const rendererRef = useRef(null);
    const cameraRef = useRef(null);
    const watchModelRef = useRef(null);
    const strapMeshesRef = useRef([]);
    const animationFrameRef = useRef(null);
    const canvas3DRef = useRef(null);

    // Initialize Three.js scene
    useEffect(() => {
        if (!canvasRef.current || !canvas3DRef.current) return;

        const videoCanvas = canvasRef.current;
        const overlayCanvas = canvas3DRef.current;

        // Set canvas dimensions to match video canvas
        const updateCanvasSize = () => {
            if (videoCanvas.width > 0 && videoCanvas.height > 0) {
                overlayCanvas.width = videoCanvas.width;
                overlayCanvas.height = videoCanvas.height;

                if (rendererRef.current) {
                    rendererRef.current.setSize(videoCanvas.width, videoCanvas.height);
                }

                if (cameraRef.current) {
                    cameraRef.current.aspect = videoCanvas.width / videoCanvas.height;
                    cameraRef.current.updateProjectionMatrix();
                }
            }
        };

        // Create WebGL renderer with transparent background on separate canvas
        const renderer = new THREE.WebGLRenderer({
            canvas: overlayCanvas,
            alpha: true,
            antialias: true,
            preserveDrawingBuffer: true
        });

        // Initial size setup
        updateCanvasSize();
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;

        // Clear color should be fully transparent
        renderer.setClearColor(0x000000, 0);
        rendererRef.current = renderer;

        // Create scene
        const scene = new THREE.Scene();
        sceneRef.current = scene;

        // Create orthographic camera for better 2D overlay alignment
        // This eliminates perspective distortion and makes positioning easier
        const aspect = videoCanvas.width / videoCanvas.height;
        const frustumSize = 2;
        const camera = new THREE.OrthographicCamera(
            -frustumSize * aspect / 2,  // left
            frustumSize * aspect / 2,   // right
            frustumSize / 2,            // top
            -frustumSize / 2,           // bottom
            0.1,                        // near
            100                         // far
        );
        camera.position.set(0, 0, 5);
        camera.lookAt(0, 0, 0);
        cameraRef.current = camera;

        // Add lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(2, 3, 4);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 1024;
        directionalLight.shadow.mapSize.height = 1024;
        scene.add(directionalLight);

        // Add subtle fill light
        const fillLight = new THREE.DirectionalLight(0xffffff, 0.3);
        fillLight.position.set(-2, 1, -2);
        scene.add(fillLight);

        // Watch for canvas size changes
        const resizeObserver = new ResizeObserver(() => {
            updateCanvasSize();
        });
        resizeObserver.observe(videoCanvas);

        console.log('✨ Three.js scene initialized for 3D watch rendering');

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
            resizeObserver.disconnect();
            renderer.dispose();
            console.log('✨ Three.js renderer disposed');
        };
    }, [canvasRef]);

    // Load 3D watch model
    useEffect(() => {
        if (!modelPath || !sceneRef.current) return;

        const loader = new GLTFLoader();

        console.log(`📦 Loading 3D model: ${modelPath}`);

        loader.load(
            modelPath,
            (gltf) => {
                const model = gltf.scene;

                // Enable shadows for all meshes
                model.traverse((node) => {
                    if (node.isMesh) {
                        node.castShadow = true;
                        node.receiveShadow = true;

                        // Enhance materials for realism
                        if (node.material) {
                            node.material.side = THREE.FrontSide;
                        }
                    }
                });

                // Scale model appropriately (adjust based on model units)
                model.scale.set(0.1, 0.1, 0.1);

                // Find strap meshes for deformation
                const strapMeshes = findStrapMeshes(model);
                strapMeshesRef.current = strapMeshes;
                console.log(`🎨 Found ${strapMeshes.length} strap meshes for deformation`);

                sceneRef.current.add(model);
                watchModelRef.current = model;

                console.log(`✅ 3D model loaded successfully: ${modelPath}`);
            },
            (progress) => {
                const percent = (progress.loaded / progress.total * 100).toFixed(0);
                console.log(`📥 Loading model: ${percent}%`);
            },
            (error) => {
                console.error('❌ Error loading 3D model:', error);
            }
        );

        return () => {
            if (watchModelRef.current && sceneRef.current) {
                sceneRef.current.remove(watchModelRef.current);
                watchModelRef.current = null;
                strapMeshesRef.current = [];
            }
        };
    }, [modelPath]);

    // Render loop - update watch position and render
    useEffect(() => {
        if (!landmarks || !watchModelRef.current || !sceneRef.current) return;

        const render = () => {
            // Calculate wrist pose from MediaPipe landmarks
            const { position, rotationMatrix, wristRadius } = calculateWristPose(
                landmarks,
                canvasRef.current.width,
                canvasRef.current.height
            );

            // Dynamic scaling based on wrist size
            // Typical watch is about 40-50% of wrist width
            const baseScale = 0.25; // Adjusted base scale for better visibility
            const scaleFactor = wristRadius * baseScale;
            watchModelRef.current.scale.set(scaleFactor, scaleFactor, scaleFactor);

            // Position watch at wrist center
            watchModelRef.current.position.copy(position);

            // Apply wrist orientation
            watchModelRef.current.rotation.setFromRotationMatrix(rotationMatrix);

            // Rotate watch face to be perpendicular to forearm
            // The watch face should be visible when looking at the wrist
            watchModelRef.current.rotateZ(Math.PI / 2);

            // Slight offset to position watch on top of wrist surface
            const offset = new THREE.Vector3(0, 0, 0.05);
            offset.applyMatrix4(rotationMatrix);
            watchModelRef.current.position.add(offset);

            // Deform strap to wrap around wrist
            // Use slightly smaller radius for strap to fit snugly
            strapMeshesRef.current.forEach(strapMesh => {
                deformStrapToWrist(strapMesh, position, wristRadius * 0.8, rotationMatrix);
            });

            // Render scene
            rendererRef.current.render(sceneRef.current, cameraRef.current);

            // Continue render loop
            animationFrameRef.current = requestAnimationFrame(render);
        };

        render();

        return () => {
            if (animationFrameRef.current) {
                cancelAnimationFrame(animationFrameRef.current);
            }
        };
    }, [landmarks, canvasRef]);

    // Render a transparent overlay canvas for 3D rendering
    return (
        <canvas
            ref={canvas3DRef}
            style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 10
            }}
        />
    );
};

export default Watch3DRenderer;
