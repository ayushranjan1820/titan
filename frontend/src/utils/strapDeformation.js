/**
 * Strap Deformation Utilities
 * Implements strap mesh deformation to wrap around wrist cylinder
 */

import * as THREE from 'three';

/**
 * Deform strap mesh to wrap around wrist cylinder
 * @param {THREE.Mesh} strapMesh - The strap mesh to deform
 * @param {THREE.Vector3} wristCenter - Center of wrist cylinder
 * @param {number} wristRadius - Radius of wrist cylinder
 * @param {THREE.Matrix4} rotationMatrix - Wrist orientation matrix
 */
export const deformStrapToWrist = (strapMesh, wristCenter, wristRadius, rotationMatrix) => {
    if (!strapMesh || !strapMesh.geometry || !strapMesh.geometry.attributes.position) {
        console.warn('Invalid strap mesh for deformation');
        return;
    }

    const positionAttribute = strapMesh.geometry.attributes.position;
    const originalPositions = strapMesh.geometry.getAttribute('originalPosition');

    // Store original positions if not already stored
    if (!originalPositions) {
        strapMesh.geometry.setAttribute(
            'originalPosition',
            positionAttribute.clone()
        );
    }

    const positions = positionAttribute.array;
    const originalArray = originalPositions ? originalPositions.array : positions.slice();

    // Inverse rotation matrix for transforming to wrist space
    const inverseRotation = rotationMatrix.clone().invert();

    for (let i = 0; i < positions.length; i += 3) {
        // Get original vertex position
        const vertex = new THREE.Vector3(
            originalArray[i],
            originalArray[i + 1],
            originalArray[i + 2]
        );

        // Transform to world space
        vertex.applyMatrix4(strapMesh.matrixWorld);

        // Transform to wrist local space
        vertex.sub(wristCenter);
        vertex.applyMatrix4(inverseRotation);

        // Apply cylindrical wrapping
        // Calculate distance from wrist axis (Y axis in wrist space)
        const distFromAxis = Math.sqrt(vertex.x * vertex.x + vertex.z * vertex.z);

        if (distFromAxis > 0.001) { // Avoid division by zero
            const angle = Math.atan2(vertex.z, vertex.x);

            // Wrap onto cylinder surface
            // Use soft constraint: blend between original and cylinder surface
            const targetRadius = wristRadius;
            const blendFactor = 0.8; // How much to conform to cylinder (0 = none, 1 = full)

            const newRadius = distFromAxis * (1 - blendFactor) + targetRadius * blendFactor;

            vertex.x = newRadius * Math.cos(angle);
            vertex.z = newRadius * Math.sin(angle);
        }

        // Transform back to world space
        vertex.applyMatrix4(rotationMatrix);
        vertex.add(wristCenter);

        // Transform back to mesh local space
        vertex.applyMatrix4(strapMesh.matrixWorld.clone().invert());

        // Update vertex position
        positions[i] = vertex.x;
        positions[i + 1] = vertex.y;
        positions[i + 2] = vertex.z;
    }

    positionAttribute.needsUpdate = true;
    strapMesh.geometry.computeVertexNormals();
};

/**
 * Identify strap components in a watch model
 * @param {THREE.Object3D} watchModel - The loaded watch model
 * @returns {Array<THREE.Mesh>} - Array of strap meshes
 */
export const findStrapMeshes = (watchModel) => {
    const strapMeshes = [];

    watchModel.traverse((child) => {
        if (child.isMesh) {
            const name = child.name.toLowerCase();
            // Look for common strap naming patterns
            if (name.includes('strap') ||
                name.includes('band') ||
                name.includes('bracelet')) {
                strapMeshes.push(child);
            }
        }
    });

    return strapMeshes;
};
