<template>
  <div ref="container" class="w-full h-full"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import * as THREE from 'three';

const container = ref<HTMLElement>();
let scene: THREE.Scene;
let camera: THREE.PerspectiveCamera;
let renderer: THREE.WebGLRenderer;
let animationId: number;
let buildings: Array<{ mesh: THREE.Mesh; height: number }> = [];
let floatingCrystals: THREE.Mesh[] = [];

const init = () => {
  if (!container.value) return;

  scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0x0a0e1a, 15, 60);

  camera = new THREE.PerspectiveCamera(
    50,
    container.value.clientWidth / container.value.clientHeight,
    0.1,
    1000
  );
  camera.position.set(18, 15, 18);
  camera.lookAt(0, 2, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x0a0e1a, 0);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  container.value.appendChild(renderer.domElement);

  const ambientLight = new THREE.AmbientLight(0x4f46e5, 0.3);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xa78bfa, 1.2);
  directionalLight.position.set(15, 25, 15);
  directionalLight.castShadow = true;
  directionalLight.shadow.mapSize.width = 2048;
  directionalLight.shadow.mapSize.height = 2048;
  directionalLight.shadow.camera.far = 50;
  scene.add(directionalLight);

  const pointLight1 = new THREE.PointLight(0x6366f1, 2, 30);
  pointLight1.position.set(-8, 8, -8);
  scene.add(pointLight1);

  const pointLight2 = new THREE.PointLight(0x8b5cf6, 2, 30);
  pointLight2.position.set(8, 8, 8);
  scene.add(pointLight2);

  const spotLight = new THREE.SpotLight(0x3b82f6, 3);
  spotLight.position.set(0, 20, 0);
  spotLight.angle = Math.PI / 6;
  spotLight.penumbra = 0.5;
  spotLight.castShadow = true;
  scene.add(spotLight);

  const groundGeometry = new THREE.PlaneGeometry(50, 50, 30, 30);
  const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0x1a1f3a,
    roughness: 0.9,
    metalness: 0.1,
  });
  const ground = new THREE.Mesh(groundGeometry, groundMaterial);
  ground.rotation.x = -Math.PI / 2;
  ground.position.y = -0.5;
  ground.receiveShadow = true;
  scene.add(ground);

  const vertices = groundGeometry.attributes.position.array as Float32Array;
  for (let i = 0; i < vertices.length; i += 3) {
    vertices[i + 2] = Math.sin(vertices[i] * 0.3) * Math.cos(vertices[i + 1] * 0.3) * 0.8;
  }
  groundGeometry.attributes.position.needsUpdate = true;
  groundGeometry.computeVertexNormals();

  createBuildings();
  createFloatingCrystals();
  createParticles();

  window.addEventListener('resize', handleResize);
  animate();
};

const createBuildings = () => {
  const buildingTypes = [
    { w: 2, h: 4, d: 2, color: 0x3b82f6, roofColor: 0x1e40af },
    { w: 2.5, h: 5, d: 2.5, color: 0x6366f1, roofColor: 0x4338ca },
    { w: 1.8, h: 3, d: 1.8, color: 0x8b5cf6, roofColor: 0x6d28d9 },
    { w: 1.5, h: 2.5, d: 1.5, color: 0x4f46e5, roofColor: 0x4338ca },
  ];

  const positions = [
    [-4, 0, -4],
    [4, 0, -4],
    [-6, 0, 3],
    [5, 0, 4],
    [0, 0, 6],
    [-3, 0, 0],
    [7, 0, -1],
    [-7, 0, -7],
    [3, 0, -7],
  ];

  positions.forEach((pos, i) => {
    const type = buildingTypes[i % buildingTypes.length];

    const baseGeometry = new THREE.BoxGeometry(type.w, type.h, type.d);
    const baseMaterial = new THREE.MeshStandardMaterial({
      color: type.color,
      roughness: 0.4,
      metalness: 0.6,
      emissive: type.color,
      emissiveIntensity: 0.3,
    });

    const building = new THREE.Mesh(baseGeometry, baseMaterial);
    building.position.set(pos[0], type.h / 2, pos[2]);
    building.castShadow = true;
    building.receiveShadow = true;
    buildings.push({ mesh: building, height: type.h });
    scene.add(building);

    const roofGeometry = new THREE.ConeGeometry(type.w * 0.7, type.h * 0.3, 4);
    const roofMaterial = new THREE.MeshStandardMaterial({
      color: type.roofColor,
      roughness: 0.5,
      metalness: 0.5,
    });
    const roof = new THREE.Mesh(roofGeometry, roofMaterial);
    roof.position.y = type.h * 0.65;
    roof.rotation.y = Math.PI / 4;
    roof.castShadow = true;
    building.add(roof);

    const edgesGeometry = new THREE.EdgesGeometry(baseGeometry);
    const edgesMaterial = new THREE.LineBasicMaterial({
      color: 0xc7d2fe,
      transparent: true,
      opacity: 0.8
    });
    const edges = new THREE.LineSegments(edgesGeometry, edgesMaterial);
    building.add(edges);

    for (let j = 0; j < 3; j++) {
      const windowGeometry = new THREE.BoxGeometry(type.w * 0.15, type.h * 0.12, 0.1);
      const windowMaterial = new THREE.MeshStandardMaterial({
        color: 0xfbbf24,
        emissive: 0xfbbf24,
        emissiveIntensity: 1.5,
      });
      const window1 = new THREE.Mesh(windowGeometry, windowMaterial);
      window1.position.set(type.w * 0.3, -type.h * 0.3 + j * type.h * 0.25, type.d / 2 + 0.05);
      building.add(window1);
    }
  });
};

