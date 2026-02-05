/**
 * Wrist Pose Estimation Utilities
 * Calculates 3D position and rotation matrix from MediaPipe Hand landmarks
 */

import * as THREE from 'three';

/**
 * Calculate full 3D wrist pose from MediaPipe landmarks
 * @param {Array} landmarks - MediaPipe hand landmarks (21 points)
 * @param {number} canvasWidth - Canvas width for coordinate conversion
 * @param {number} canvasHeight - Canvas height for coordinate conversion
 * @returns {Object} - { position, rotationMatrix, wristRadius }
 */
export const calculateWristPose = (landmarks, canvasWidth, canvasHeight) => {
    // MediaPipe Hand Landmarks indices:
    // 0: Wrist
    // 5: Index finger base (MCP)
    // 9: Middle finger base (MCP)
    // 17: Pinky base (MCP)

    const wrist = landmarks[0];
    const indexBase = landmarks[5];
    const middleBase = landmarks[9];
    const pinkyBase = landmarks[17];

    // Transform MediaPipe normalized coords [0,1] to NDC [-1,1]
    // MediaPipe: (0,0) is top-left, (1,1) is bottom-right
    // WebGL NDC: (-1,1) is top-left, (1,-1) is bottom-right
    const transformToNDC = (landmark) => new THREE.Vector3(
        landmark.x * 2 - 1,        // Map [0,1] to [-1,1]
        -(landmark.y * 2 - 1),     // Flip Y axis and map to [-1,1]
        -landmark.z * 5            // Scale depth (negative for camera facing)
    );

    const wristPos = transformToNDC(wrist);
    const indexPos = transformToNDC(indexBase);
    const middlePos = transformToNDC(middleBase);
    const pinkyPos = transformToNDC(pinkyBase);

    // Calculate knuckle center (average of finger bases)
    const knuckleCenterX = (indexPos.x + middlePos.x + pinkyPos.x) / 3;
    const knuckleCenterY = (indexPos.y + middlePos.y + pinkyPos.y) / 3;
    const knuckleCenterZ = (indexPos.z + middlePos.z + pinkyPos.z) / 3;
    const knuckleCenter = new THREE.Vector3(knuckleCenterX, knuckleCenterY, knuckleCenterZ);

    // Calculate 3D orientation axes

    // Forward axis: direction from wrist to knuckles (forearm direction)
    const forward = new THREE.Vector3()
        .subVectors(knuckleCenter, wristPos)
        .normalize();

    // Right axis: direction from pinky to index (across hand)
    const right = new THREE.Vector3()
        .subVectors(indexPos, pinkyPos)
        .normalize();

    // Up axis: perpendicular to wrist surface (normal to palm)
    const up = new THREE.Vector3()
        .crossVectors(forward, right)
        .normalize();

    // Recalculate right to ensure orthogonality
    const rightOrthogonal = new THREE.Vector3()
        .crossVectors(up, forward)
        .normalize();

    // Build rotation matrix from basis vectors
    const rotationMatrix = new THREE.Matrix4();
    rotationMatrix.makeBasis(rightOrthogonal, up, forward);

    // Estimate wrist radius from hand width
    const wristWidth = indexPos.distanceTo(pinkyPos);
    const wristRadius = wristWidth / 2;

    return {
        position: wristPos,
        rotationMatrix,
        wristRadius,
        // Additional useful vectors
        forward,
        right: rightOrthogonal,
        up
    };
};

/**
 * Convert MediaPipe screen coordinates to Three.js world coordinates
 * @param {Object} landmark - MediaPipe landmark with x, y, z
 * @param {number} canvasWidth - Canvas width
 * @param {number} canvasHeight - Canvas height
 * @returns {THREE.Vector3} - World position
 */
export const landmarkToWorldPos = (landmark, canvasWidth, canvasHeight) => {
    return new THREE.Vector3(
        (landmark.x - 0.5) * 2,
        -(landmark.y - 0.5) * 2,
        landmark.z * 2
    );
};
