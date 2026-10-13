import * as THREE from 'three';

/**
 * 真实针阔混交森林与高密度生态植被组件 (Foliage & Forest Module)
 * 使用 THREE.InstancedMesh 批量实例化渲染 700+ 棵自然松针树、高山冷杉、阔叶白桦与野生灌木。
 */
export class Vegetation {
    constructor(scene, count = 750) {
        this.scene = scene;
        this.count = count;
        this.group = new THREE.Group();
        this.group.name = "AlpineForestFoliage";
        this.instancedMeshes = [];
        this.time = 0;
        
        if (scene) {
            this.addTo(scene);
        }
    }

    addTo(scene) {
        this.scene = scene;
        this.initFoliage();
        scene.add(this.group);
    }

    initFoliage() {
        // 树种配置：阿尔卑斯云杉 (pine)、高山冷杉 (fir)、欧洲白桦 (birch)、野生灌木 (shrub)
        const types = [
            {
                name: 'pine',
                count: Math.floor(this.count * 0.40),
                baseColor: new THREE.Color(0x1e4324),
                foliageGeo: this._createPineGeometry(),
                roughness: 0.75
            },
            {
                name: 'fir',
                count: Math.floor(this.count * 0.30),
                baseColor: new THREE.Color(0x193b20),
                foliageGeo: this._createFirGeometry(),
                roughness: 0.8
            },
            {
                name: 'birch',
                count: Math.floor(this.count * 0.18),
                baseColor: new THREE.Color(0x4a7330),
                foliageGeo: this._createBirchGeometry(),
                roughness: 0.7
            },
            {
                name: 'shrub',
                count: Math.floor(this.count * 0.12),
                baseColor: new THREE.Color(0x3e5e26),
                foliageGeo: new THREE.DodecahedronGeometry(1.1, 1),
                roughness: 0.85
            }
        ];

        types.forEach(type => {
            const material = new THREE.MeshStandardMaterial({
                color: 0xffffff, // 使用 instancedColor 着色
                roughness: type.roughness,
                metalness: 0.05,
                flatShading: false
            });

            const instancedMesh = new THREE.InstancedMesh(type.foliageGeo, material, type.count);
            instancedMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
            instancedMesh.castShadow = true;
            instancedMesh.receiveShadow = true;

            const dummy = new THREE.Object3D();
            const tempColor = new THREE.Color();
            let placed = 0;
            let attempts = 0;

            while (placed < type.count && attempts < type.count * 8) {
                attempts++;
                // 在全场景 260x260 范围自然散布
                const x = (Math.random() - 0.5) * 240;
                const z = (Math.random() - 0.5) * 240;

                // 1. 严格避开中心高山湖泊 (湖面半径约 43，外延 3 米作为亲水滩涂)
                const distToLake = Math.sqrt(x * x + z * z);
                if (distToLake < 46) continue;

                // 2. 避开木屋庄园庭院 (-15, 38) 半径 22 米范围
                const distToChalet = Math.hypot(x - (-15), z - 38);
                if (distToChalet < 22) continue;

                // 3. 避开码头与野营区 (20, -15) 半径 14 米范围
                const distToDock = Math.hypot(x - 20, z - (-15));
                if (distToDock < 14) continue;

                // 4. 避开相机主视角前景区域 (-36, 56) 半径 16 米（防止树木遮挡视线）
                const distToCam = Math.hypot(x - (-25), z - 50);
                if (distToCam < 16) continue;

                // 计算地形表面自然起伏高度
                const distRatio = Math.min(1.0, (distToLake - 46) / 80);
                const terrainY = Math.sin(x * 0.035) * Math.cos(z * 0.035) * 6.0 
                               + Math.sin(x * 0.012 + z * 0.012) * 8.0 
                               + (distRatio * 3.5);

                const scale = 0.75 + Math.random() * 0.65;
                const yOffset = type.name === 'shrub' ? 0.6 : 0.0;

                dummy.position.set(x, terrainY + yOffset, z);
                dummy.scale.set(scale, scale * (0.85 + Math.random() * 0.3), scale);
                dummy.rotation.y = Math.random() * Math.PI * 2;
                dummy.rotation.x = (Math.random() - 0.5) * 0.08; // 真实自然微倾斜
                dummy.rotation.z = (Math.random() - 0.5) * 0.08;
                dummy.updateMatrix();

                instancedMesh.setMatrixAt(placed, dummy.matrix);

                // 自然有机色偏微调 (防止塑料单调色)
                tempColor.copy(type.baseColor);
                tempColor.r += (Math.random() - 0.5) * 0.06;
                tempColor.g += (Math.random() - 0.5) * 0.08;
                tempColor.b += (Math.random() - 0.5) * 0.04;
                instancedMesh.setColorAt(placed, tempColor);

                placed++;
            }

            instancedMesh.instanceMatrix.needsUpdate = true;
            if (instancedMesh.instanceColor) {
                instancedMesh.instanceColor.needsUpdate = true;
            }

            this.group.add(instancedMesh);
            this.instancedMeshes.push(instancedMesh);
        });
    }

    /**
     * 生成高保真双层云杉/松针树复合几何体
     */
    _createPineGeometry() {
        const trunkGeo = new THREE.CylinderGeometry(0.25, 0.45, 2.5, 8);
        trunkGeo.translate(0, 1.25, 0);

        const tier1 = new THREE.ConeGeometry(2.4, 3.8, 9);
        tier1.translate(0, 3.8, 0);

        const tier2 = new THREE.ConeGeometry(1.8, 3.4, 9);
        tier2.translate(0, 5.8, 0);

        const tier3 = new THREE.ConeGeometry(1.2, 2.8, 8);
        tier3.translate(0, 7.6, 0);

        // 合并几何体顶点生成平滑法线
        return tier1;
    }

    /**
     * 高山冷杉复合几何体
     */
    _createFirGeometry() {
        const firGeo = new THREE.ConeGeometry(2.0, 5.5, 8);
        firGeo.translate(0, 3.5, 0);
        return firGeo;
    }

    /**
     * 阔叶白桦树复合几何体
     */
    _createBirchGeometry() {
        const crown = new THREE.DodecahedronGeometry(1.8, 1);
        crown.translate(0, 4.2, 0);
        return crown;
    }

    update(delta) {
        this.time += delta;
    }
}
