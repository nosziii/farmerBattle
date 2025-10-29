export type Vec3Tuple = [number, number, number];

export interface BuildingAssetConfig {
  id: string;
  model: string;
  /** Uniform scale applied to the imported GLB */
  scale: number;
  /** Position in 3D space (x, y, z) */
  position: Vec3Tuple;
  /** Rotation in radians (x, y, z) */
  rotation?: Vec3Tuple;
  /** Optional idle animation amplitude for subtle movement */
  idleAmplitude?: number;
}

const BASE_PATH = "/picture/fbx/House_1_unity";

const makeConfig = (
  id: string,
  modelFile: string,
  position: Vec3Tuple,
  scale: number,
  rotation: Vec3Tuple = [0, 0, 0],
  idleAmplitude = 0.0,
): BuildingAssetConfig => ({
  id,
  model: `${BASE_PATH}/${modelFile}`,
  position,
  scale,
  rotation,
  idleAmplitude,
});

const BUILDING_ASSET_LOOKUP: Record<string, BuildingAssetConfig> = {
  town_hall: makeConfig(
    "town_hall",
    "house_14_1.glb",
    [0, 0, 0],
    0.75,
    [0, Math.PI * 0.25, 0],
    0.15,
  ),
  wood_mill: makeConfig(
    "wood_mill",
    "house_5_1.glb",
    [-4.5, 0, 6],
    0.58,
    [0, Math.PI * 0.35, 0],
    0.1,
  ),
  clay_pit: makeConfig(
    "clay_pit",
    "house_8_1.glb",
    [5.2, 0, 7.4],
    0.6,
    [0, -Math.PI * 0.45, 0],
    0.05,
  ),
  iron_mine: makeConfig(
    "iron_mine",
    "house_19_1.glb",
    [8.2, 0, -3.2],
    0.6,
    [0, Math.PI * 0.15, 0],
    0.08,
  ),
  warehouse: makeConfig(
    "warehouse",
    "house_17_1.glb",
    [-5.8, 0, -5.6],
    0.7,
    [0, -Math.PI * 0.2, 0],
  ),
  barracks: makeConfig(
    "barracks",
    "house_10_1.glb",
    [2.8, 0, -6.8],
    0.65,
    [0, Math.PI * 0.35, 0],
    0.12,
  ),
  market: makeConfig(
    "market",
    "house_3_1.glb",
    [-2.4, 0, 8.5],
    0.6,
    [0, Math.PI * 0.15, 0],
    0.05,
  ),
  stable: makeConfig(
    "stable",
    "house_12_1.glb",
    [7.8, 0, 3.6],
    0.62,
    [0, -Math.PI * 0.35, 0],
    0.07,
  ),
};

const FALLBACK_CONFIGS: BuildingAssetConfig[] = [
  makeConfig("fallback-a", "house_2_1.glb", [-8, 0, 2], 0.58, [0, 0.2, 0]),
  makeConfig("fallback-b", "house_6_1.glb", [4, 0, 9.5], 0.6, [0, -0.3, 0]),
  makeConfig("fallback-c", "house_9_1.glb", [10, 0, 0], 0.6, [0, 0.5, 0]),
  makeConfig("fallback-d", "house_11_1.glb", [-9, 0, -4], 0.6, [0, -0.5, 0]),
];

export const getBuildingAsset = (internalName: string, index: number): BuildingAssetConfig => {
  if (BUILDING_ASSET_LOOKUP[internalName]) {
    return BUILDING_ASSET_LOOKUP[internalName];
  }
  const fallbackIndex = index % FALLBACK_CONFIGS.length;
  return {
    ...FALLBACK_CONFIGS[fallbackIndex],
    id: `${FALLBACK_CONFIGS[fallbackIndex].id}-${index}`,
  };
};
