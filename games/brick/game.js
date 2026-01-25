import * as THREE from 'three';

const COLORS = {
    primary: 0x00f5ff,
    secondary: 0xff00ff,
    bg: 0x030308,
    brick: [0xff2e63, 0xff6b6b, 0xffe66d, 0x4ecdc4, 0x45b7d1]
};

const CONFIG = {
    paddleWidth: 2.5,
    paddleDepth: 0.5,
    paddleHeight: 0.2,
    ballRadius: 0.15,
    ballSpeed: 0.12,
    fieldWidth: 14,
    fieldDepth: 20,
    brickRows: 5,
    brickCols: 9,
    powerupDuration: 600
};

const LEVELS = [
    { rows: 4, cols: 9, pattern: 'full', ballSpeed: 0.11, transition: 'teleport' },
    { rows: 5, cols: 9, pattern: 'checkers', ballSpeed: 0.12, transition: 'fall' },
    { rows: 5, cols: 9, pattern: 'checkerboard', ballSpeed: 0.13, transition: 'teleport' },
    { rows: 6, cols: 9, pattern: 'pyramid', ballSpeed: 0.14, transition: 'fall' },
    { rows: 6, cols: 10, pattern: 'ring', ballSpeed: 0.15, transition: 'teleport' },
    { rows: 7, cols: 9, pattern: 'pillars', ballSpeed: 0.16, transition: 'fall' },
    { rows: 7, cols: 10, pattern: 'diamond', ballSpeed: 0.17, transition: 'teleport' },
    { rows: 8, cols: 9, pattern: 'waves', ballSpeed: 0.18, transition: 'fall' },
    { rows: 8, cols: 10, pattern: 'castle', ballSpeed: 0.19, transition: 'teleport' },
    { rows: 9, cols: 10, pattern: 'maze', ballSpeed: 0.21, transition: 'fall' }
];

const POWERUP_TYPES = [
    { type: 'multiball', color: 0x7bed9f, name: 'MULTI-BALL' },
    { type: 'expand', color: 0xff00ff, name: 'EXPAND' },
    { type: 'slow', color: 0x00f0ff, name: 'SLOW MO' },
    { type: 'fireball', color: 0xff4757, name: 'FIREBALL' },
    { type: 'laser', color: 0xffa502, name: 'LASER' },
    { type: 'sticky', color: 0x2ed573, name: 'STICKY' },
    { type: 'extralife', color: 0xff6b81, name: '+1 LIFE' },
    { type: 'shield', color: 0x70a1ff, name: 'SHIELD' }
];

let scene, camera, renderer;
let paddle, paddleBox;
let balls = [];
let bricks = [];
let particles = [];
let powerups = [];
let trails = [];
let lasers = [];
let laserCooldown = 0;

let score = 0;
let lives = 3;
let gameRunning = false;
let gamePaused = false;
let currentLevel = 1;
let maxLevel = 10;

let activePowerup = null;
let powerupTimer = 0;

let shieldActive = false;
let shieldMesh = null;

let mouseX = 0;

const paddleMaterial = new THREE.MeshPhysicalMaterial({
    color: COLORS.primary,
    emissive: COLORS.primary,
    emissiveIntensity: 0.4,
    metalness: 0.95,
    roughness: 0.05,
    clearcoat: 1,
    clearcoatRoughness: 0.05
});

const ballGeometry = new THREE.SphereGeometry(CONFIG.ballRadius, 32, 32);
const ballMaterial = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    metalness: 0.2,
    roughness: 0.0,
    emissive: COLORS.primary,
    emissiveIntensity: 0.5,
    clearcoat: 1,
    clearcoatRoughness: 0
});

function init() {
    scene = new THREE.Scene();
    scene.background = new THREE.Color(COLORS.bg);
    scene.fog = new THREE.Fog(COLORS.bg, 15, 35);

    camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 12, 14);
    camera.lookAt(0, 0, 0);

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    document.body.appendChild(renderer.domElement);

    setupLights();
    setupEnvironment();
    setupPaddle();

    setupEventListeners();

    renderer.setAnimationLoop(animate);
}

function setupLights() {
    const ambient = new THREE.AmbientLight(0x404060, 0.4);
    scene.add(ambient);

    const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
    mainLight.position.set(5, 18, 5);
    mainLight.castShadow = true;
    mainLight.shadow.mapSize.set(2048, 2048);
    mainLight.shadow.camera.near = 0.5;
    mainLight.shadow.camera.far = 30;
    mainLight.shadow.camera.left = -12;
    mainLight.shadow.camera.right = 12;
    mainLight.shadow.camera.top = 12;
    mainLight.shadow.camera.bottom = -12;
    scene.add(mainLight);

    const blueLight = new THREE.PointLight(COLORS.primary, 3, 25);
    blueLight.position.set(-8, 6, 4);
    scene.add(blueLight);

    const pinkLight = new THREE.PointLight(COLORS.secondary, 3, 25);
    pinkLight.position.set(8, 6, 4);
    scene.add(pinkLight);

    const rimLight = new THREE.PointLight(0xffffff, 1.5, 30);
    rimLight.position.set(0, 10, -10);
    scene.add(rimLight);
}