const createFloatingCrystals = () => {
  const crystalPositions = [
    [-10, 8, -10],
    [10, 10, -8],
    [-8, 12, 10],
    [12, 9, 12],
    [0, 15, 0],
  ];

  crystalPositions.forEach((pos) => {
    const geometry = new THREE.OctahedronGeometry(0.8, 0);
    const material = new THREE.MeshStandardMaterial({
      color: 0xa78bfa,
      roughness: 0.2,
      metalness: 0.8,
      emissive: 0x8b5cf6,
      emissiveIntensity: 0.5,
      transparent: true,
      opacity: 0.9,
    });

    const crystal = new THREE.Mesh(geometry, material);
    crystal.position.set(pos[0], pos[1], pos[2]);
    crystal.castShadow = true;
    floatingCrystals.push(crystal);
    scene.add(crystal);

    const glowGeometry = new THREE.OctahedronGeometry(1.2, 0);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: 0x8b5cf6,
      transparent: true,
      opacity: 0.15,
    });
    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    crystal.add(glow);
  });
};

const createParticles = () => {
  const particles = new THREE.BufferGeometry();
  const particleCount = 200;
  const positions = new Float32Array(particleCount * 3);

  for (let i = 0; i < particleCount * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 60;
    positions[i + 1] = Math.random() * 35;
    positions[i + 2] = (Math.random() - 0.5) * 60;
  }

  particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));

  const particleMaterial = new THREE.PointsMaterial({
    color: 0xa78bfa,
    size: 0.15,
    transparent: true,
    opacity: 0.7,
    blending: THREE.AdditiveBlending,
  });

  const particleSystem = new THREE.Points(particles, particleMaterial);
  scene.add(particleSystem);
};

const animate = () => {
  animationId = requestAnimationFrame(animate);

  const time = Date.now() * 0.001;

  buildings.forEach((building, i) => {
    building.mesh.rotation.y += 0.002 * (i % 2 === 0 ? 1 : -1);
    building.mesh.position.y = Math.sin(time + i) * 0.15 + building.height / 2;
  });

  floatingCrystals.forEach((crystal, i) => {
    crystal.rotation.x += 0.01;
    crystal.rotation.y += 0.015;
    const baseY = crystal.position.y;
    crystal.position.y = baseY + Math.sin(time * 2 + i) * 0.3;
  });

  camera.position.x = Math.sin(time * 0.15) * 18;
  camera.position.z = Math.cos(time * 0.15) * 18;
  camera.position.y = 15 + Math.sin(time * 0.1) * 2;
  camera.lookAt(0, 2, 0);

  renderer.render(scene, camera);
};

const handleResize = () => {
  if (!container.value) return;
  camera.aspect = container.value.clientWidth / container.value.clientHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
};

onMounted(() => {
  init();
});

onUnmounted(() => {
  cancelAnimationFrame(animationId);
  window.removeEventListener('resize', handleResize);
  if (renderer) {
    renderer.dispose();
  }
});
</script>
