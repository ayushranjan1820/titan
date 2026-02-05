import React, { useRef, useEffect, useState } from 'react';
import './VirtualTryOn.css';
import Watch3DRenderer from './Watch3DRenderer';

/**
 * VirtualTryOn Component
 * Uses MediaPipe Hands for wrist detection and overlays watch image
 * 
 * Supports both 2D image overlay and 3D model rendering:
 * - 2D: Fast, works with all products (legacy)
 * - 3D: Realistic strap wrapping, occlusion, lighting (selected products)
 */
function VirtualTryOn({ product, onClose }) {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [cameraActive, setCameraActive] = useState(false);
    const [handsDetected, setHandsDetected] = useState(false);
    const [watchImageLoaded, setWatchImageLoaded] = useState(false);

    // 3D rendering state
    const [use3DRendering, setUse3DRendering] = useState(false);
    const [currentLandmarks, setCurrentLandmarks] = useState(null);

    // MediaPipe Hands instance
    const handsRef = useRef(null);
    const animationFrameRef = useRef(null);
    // Use ref for watchImage so MediaPipe callbacks always get the latest value
    const watchImageRef = useRef(null);

    // Initialize camera and MediaPipe
    useEffect(() => {
        initializeTryOn();

        return () => {
            cleanup();
        };
    }, []);

    // Load watch image
    useEffect(() => {
        if (product?.image_url) {
            console.log('Loading watch image from:', product.image_url);
            const img = new Image();
            img.crossOrigin = 'anonymous';
            img.onload = () => {
                console.log('✅ Watch image loaded successfully!', {
                    width: img.width,
                    height: img.height,
                    src: img.src
                });
                // Store in ref so MediaPipe callbacks can access it
                watchImageRef.current = img;
                setWatchImageLoaded(true);
            };
            img.onerror = (e) => {
                console.error('❌ Failed to load watch image:', e);
                console.error('Image URL:', product.image_url);
                watchImageRef.current = null;
                setWatchImageLoaded(false);
            };
            img.src = product.image_url;
        }
    }, [product]);

    // Determine if we should use 3D rendering for this product
    useEffect(() => {
        if (product?.has3DModel && product?.model3D) {
            console.log('🎨 3D model available for this product:', product.model3D);
            setUse3DRendering(true);
        } else {
            console.log('📷 Using 2D image overlay for this product');
            setUse3DRendering(false);
        }
    }, [product]);

    const initializeTryOn = async () => {
        try {
            setIsLoading(true);
            setError(null);

            // Request camera access
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user',
                },
            });

            const video = videoRef.current;
            if (video) {
                video.srcObject = stream;
                video.onloadedmetadata = () => {
                    video.play();
                    setCameraActive(true);

                    // Initialize MediaPipe Hands
                    initializeMediaPipe();
                };
            }

            setIsLoading(false);
        } catch (err) {
            console.error('Camera access error:', err);
            setError(`Failed to access camera: ${err.message}`);
            setIsLoading(false);
        }
    };

    const initializeMediaPipe = async () => {
        // Wait a bit for MediaPipe to load from CDN
        await new Promise(resolve => setTimeout(resolve, 500));

        // Check if MediaPipe Hands is available
        if (typeof window.Hands === 'undefined') {
            console.warn('MediaPipe Hands not loaded. Using basic overlay instead.');
            setError('MediaPipe not available. Showing basic overlay.');
            startBasicRendering();
            return;
        }

        try {
            console.log('Initializing MediaPipe Hands...');

            const hands = new window.Hands({
                locateFile: (file) => {
                    return `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`;
                },
            });

            hands.setOptions({
                maxNumHands: 2,
                modelComplexity: 1,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5,
            });

            hands.onResults(onHandsResults);
            handsRef.current = hands;

            // Start processing video frames
            processFrame();
        } catch (err) {
            console.error('MediaPipe initialization error:', err);
            startBasicRendering();
        }
    };

    const processFrame = async () => {
        const video = videoRef.current;
        const hands = handsRef.current;

        if (video && hands && video.readyState === 4) {
            await hands.send({ image: video });
        }

        animationFrameRef.current = requestAnimationFrame(processFrame);
    };

    const onHandsResults = (results) => {
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        const video = videoRef.current;

        if (!canvas || !ctx || !video) return;

        // Set canvas size to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw vide feed
        ctx.save();
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Draw hand landmarks and watch overlay
        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            setHandsDetected(true);

            // Store current landmarks for 3D renderer
            setCurrentLandmarks(results.multiHandLandmarks[0]); // Use first detected hand

            for (const landmarks of results.multiHandLandmarks) {
                // Draw hand landmarks (optional - for debugging)
                // drawHandLandmarks(ctx, landmarks);

                // Only overlay 2D watch if not using 3D rendering
                if (!use3DRendering) {
                    overlayWatch(ctx, landmarks);
                }
            }
        } else {
            setHandsDetected(false);
            setCurrentLandmarks(null);
        }

        ctx.restore();
    };

    const overlayWatch = (ctx, landmarks) => {
        const watchImage = watchImageRef.current;
        if (!watchImage) {
            // Only log this warning occasionally
            if (!window.lastWatchWarning || Date.now() - window.lastWatchWarning > 2000) {
                console.log('⚠️ overlayWatch called but watchImage is null');
                window.lastWatchWarning = Date.now();
            }
            return;
        }

        // Log only once per second to avoid console spam
        const now = Date.now();
        if (!window.lastOverlayLog || now - window.lastOverlayLog > 1000) {
            console.log('🎯 Overlaying watch on wrist');
            window.lastOverlayLog = now;
        }

        // MediaPipe Hand Landmarks:
        // 0: Wrist
        // 5: Index finger base (metacarpophalangeal joint)
        // 9: Middle finger base
        // 17: Pinky base
        const wrist = landmarks[0];
        const indexBase = landmarks[5];
        const middleBase = landmarks[9];
        const pinkyBase = landmarks[17];

        // Convert normalized coordinates to pixel coordinates
        const wristX = wrist.x * ctx.canvas.width;
        const wristY = wrist.y * ctx.canvas.height;
        const indexX = indexBase.x * ctx.canvas.width;
        const indexY = indexBase.y * ctx.canvas.height;
        const middleX = middleBase.x * ctx.canvas.width;
        const middleY = middleBase.y * ctx.canvas.height;
        const pinkyX = pinkyBase.x * ctx.canvas.width;
        const pinkyY = pinkyBase.y * ctx.canvas.height;

        // Calculate hand width (index to pinky distance) - this represents the width of the hand
        const handWidth = Math.sqrt(
            Math.pow(pinkyX - indexX, 2) + Math.pow(pinkyY - indexY, 2)
        );

        // Calculate the knuckle center point (between index and pinky)
        const knuckleCenterX = (indexX + pinkyX) / 2;
        const knuckleCenterY = (indexY + pinkyY) / 2;

        // NEW APPROACH: Calculate the angle of the FOREARM (wrist to knuckles)
        // This represents the direction of the arm, not the hand width
        const forearmAngle = Math.atan2(knuckleCenterY - wristY, knuckleCenterX - wristX);

        // Watch should be PERPENDICULAR to the forearm direction
        // A watch naturally sits across the wrist, perpendicular to the arm
        const watchRotation = forearmAngle;

        // INCREASED watch size - real watches typically span 80-90% of wrist width
        // Using 0.85x hand width for a more realistic, visible watch
        const watchSize = handWidth * 0.85;

        // Position watch at the wrist point, slightly adjusted along the forearm direction
        // This makes the watch sit naturally on the wrist area
        const watchOffsetDistance = watchSize * 0.1;
        const watchX = wristX + Math.cos(forearmAngle) * watchOffsetDistance;
        const watchY = wristY + Math.sin(forearmAngle) * watchOffsetDistance;

        // Create a temporary canvas for processing the watch image (remove white background)
        if (!window.watchProcessedCanvas) {
            window.watchProcessedCanvas = document.createElement('canvas');
        }
        const tempCanvas = window.watchProcessedCanvas;
        const tempCtx = tempCanvas.getContext('2d');

        tempCanvas.width = watchImage.width;
        tempCanvas.height = watchImage.height;

        // Draw original watch image
        tempCtx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);
        tempCtx.drawImage(watchImage, 0, 0);

        // Get image data to remove white background
        const imageData = tempCtx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
        const data = imageData.data;

        // Remove white/light background pixels (chroma key technique)
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];

            // Check if pixel is close to white (all RGB values > 240)
            // Or if pixel is very light gray (all RGB similar and > 230)
            const isWhite = r > 240 && g > 240 && b > 240;
            const isLightGray = r > 230 && g > 230 && b > 230 &&
                Math.abs(r - g) < 10 && Math.abs(g - b) < 10;

            if (isWhite || isLightGray) {
                data[i + 3] = 0; // Set alpha to 0 (transparent)
            }
        }

        tempCtx.putImageData(imageData, 0, 0);

        // Draw shadow for depth effect
        ctx.save();
        ctx.translate(watchX, watchY);

        // KEY CHANGE: Watch rotates to be PERPENDICULAR to arm direction
        // Add 90 degrees (Math.PI/2) to make watch face perpendicular to forearm
        ctx.rotate(watchRotation + Math.PI / 2);

        // Shadow for 3D depth
        ctx.shadowColor = 'rgba(0, 0, 0, 0.4)';
        ctx.shadowBlur = 10;
        ctx.shadowOffsetX = 3;
        ctx.shadowOffsetY = 3;

        // Draw the processed watch image (with transparent background)
        ctx.drawImage(
            tempCanvas,
            -watchSize / 2,
            -watchSize / 2,
            watchSize,
            watchSize
        );

        ctx.restore();
    };

    const drawHandLandmarks = (ctx, landmarks) => {
        // Draw landmarks as circles (for debugging)
        ctx.fillStyle = 'red';
        for (const landmark of landmarks) {
            const x = landmark.x * ctx.canvas.width;
            const y = landmark.y * ctx.canvas.height;
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, 2 * Math.PI);
            ctx.fill();
        }
    };

    const startBasicRendering = () => {
        // Fallback: render video without hand detection
        const renderFrame = () => {
            const canvas = canvasRef.current;
            const video = videoRef.current;
            const ctx = canvas?.getContext('2d');

            if (canvas && video && ctx && video.readyState === 4) {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

                // Overlay watch in center (no hand detection)
                const watchImage = watchImageRef.current;
                if (watchImage) {
                    const centerX = canvas.width / 2;
                    const centerY = canvas.height / 2;
                    const size = 200;

                    ctx.globalAlpha = 0.8;
                    ctx.drawImage(watchImage, centerX - size / 2, centerY - size / 2, size, size);
                }
            }

            animationFrameRef.current = requestAnimationFrame(renderFrame);
        };

        renderFrame();
    };

    const cleanup = () => {
        // Stop camera
        const video = videoRef.current;
        if (video?.srcObject) {
            const tracks = video.srcObject.getTracks();
            tracks.forEach((track) => track.stop());
        }

        // Stop animation frame
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
        }

        // Cleanup MediaPipe
        if (handsRef.current) {
            handsRef.current.close();
        }
    };

    return (
        <div className="virtual-tryon-container">
            {/* Header */}
            <div className="tryon-header">
                <h2>Virtual Try-On</h2>
                <button className="close-button" onClick={onClose}>
                    ✕ Close
                </button>
            </div>

            {/* Product Info */}
            {product && (
                <div className="product-info-bar">
                    <img src={product.image_url} alt={product.name} className="product-thumb" />
                    <div className="product-info-text">
                        <strong>{product.name}</strong>
                        <span>₹{product.price?.toLocaleString('en-IN')}</span>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <div className="tryon-content">
                {/* Loading State */}
                {isLoading && (
                    <div className="tryon-state">
                        <div className="spinner"></div>
                        <p>Initializing camera...</p>
                    </div>
                )}

                {/* Error State */}
                {error && (
                    <div className="tryon-state error">
                        <p>❌ {error}</p>
                        <p className="error-hint">
                            Please ensure you've granted camera permissions and try again.
                        </p>
                        <button className="btn btn-primary" onClick={initializeTryOn}>
                            Retry
                        </button>
                    </div>
                )}

                {/* Video and Canvas */}
                {!isLoading && !error && (
                    <div className="video-container">
                        {/* Hidden video element */}
                        <video ref={videoRef} style={{ display: 'none' }} />

                        {/* Canvas for rendering */}
                        <canvas ref={canvasRef} className="render-canvas" />

                        {/* 3D Watch Renderer (only for products with 3D models) */}
                        {use3DRendering && currentLandmarks && product?.model3D && (
                            <Watch3DRenderer
                                landmarks={currentLandmarks}
                                canvasRef={canvasRef}
                                productId={product.id}
                                modelPath={product.model3D}
                            />
                        )}

                        {/* Status Indicator */}
                        <div className="status-indicator">
                            <div className={`status-badge ${cameraActive ? 'active' : ''}`}>
                                📷 Camera: {cameraActive ? 'Active' : 'Inactive'}
                            </div>
                            <div className={`status-badge ${handsDetected ? 'active' : ''}`}>
                                ✋ Hands: {handsDetected ? 'Detected' : 'Not Detected'}
                            </div>
                            <div className={`status-badge ${watchImageLoaded || use3DRendering ? 'active' : ''}`}>
                                ⌚ Watch: {use3DRendering ? '3D Model' : watchImageLoaded ? 'Loaded' : 'Loading...'}
                            </div>
                        </div>

                        {/* Instructions */}
                        <div className="instructions">
                            <p>👋 Hold your wrist in front of the camera</p>
                            <p className="instruction-hint">
                                Position your hand so the wrist is clearly visible
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* MediaPipe Script */}
            <script
                src="https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js"
                crossOrigin="anonymous"
            ></script>
        </div>
    );
}

export default VirtualTryOn;