function setupEnvironment() {
    const grid = new THREE.GridHelper(CONFIG.fieldWidth, 20, 0x1a1a2e, 0x0f0f1a);
    grid.position.y = -0.01;
    grid.userData.grid = true;
    scene.add(grid);

    const floorGeo = new THREE.PlaneGeometry(50, 50);
    const floorMat = new THREE.MeshPhysicalMaterial({
        color: 0x080810,
        metalness: 0.85,
        roughness: 0.35,
        clearcoat: 0.6
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.02;
    floor.receiveShadow = true;
    scene.add(floor);

    const halfWidth = CONFIG.fieldWidth / 2;
    const halfDepth = CONFIG.fieldDepth / 2;

    const borderPoints = [
        new THREE.Vector3(-halfWidth, 0, -halfDepth),
        new THREE.Vector3(halfWidth, 0, -halfDepth),
        new THREE.Vector3(halfWidth, 0, halfDepth),
        new THREE.Vector3(-halfWidth, 0, halfDepth),
        new THREE.Vector3(-halfWidth, 0, -halfDepth)
    ];

    const borderGroup = new THREE.Group();
    const borderColors = [COLORS.primary, COLORS.secondary, 0x00ffff, 0xff00ff];

    for (let i = 0; i < 4; i++) {
        const borderGeo = new THREE.BufferGeometry().setFromPoints(borderPoints);
        const borderMat = new THREE.LineBasicMaterial({
            color: borderColors[i],
            transparent: true,
            opacity: 0.4 - i * 0.08,
            blending: THREE.AdditiveBlending
        });
        const border = new THREE.Line(borderGeo, borderMat);
        border.position.y = 0.01 + i * 0.005;
        const scale = 1 + i * 0.02;
        border.scale.set(scale, 1, scale);
        borderGroup.add(border);
    }

    const outerGlowGeo = new THREE.BufferGeometry().setFromPoints(borderPoints);
    const outerGlowMat = new THREE.LineBasicMaterial({
        color: COLORS.primary,
        transparent: true,
        opacity: 0.15,
        blending: THREE.AdditiveBlending
    });
    const outerGlow = new THREE.Line(outerGlowGeo, outerGlowMat);
    outerGlow.position.y = 0.02;
    outerGlow.scale.set(1.08, 1, 1.08);
    borderGroup.add(outerGlow);

    borderGroup.userData.borderGroup = true;
    scene.add(borderGroup);

    const starCount = 800;
    const starGeo = new THREE.BufferGeometry();
    const starPositions = new Float32Array(starCount * 3);
    const starColors = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        const radius = 40 + Math.random() * 40;

        starPositions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
        starPositions[i * 3 + 1] = 20 + radius * Math.sin(phi) * Math.sin(theta);
        starPositions[i * 3 + 2] = radius * Math.cos(phi);

        const color = Math.random() > 0.5 ? COLORS.primary : COLORS.secondary;
        const colorObj = new THREE.Color(color);
        starColors[i * 3] = colorObj.r;
        starColors[i * 3 + 1] = colorObj.g;
        starColors[i * 3 + 2] = colorObj.b;
    }

    starGeo.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
    starGeo.setAttribute('color', new THREE.BufferAttribute(starColors, 3));

    const starMat = new THREE.PointsMaterial({
        size: 0.15,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });
    const stars = new THREE.Points(starGeo, starMat);
    stars.userData.stars = true;
    scene.add(stars);

    const nebulaGeo = new THREE.PlaneGeometry(60, 60);
    const nebulaMat = new THREE.ShaderMaterial({
        uniforms: {
            time: { value: 0 },
            color1: { value: new THREE.Color(COLORS.primary) },
            color2: { value: new THREE.Color(COLORS.secondary) }
        },
        vertexShader: `
            varying vec2 vUv;
            void main() {
                vUv = uv;
                gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
            }
        `,
        fragmentShader: `
            uniform float time;
            uniform vec3 color1;
            uniform vec3 color2;
            varying vec2 vUv;
            
            float noise(vec2 p) {
                return sin(p.x * 10.0 + time) * sin(p.y * 10.0 + time * 0.5);
            }
            
            void main() {
                vec2 pos = vUv * 2.0 - 1.0;
                float dist = length(pos);
                float alpha = smoothstep(1.0, 0.0, dist) * 0.15;
                float n = noise(pos * 0.5 + time * 0.1);
                vec3 color = mix(color1, color2, n + 0.5);
                gl_FragColor = vec4(color, alpha * (0.5 + n * 0.3));
            }
        `,
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        side: THREE.DoubleSide
    });
    const nebula = new THREE.Mesh(nebulaGeo, nebulaMat);
    nebula.rotation.x = -Math.PI / 2;
    nebula.position.y = -15;
    nebula.userData.nebula = true;
    scene.add(nebula);

    const floatingParticles = [];
    for (let i = 0; i < 50; i++) {
        const angle = Math.random() * Math.PI * 2;
        const radius = CONFIG.fieldWidth / 2 + 2 + Math.random() * 3;
        const particleGeo = new THREE.SphereGeometry(0.03 + Math.random() * 0.02, 8, 8);
        const particleMat = new THREE.MeshBasicMaterial({
            color: Math.random() > 0.5 ? COLORS.primary : COLORS.secondary,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending
        });
        const particle = new THREE.Mesh(particleGeo, particleMat);
        particle.position.set(
            Math.cos(angle) * radius,
            Math.random() * 2,
            (Math.random() - 0.5) * CONFIG.fieldDepth
        );
        particle.userData.floatingParticle = true;
        particle.userData.offset = Math.random() * Math.PI * 2;
        particle.userData.speed = 0.5 + Math.random() * 0.5;
        floatingParticles.push(particle);
        scene.add(particle);
    }
}

function setupPaddle() {
    const paddleGroup = new THREE.Group();

    const mainBody = new THREE.CapsuleGeometry(CONFIG.paddleHeight / 2, CONFIG.paddleWidth - CONFIG.paddleHeight, 8, 16);
    const bodyMesh = new THREE.Mesh(mainBody, paddleMaterial);
    bodyMesh.rotation.z = Math.PI / 2;
    bodyMesh.castShadow = true;
    bodyMesh.receiveShadow = true;
    paddleGroup.add(bodyMesh);

    const glowGeo = new THREE.CapsuleGeometry(CONFIG.paddleHeight / 2 + 0.03, CONFIG.paddleWidth - CONFIG.paddleHeight + 0.06, 8, 16);
    const glowMat = new THREE.MeshBasicMaterial({
        color: COLORS.primary,
        transparent: true,
        opacity: 0.3
    });
    const glowMesh = new THREE.Mesh(glowGeo, glowMat);
    glowMesh.rotation.z = Math.PI / 2;
    paddleGroup.add(glowMesh);

    paddle = paddleGroup;
    paddle.position.y = CONFIG.paddleHeight / 2;
    paddle.position.z = 8;
    scene.add(paddle);

    paddleBox = new THREE.Box3();
}

function createBall(position, velocity) {
    const ball = new THREE.Mesh(ballGeometry, ballMaterial.clone());
    ball.position.copy(position);
    ball.castShadow = true;
    ball.userData = {
        velocity: velocity.clone(),
        active: false,
        stuck: false
    };
    scene.add(ball);
    balls.push(ball);
    return ball;
}

function setupBricks() {
    clearBricks();

    const levelConfig = LEVELS[currentLevel - 1];
    const brickRows = levelConfig.rows;
    const brickCols = levelConfig.cols;

    const brickWidth = 1.2;
    const brickHeight = 0.4;
    const brickDepth = 0.55;
    const gapX = 0.2;
    const gapZ = 0.2;
    const radius = 0.08;

    const totalWidth = brickCols * brickWidth + (brickCols - 1) * gapX;
    const totalDepth = brickRows * brickDepth + (brickRows - 1) * gapZ;

    const startX = -totalWidth / 2 + brickWidth / 2;
    const startZ = -totalDepth / 2 - 3;

    const shape = new THREE.Shape();
    const w = brickWidth - radius * 2;
    const d = brickDepth - radius * 2;
    shape.moveTo(-brickWidth / 2 + radius, -brickDepth / 2);
    shape.lineTo(brickWidth / 2 - radius, -brickDepth / 2);
    shape.quadraticCurveTo(brickWidth / 2, -brickDepth / 2, brickWidth / 2, -brickDepth / 2 + radius);
    shape.lineTo(brickWidth / 2, brickDepth / 2 - radius);
    shape.quadraticCurveTo(brickWidth / 2, brickDepth / 2, brickWidth / 2 - radius, brickDepth / 2);
    shape.lineTo(-brickWidth / 2 + radius, brickDepth / 2);
    shape.quadraticCurveTo(-brickWidth / 2, brickDepth / 2, -brickWidth / 2, brickDepth / 2 - radius);
    shape.lineTo(-brickWidth / 2, -brickDepth / 2 + radius);
    shape.quadraticCurveTo(-brickWidth / 2, -brickDepth / 2, -brickWidth / 2 + radius, -brickDepth / 2);

    const extrudeSettings = {
        steps: 1,
        depth: brickHeight,
        bevelEnabled: true,
        bevelThickness: radius * 0.5,
        bevelSize: radius * 0.5,
        bevelSegments: 3
    };

    const brickGeometry = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    brickGeometry.rotateX(Math.PI / 2);

    const pattern = levelConfig.pattern;
    const transition = levelConfig.transition || 'teleport';

    let brickIndex = 0;

    for (let row = 0; row < brickRows; row++) {
        for (let col = 0; col < brickCols; col++) {
            let shouldCreate = true;
            let hits = 1;

            if (pattern === 'checkers' || pattern === 'checkerboard') {
                shouldCreate = (row + col) % 2 === 0;
                hits = (row < 2) ? 2 : 1;
            } else if (pattern === 'pyramid') {
                const centerCol = (brickCols - 1) / 2;
                const distFromCenter = Math.abs(col - centerCol);
                shouldCreate = row >= distFromCenter;
                hits = (row === distFromCenter) ? 2 : 1;
            } else if (pattern === 'diamond') {
                const centerCol = (brickCols - 1) / 2;
                const centerRow = (brickRows - 1) / 2;
                const dist = Math.abs(col - centerCol) + Math.abs(row - centerRow);
                shouldCreate = dist <= 4;
                hits = (dist <= 1) ? 2 : 1;
            } else if (pattern === 'maze') {
                const mazePattern = [
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                    [1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
                    [1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
                    [1, 0, 1, 1, 1, 1, 0, 1, 0, 1],
                    [1, 0, 0, 0, 0, 1, 0, 1, 0, 1],
                    [1, 1, 1, 1, 0, 1, 0, 0, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 1, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
                ];
                shouldCreate = mazePattern[row % 9] && mazePattern[row % 9][col] === 1;
                hits = (row === 0 || row === brickRows - 1) ? 2 : 1;
            } else if (pattern === 'pillars') {
                shouldCreate = col % 2 === 0;
                hits = (row % 3 === 0) ? 2 : 1;
            } else if (pattern === 'ring') {
                const centerCol = (brickCols - 1) / 2;
                const centerRow = (brickRows - 1) / 2;
                const dx = col - centerCol;
                const dy = row - centerRow;
                const dist = Math.sqrt(dx * dx + dy * dy);
                shouldCreate = dist > 1.5 && dist < 4.5;
                hits = 1;
            } else if (pattern === 'waves') {
                shouldCreate = Math.sin(col * 0.8 + row * 0.5) > -0.2;
                hits = 1;
            } else if (pattern === 'castle') {
                // Castle battlements and walls
                if (row === 0) {
                    shouldCreate = col % 2 === 0; // Battlements
                    hits = 2;
                } else if (row === brickRows - 1) {
                    shouldCreate = true; // Base
                    hits = 2;
                } else {
                    // Walls on sides and a central keep
                    const isSide = col === 0 || col === brickCols - 1;
                    const isKeep = col >= Math.floor(brickCols/2) - 1 && col <= Math.floor(brickCols/2) + 1 && row > 2;
                    shouldCreate = isSide || isKeep;
                    hits = isKeep ? 2 : 1;
                }
            } else {
                hits = (row === 0) ? 2 : 1;
            }

            if (!shouldCreate) continue;

            const color = COLORS.brick[row % COLORS.brick.length];
            const material = new THREE.MeshPhysicalMaterial({
                color: color,
                emissive: color,
                emissiveIntensity: 0.25,
                metalness: 0.4,
                roughness: 0.2,
                clearcoat: 0.8,
                clearcoatRoughness: 0.1
            });

            const brick = new THREE.Mesh(brickGeometry, material);
            const targetX = startX + col * (brickWidth + gapX);
            const targetY = brickHeight / 2;
            const targetZ = startZ + row * (brickDepth + gapZ);

            brick.position.set(targetX, targetY, targetZ);
            brick.castShadow = true;
            brick.receiveShadow = true;

            // Animation Setup
            brick.userData = {
                hits: hits,
                points: (brickRows - row) * 100 + (hits - 1) * 50,
                color: color,
                row: row,
                col: col,
                originalY: targetY,
                targetPos: new THREE.Vector3(targetX, targetY, targetZ),
                transitionCtx: {
                    type: transition,
                    progress: 0,
                    delay: brickIndex * 0.03,
                    active: true
                }
            };

            if (transition === 'teleport') {
                brick.scale.set(0, 0, 0);
            } else if (transition === 'fall') {
                brick.position.y = 20 + Math.random() * 5;
            }

            scene.add(brick);
            bricks.push(brick);
            brickIndex++;
        }
    }
}

function clearBricks() {
    bricks.forEach(brick => scene.remove(brick));
    bricks.length = 0;
}

function createParticles(position, color, count = 12) {
    const geo = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const velocities = [];

    for (let i = 0; i < count; i++) {
        positions[i * 3] = position.x;
        positions[i * 3 + 1] = position.y;
        positions[i * 3 + 2] = position.z;

        velocities.push(new THREE.Vector3(
            (Math.random() - 0.5) * 0.15,
            Math.random() * 0.15,
            (Math.random() - 0.5) * 0.15
        ));
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const mat = new THREE.PointsMaterial({
        color: color,
        size: 0.08,
        transparent: true,
        opacity: 1,
        blending: THREE.AdditiveBlending
    });

    const particleSystem = new THREE.Points(geo, mat);
    particleSystem.userData = {
        velocities: velocities,
        life: 1
    };
    scene.add(particleSystem);
    particles.push(particleSystem);
}

function createTrail(position) {
    const geo = new THREE.SphereGeometry(0.03, 8, 8);
    const mat = new THREE.MeshBasicMaterial({
        color: COLORS.primary,
        transparent: true,
        opacity: 0.6,
        blending: THREE.AdditiveBlending
    });
    const trail = new THREE.Mesh(geo, mat);
    trail.position.copy(position);
    trail.userData = {
        life: 1,
        scale: 1
    };
    scene.add(trail);
    trails.push(trail);
}

function createPowerup(position) {
    const powerupType = POWERUP_TYPES[Math.floor(Math.random() * POWERUP_TYPES.length)];

    const group = new THREE.Group();

    const coreGeo = new THREE.OctahedronGeometry(0.18, 0);
    const coreMat = new THREE.MeshPhysicalMaterial({
        color: powerupType.color,
        emissive: powerupType.color,
        emissiveIntensity: 0.8,
        metalness: 0.8,
        roughness: 0.1,
        clearcoat: 1
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    group.add(core);

    const ringGeo = new THREE.TorusGeometry(0.25, 0.03, 8, 32);
    const ringMat = new THREE.MeshBasicMaterial({
        color: powerupType.color,
        transparent: true,
        opacity: 0.5
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2;
    group.add(ring);

    group.position.copy(position);
    group.userData = {
        type: powerupType.type,
        name: powerupType.name,
        velocity: new THREE.Vector3(0, 0, 0.06),
        core: core,
        ring: ring
    };
    scene.add(group);
    powerups.push(group);
}

function createLaser(position) {
    const geo = new THREE.CapsuleGeometry(0.12, 0.8, 4, 8);
    const mat = new THREE.MeshBasicMaterial({
        color: 0xffa502,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });
    const laser = new THREE.Mesh(geo, mat);
    laser.rotation.x = Math.PI / 2;
    laser.position.copy(position);
    scene.add(laser);
    lasers.push(laser);
}

function activatePowerup(type) {
    activePowerup = type;
    powerupTimer = CONFIG.powerupDuration;

    const indicator = document.getElementById('powerup-indicator');
    const name = document.getElementById('powerup-name');
    indicator.classList.add('active');

    const powerupNames = {
        multiball: 'MULTI-BALL',
        expand: 'EXPAND',
        slow: 'SLOW MO',
        fireball: 'FIREBALL',
        laser: 'LASER',
        sticky: 'STICKY',
        extralife: '+1 LIFE',
        shield: 'SHIELD'
    };
    name.textContent = powerupNames[type];

    switch (type) {
        case 'expand':
            paddle.scale.set(1.5, 1, 1);
            break;
        case 'slow':
            balls.forEach(ball => {
                if (ball.userData.active) {
                    ball.userData.velocity.multiplyScalar(0.6);
                }
            });
            break;
        case 'multiball':
            const activeBalls = balls.filter(b => b.userData.active);
            if (activeBalls.length > 0 && activeBalls.length < 5) {
                const sourceBall = activeBalls[0];
                const newVel1 = sourceBall.userData.velocity.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), 0.3);
                const newVel2 = sourceBall.userData.velocity.clone().applyAxisAngle(new THREE.Vector3(0, 1, 0), -0.3);
                createBall(sourceBall.position.clone(), newVel1).userData.active = true;
                createBall(sourceBall.position.clone(), newVel2).userData.active = true;
            }
            break;
        case 'fireball':
            balls.forEach(ball => {
                if (ball.userData.active) {
                    ball.material.emissive.setHex(0xff4757);
                    ball.material.emissiveIntensity = 1;
                }
            });
            break;
        case 'laser':
            laserCooldown = 0;
            break;
        case 'sticky':
            balls.forEach(ball => {
                ball.userData.sticky = true;
            });
            break;
        case 'extralife':
            lives++;
            updateLives();
            activePowerup = null;
            document.getElementById('powerup-indicator').classList.remove('active');
            return;
        case 'shield':
            if (!shieldActive) {
                shieldActive = true;
                const shieldGeo = new THREE.BoxGeometry(CONFIG.fieldWidth, 0.5, 0.5);
                const shieldMat = new THREE.MeshPhysicalMaterial({
                    color: 0x70a1ff,
                    transparent: true,
                    opacity: 0.3,
                    emissive: 0x70a1ff,
                    emissiveIntensity: 0.4,
                    blending: THREE.AdditiveBlending
                });
                shieldMesh = new THREE.Mesh(shieldGeo, shieldMat);
                shieldMesh.position.set(0, 0, 9);
                scene.add(shieldMesh);
            }
            // Shield is an instant/state powerup, doesn't use the timer or replace active powerup
            activePowerup = null;
            document.getElementById('powerup-indicator').classList.remove('active');
            return;
    }
}

function deactivatePowerup() {
    if (!activePowerup) return;

    switch (activePowerup) {
        case 'expand':
            paddle.scale.set(1, 1, 1);
            break;
        case 'slow':
            balls.forEach(ball => {
                if (ball.userData.active) {
                    ball.userData.velocity.multiplyScalar(1.67);
                }
            });
            break;
        case 'fireball':
            balls.forEach(ball => {
                ball.material.emissive.setHex(COLORS.primary);
                ball.material.emissiveIntensity = 0.5;
            });
            break;
        case 'laser':
            break;
        case 'sticky':
            balls.forEach(ball => {
                ball.userData.sticky = false;
            });
            break;
        case 'shield':
            if (shieldMesh) {
                scene.remove(shieldMesh);
                shieldMesh = null;
                shieldActive = false;
            }
            break;
    }

    activePowerup = null;
    document.getElementById('powerup-indicator').classList.remove('active');
}

function checkCollisions(ball) {
    const ballPos = ball.position;
    const ballRadius = CONFIG.ballRadius;

    paddleBox.setFromObject(paddle);

    if (ball.userData.velocity.z > 0 && paddleBox.intersectsSphere(new THREE.Sphere(ballPos, ballRadius))) {
        let relativeX = (ballPos.x - paddle.position.x) / (CONFIG.paddleWidth * paddle.scale.x / 2);
        relativeX = THREE.MathUtils.clamp(relativeX, -1, 1);

        const angle = relativeX * (Math.PI / 3);
        const speed = ball.userData.velocity.length();

        if (ball.userData.sticky && activePowerup === 'sticky') {
            ball.userData.active = false;
            ball.position.x = paddle.position.x;
            ball.position.z = paddle.position.z - 0.5;
            ball.userData.velocity.set(0, 0, -CONFIG.ballSpeed);
        } else {
            ball.userData.velocity.set(
                Math.sin(angle) * speed,
                0,
                -Math.abs(Math.cos(angle) * speed)
            );
        }

        ball.position.z = paddle.position.z - CONFIG.paddleDepth / 2 - ballRadius - 0.01;

        createParticles(ball.position, COLORS.primary, 8);
        return;
    }

    if (shieldActive && ball.position.z > 8.5 && ball.userData.velocity.z > 0) {
        ball.userData.velocity.z *= -1;
        ball.position.z = 8.5 - ballRadius - 0.01;
        createParticles(ball.position, 0x70a1ff, 8);
        
        // Remove shield after use (one-time save)
        if (shieldMesh) {
            scene.remove(shieldMesh);
            shieldMesh = null;
        }
        shieldActive = false;
        
        return;
    }

    for (let i = bricks.length - 1; i >= 0; i--) {
        const brick = bricks[i];
        const brickBox = new THREE.Box3().setFromObject(brick);

        if (brickBox.intersectsSphere(new THREE.Sphere(ballPos, ballRadius))) {
            const isFireball = activePowerup === 'fireball';

            if (!isFireball) {
                const brickCenter = new THREE.Vector3();
                brickBox.getCenter(brickCenter);

                const dx = ballPos.x - brickCenter.x;
                const dz = ballPos.z - brickCenter.z;

                const brickHalfX = (brickBox.max.x - brickBox.min.x) / 2;
                const brickHalfZ = (brickBox.max.z - brickBox.min.z) / 2;

                const overlapX = brickHalfX - Math.abs(dx);
                const overlapZ = brickHalfZ - Math.abs(dz);

                if (overlapX < overlapZ) {
                    ball.userData.velocity.x *= -1;
                } else {
                    ball.userData.velocity.z *= -1;
                }
            }

            brick.userData.hits--;

            if (brick.userData.hits <= 0) {
                createParticles(brick.position, brick.userData.color, 20);

                if (Math.random() < 0.18) {
                    createPowerup(brick.position.clone());
                }

                score += brick.userData.points;
                updateScore();
                scene.remove(brick);
                bricks.splice(i, 1);

                if (bricks.length === 0) {
                    if (currentLevel < maxLevel) {
                        currentLevel++;
                        startLevel();
                    } else {
                        endGame(true);
                    }
                }
            } else {
                brick.material.emissiveIntensity += 0.3;
                createParticles(ball.position, brick.userData.color, 8);
            }

            if (!isFireball) return;
        }
    }

    const halfWidth = CONFIG.fieldWidth / 2;
    const halfDepth = CONFIG.fieldDepth / 2;

    if (ballPos.x > halfWidth - ballRadius) {
        ballPos.x = halfWidth - ballRadius;
        ball.userData.velocity.x *= -1;
    } else if (ballPos.x < -halfWidth + ballRadius) {
        ballPos.x = -halfWidth + ballRadius;
        ball.userData.velocity.x *= -1;
    }

    if (ballPos.z < -halfDepth + ballRadius) {
        ballPos.z = -halfDepth + ballRadius;
        ball.userData.velocity.z *= -1;
    }
}

function setupEventListeners() {
    document.getElementById('start-btn').addEventListener('click', startGame);
    document.getElementById('restart-btn').addEventListener('click', startGame);

    document.addEventListener('mousemove', (e) => {
        mouseX = ((e.clientX / window.innerWidth) * 2 - 1) * (CONFIG.fieldWidth / 2 - CONFIG.paddleWidth / 2);
    });

    document.addEventListener('click', () => {
        if (gameRunning && !gamePaused) {
            launchBalls();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.code === 'KeyP' && gameRunning) {
            gamePaused = !gamePaused;
        }
        if (e.code === 'Space' && gameRunning && !gamePaused) {
            launchBalls();
        }
    });

    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}

function startGame() {
    score = 0;
    lives = 3;
    currentLevel = 1;
    gameRunning = true;
    gamePaused = false;
    activePowerup = null;
    powerupTimer = 0;
    shieldActive = false;
    if (shieldMesh) {
        scene.remove(shieldMesh);
        shieldMesh = null;
    }

    updateScore();
    updateLives();

    document.getElementById('start-screen').classList.remove('active');
    document.getElementById('gameover-screen').classList.remove('active');
    document.getElementById('powerup-indicator').classList.remove('active');

    clearBalls();
    setupBricks();

    paddle.scale.set(1, 1, 1);

    const levelConfig = LEVELS[currentLevel - 1];
    const ball = createBall(new THREE.Vector3(0, CONFIG.ballRadius, 7.5), new THREE.Vector3(0, 0, -levelConfig.ballSpeed));
    ball.userData.active = false;
}

function startLevel() {
    clearBalls();
    setupBricks();

    paddle.scale.set(1, 1, 1);

    const levelConfig = LEVELS[currentLevel - 1];
    const ball = createBall(new THREE.Vector3(0, CONFIG.ballRadius, 7.5), new THREE.Vector3(0, 0, -levelConfig.ballSpeed));
    ball.userData.active = false;
}

function clearBalls() {
    balls.forEach(ball => scene.remove(ball));
    balls.length = 0;
    lasers.forEach(l => scene.remove(l));
    lasers.length = 0;
    trails.forEach(trail => scene.remove(trail));
    trails.length = 0;
}

function launchBalls() {
    balls.forEach(ball => {
        if (!ball.userData.active) {
            ball.userData.active = true;
            const angle = (Math.random() - 0.5) * 0.5;
            ball.userData.velocity.set(
                angle * CONFIG.ballSpeed,
                0,
                -CONFIG.ballSpeed
            ).normalize().multiplyScalar(CONFIG.ballSpeed);
        }
    });
}

function updateScore() {
    document.getElementById('score').textContent = score;
}

function updateLives() {
    document.getElementById('lives').textContent = lives;
}

function endGame(won) {
    gameRunning = false;
    trails.forEach(trail => scene.remove(trail));
    trails.length = 0;
    document.getElementById('gameover-title').textContent = won ? 'YOU WIN!' : 'GAME OVER';
    document.getElementById('final-score').textContent = score;
    document.getElementById('gameover-screen').classList.add('active');
}

function update(time) {
    const t = time * 0.001;

    bricks.forEach((brick, i) => {
        const trans = brick.userData.transitionCtx;

        if (trans && trans.active) {
            trans.delay -= 0.016;
            if (trans.delay <= 0) {
                trans.progress += 0.02;
                if (trans.progress > 1) {
                    trans.progress = 1;
                    trans.active = false;
                }

                const p = trans.progress;
                // Elastic ease out
                const ease = p === 0 ? 0 : p === 1 ? 1 : Math.pow(2, -10 * p) * Math.sin((p * 10 - 0.75) * (2 * Math.PI) / 3) + 1;
                const smoothEase = p * (2 - p);

                if (trans.type === 'teleport') {
                    brick.scale.setScalar(ease);
                } else if (trans.type === 'fall') {
                    brick.position.y = THREE.MathUtils.lerp(20, brick.userData.originalY, ease);
                }

                if (trans.progress === 1) {
                    createParticles(brick.position, brick.userData.color, 4);
                }
            }
        } else {
            const row = Math.floor(i / CONFIG.brickCols);
            brick.position.y = brick.userData.hits === 2 ? 0.25 : brick.userData.originalY + Math.sin(t * 2 + row * 0.5) * 0.02;
        }
    });

    if (!gameRunning || gamePaused) return;

    paddle.position.x = THREE.MathUtils.lerp(paddle.position.x, mouseX, 0.15);
    paddle.position.x = THREE.MathUtils.clamp(
        paddle.position.x,
        -CONFIG.fieldWidth / 2 + CONFIG.paddleWidth * paddle.scale.x / 2,
        CONFIG.fieldWidth / 2 - CONFIG.paddleWidth * paddle.scale.x / 2
    );

    const targetCamX = mouseX * 0.15;
    camera.position.x = THREE.MathUtils.lerp(camera.position.x, targetCamX, 0.05);
    camera.lookAt(0, 0, 0);

    for (let i = balls.length - 1; i >= 0; i--) {
        const ball = balls[i];

        if (!ball.userData.active) {
            ball.position.x = paddle.position.x;
            ball.material.emissiveIntensity = 0.5 + Math.sin(t * 3) * 0.2;
            continue;
        }

        ball.position.add(ball.userData.velocity);

        const speed = ball.userData.velocity.length();
        ball.material.emissiveIntensity = 0.5 + speed * 2 + Math.sin(t * 5) * 0.3;

        if (speed > 0.05) {
            createTrail(ball.position.clone());
        }

        checkCollisions(ball);

        if (ball.position.z > CONFIG.fieldDepth / 2 + 2) {
            scene.remove(ball);
            balls.splice(i, 1);
        }
    }

    if (balls.length === 0 && lives > 0) {
        lives--;
        updateLives();

        if (lives > 0) {
            deactivatePowerup();
            // Also force remove shield if it exists (shouldn't if logic is correct, but safe fallback)
            if (shieldMesh) {
                scene.remove(shieldMesh);
                shieldMesh = null;
                shieldActive = false;
            }
            const levelConfig = LEVELS[currentLevel - 1];
            const ball = createBall(new THREE.Vector3(0, CONFIG.ballRadius, 7.5), new THREE.Vector3(0, 0, -levelConfig.ballSpeed));
            ball.userData.active = false;
        } else {
            endGame(false);
        }
    }

    // Laser Logic
    if (activePowerup === 'laser' && gameRunning && !gamePaused) {
        laserCooldown--;
        if (laserCooldown <= 0) {
            createLaser(paddle.position.clone().add(new THREE.Vector3(-0.9, 0, -0.6)));
            createLaser(paddle.position.clone().add(new THREE.Vector3(0.9, 0, -0.6)));
            laserCooldown = 25;
        }
    }

    for (let i = lasers.length - 1; i >= 0; i--) {
        const laser = lasers[i];
        laser.position.z -= 0.5;

        let hit = false;

        for (let j = bricks.length - 1; j >= 0; j--) {
            const brick = bricks[j];
            // Simple distance check mostly works for capsules/boxes this size
            const dx = Math.abs(laser.position.x - brick.position.x);
            const dz = Math.abs(laser.position.z - brick.position.z);

            if (dx < 0.8 && dz < 0.5) {
                brick.userData.hits--;
                createParticles(brick.position, brick.userData.color, 10);

                if (brick.userData.hits <= 0) {
                    if (Math.random() < 0.18) createPowerup(brick.position.clone());
                    score += brick.userData.points;
                    updateScore();
                    scene.remove(brick);
                    bricks.splice(j, 1);

                    if (bricks.length === 0) {
                        if (currentLevel < maxLevel) {
                            currentLevel++;
                            startLevel();
                            return;
                        } else {
                            endGame(true);
                            return;
                        }
                    }
                } else {
                    brick.material.emissiveIntensity += 0.3;
                }

                hit = true;
                break;
            }
        }

        if (hit || laser.position.z < -CONFIG.fieldDepth / 2 - 2) {
            scene.remove(laser);
            lasers.splice(i, 1);
        }
    }

    for (let i = particles.length - 1; i >= 0; i--) {
        const ps = particles[i];
        const positions = ps.geometry.attributes.position.array;

        for (let j = 0; j < ps.userData.velocities.length; j++) {
            positions[j * 3] += ps.userData.velocities[j].x;
            positions[j * 3 + 1] += ps.userData.velocities[j].y;
            positions[j * 3 + 2] += ps.userData.velocities[j].z;

            ps.userData.velocities[j].y -= 0.003;
        }

        ps.geometry.attributes.position.needsUpdate = true;
        ps.userData.life -= 0.02;
        ps.material.opacity = ps.userData.life;

        if (ps.userData.life <= 0) {
            scene.remove(ps);
            particles.splice(i, 1);
        }
    }

    for (let i = trails.length - 1; i >= 0; i--) {
        const trail = trails[i];
        trail.userData.life -= 0.03;
        trail.userData.scale *= 0.92;
        trail.scale.setScalar(trail.userData.scale);
        trail.material.opacity = trail.userData.life * 0.6;

        if (trail.userData.life <= 0) {
            scene.remove(trail);
            trails.splice(i, 1);
        }
    }

    for (let i = powerups.length - 1; i >= 0; i--) {
        const powerup = powerups[i];
        powerup.position.add(powerup.userData.velocity);
        powerup.userData.core.rotation.x += 0.03;
        powerup.userData.core.rotation.y += 0.05;
        powerup.userData.ring.rotation.z += 0.02;
        powerup.userData.ring.rotation.x = Math.PI / 2 + Math.sin(t * 3) * 0.3;

        const paddleBox = new THREE.Box3().setFromObject(paddle);
        const powerupBox = new THREE.Box3().setFromObject(powerup);

        if (paddleBox.intersectsBox(powerupBox)) {
            activatePowerup(powerup.userData.type);
            createParticles(powerup.position, powerup.userData.core.material.color, 15);
            scene.remove(powerup);
            powerups.splice(i, 1);
        } else if (powerup.position.z > 12) {
            scene.remove(powerup);
            powerups.splice(i, 1);
        }
    }

    if (powerupTimer > 0) {
        powerupTimer--;
        const progress = (powerupTimer / CONFIG.powerupDuration) * 100;
        document.getElementById('powerup-progress').style.width = progress + '%';

        if (powerupTimer <= 0) {
            deactivatePowerup();
        }
    }
}

function animate(time) {
    update(time);

    const t = time * 0.001;
    const pulse = Math.sin(t * 3) * 0.1 + 0.9;
    if (paddle) {
        paddle.children[1].material.opacity = 0.3 * pulse;
    }

    if (shieldMesh) {
        shieldMesh.material.opacity = THREE.MathUtils.lerp(shieldMesh.material.opacity, 0.2 + Math.sin(t * 3) * 0.1, 0.1);
    }

    scene.traverse((object) => {
        if (object.userData.nebula) {
            object.material.uniforms.time.value = t;
        }

        if (object.userData.stars) {
            object.rotation.y = t * 0.02;
            object.rotation.x = Math.sin(t * 0.1) * 0.05;
        }

        if (object.userData.borderGroup) {
            object.children.forEach((border, i) => {
                if (border.material) {
                    border.material.opacity = (0.4 - i * 0.08) * (0.8 + Math.sin(t * 2 + i * 0.5) * 0.2);
                }
            });
        }

        if (object.userData.floatingParticle) {
            object.position.y = 0.5 + Math.sin(t * object.userData.speed + object.userData.offset) * 0.3;
            object.material.opacity = 0.4 + Math.sin(t * 3 + object.userData.offset) * 0.2;
        }
    });

    renderer.render(scene, camera);
}

init();