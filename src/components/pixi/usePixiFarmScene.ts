import { Application } from "pixi.js";
import type { Renderer } from "@pixi/core";
import {
  Camera,
  CameraOrbitControl,
  Container3D,
  Light,
  LightType,
  LightingEnvironment,
  Mesh3D,
  Model,
  StandardMaterial,
  Color,
  glTFAsset,
} from "pixi3d/pixi7";
import { gsap } from "gsap";
import { getBuildingAsset, BuildingAssetConfig } from "./buildingCatalog";

export interface StructureSnapshot {
  internalName: string;
  name: string;
  level: number;
  isUpgrading: boolean;
  canUpgrade: boolean;
  progress: number;
}

export interface FarmSceneInitOptions {
  container: HTMLElement;
  onStructureSelect?: (internalName: string) => void;
}

interface VisualBuilding {
  config: BuildingAssetConfig;
  model: Container3D;
  baseY: number;
  floatTween?: gsap.core.Tween;
  highlightTween?: gsap.core.Tween;
  selectHandler?: () => void;
}

const RAD_TO_DEG = 180 / Math.PI;

const toDegrees = (value: number) => value * RAD_TO_DEG;

const baseModelCache = new Map<string, Promise<Model>>();

async function createModelInstance(config: BuildingAssetConfig): Promise<Container3D> {
  if (!baseModelCache.has(config.model)) {
    const entry = glTFAsset
      .fromURL(config.model)
      .then((asset) => {
        const baseModel = Model.from(asset);
        baseModel.visible = false;
        return baseModel;
      })
      .catch((error) => {
        console.error(`[farm-scene] Failed to load model ${config.model}`, error);
        throw error;
      });
    baseModelCache.set(config.model, entry);
  }

  const baseModel = await baseModelCache.get(config.model)!;
  const instance = baseModel.createInstance();
  instance.visible = true;
  instance.scale.set(config.scale);
  instance.position.set(...config.position);

  const rotation = config.rotation ?? [0, 0, 0];
  instance.rotationQuaternion.setEulerAngles(
    toDegrees(rotation[0]),
    toDegrees(rotation[1]),
    toDegrees(rotation[2]),
  );

  return instance;
}

const setupGroundPlane = () => {
  const ground = Mesh3D.createPlane();
  ground.position.set(0, -0.35, 0);
  ground.scale.set(20, 1, 20);

  const material = ground.material as StandardMaterial;
  material.baseColor = Color.fromHex(0x1f5439);
  material.metallic = 0.1;
  material.roughness = 0.9;

  return ground;
};

const setupLighting = (root: Container3D) => {
  const mainLight = new Light();
  mainLight.type = LightType.directional;
  mainLight.position.set(6, 12, 8);
  mainLight.intensity = 1.4;
  mainLight.rotationQuaternion.setEulerAngles(-45, 30, 0);

  const bounceLight = new Light();
  bounceLight.type = LightType.directional;
  bounceLight.position.set(-3, 6, -6);
  bounceLight.intensity = 0.45;
  bounceLight.color = Color.fromBytes(140, 188, 255);

  LightingEnvironment.main.lights = [mainLight, bounceLight];
  root.addChild(mainLight);
  root.addChild(bounceLight);
};

const setupCamera = (renderer: Application["renderer"], canvas: HTMLCanvasElement) => {
  const camera = new Camera(renderer as unknown as Renderer);
  camera.position.set(0, 9, 18);
  camera.rotationQuaternion.setEulerAngles(-18, -32, 0);
  camera.near = 0.4;
  camera.far = 80;

  Camera.main = camera;

  const controls = new CameraOrbitControl(canvas, camera);
  controls.distance = 18;
  controls.angles.set(24, -32);
  controls.target = { x: 0, y: 0, z: 0 };
  controls.updateCamera();

  return { camera, controls };
};

export interface FarmSceneHandle {
  syncStructures(structures: StructureSnapshot[]): Promise<void>;
  resize(): void;
  destroy(): void;
}

export const createFarmScene = async (
  options: FarmSceneInitOptions,
): Promise<FarmSceneHandle> => {
  const app = new Application({
    resizeTo: options.container,
    backgroundAlpha: 0,
    antialias: true,
  });

  const canvasElement = app.view as unknown as HTMLCanvasElement;
  options.container.appendChild(canvasElement);

  const sceneRoot = new Container3D();
  app.stage.addChild(sceneRoot);

  const ground = setupGroundPlane();
  sceneRoot.addChild(ground);

  setupLighting(sceneRoot);
  const { controls, camera } = setupCamera(app.renderer, canvasElement);
  sceneRoot.addChild(camera);
  const updateCamera = () => controls.updateCamera();
  app.ticker.add(updateCamera);

  const buildings = new Map<string, VisualBuilding>();

  const ensureFloatTween = (entry: VisualBuilding, amplitude = 0.08) => {
    if (entry.floatTween) return;
    entry.floatTween = gsap.to(entry.model.position, {
      y: entry.baseY + amplitude,
      duration: 4 + Math.random() * 2,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });
  };

  const clearFloatTween = (entry: VisualBuilding) => {
    entry.floatTween?.kill();
    entry.floatTween = undefined;
    entry.model.position.y = entry.baseY;
  };

  const setHighlight = (entry: VisualBuilding, isUpgrading: boolean) => {
    entry.highlightTween?.kill();
    if (!isUpgrading) {
      entry.model.scale.set(entry.config.scale);
      return;
    }
    entry.highlightTween = gsap.to(entry.model.scale, {
      x: entry.config.scale * 1.04,
      y: entry.config.scale * 1.04,
      z: entry.config.scale * 1.04,
      duration: 1.6,
      repeat: -1,
      yoyo: true,
      ease: "sine.inOut",
    });
  };

  const syncStructures = async (structures: StructureSnapshot[]) => {
    const seen = new Set<string>();

    let index = 0;
    for (const structure of structures) {
      const asset = getBuildingAsset(structure.internalName, index);
      let entry = buildings.get(structure.internalName);
      if (!entry) {
        const model = await createModelInstance(asset);
        sceneRoot.addChild(model);
        entry = {
          config: asset,
          model,
          baseY: model.position.y,
        };
        buildings.set(structure.internalName, entry);
      }

      const interactiveModel = entry.model as any;
      if (entry.selectHandler) {
        interactiveModel.off("pointertap", entry.selectHandler);
      }
      entry.selectHandler = () => {
        options.onStructureSelect?.(structure.internalName);
      };
      interactiveModel.eventMode = "static";
      interactiveModel.cursor = "pointer";
      interactiveModel.buttonMode = true;
      interactiveModel.on("pointertap", entry.selectHandler);

      entry.config = asset;
      entry.model.position.set(...asset.position);
      entry.baseY = asset.position[1];
      entry.model.scale.set(asset.scale);

      const rotation = asset.rotation ?? [0, 0, 0];
      entry.model.rotationQuaternion.setEulerAngles(
        toDegrees(rotation[0]),
        toDegrees(rotation[1]),
        toDegrees(rotation[2]),
      );

      if (asset.idleAmplitude && asset.idleAmplitude > 0) {
        ensureFloatTween(entry, asset.idleAmplitude * 0.25);
      } else {
        clearFloatTween(entry);
      }

      setHighlight(entry, structure.isUpgrading);

      seen.add(structure.internalName);
      index += 1;
    }

    buildings.forEach((entry, key) => {
      if (!seen.has(key)) {
        entry.floatTween?.kill();
        entry.highlightTween?.kill();
        if (entry.selectHandler) {
          (entry.model as any).off("pointertap", entry.selectHandler);
        }
        entry.model.destroy({ children: true });
        buildings.delete(key);
      }
    });
  };

  const resize = () => {
    app.resize();
    controls.updateCamera();
  };

  const destroy = () => {
    buildings.forEach((entry) => {
      entry.floatTween?.kill();
      entry.highlightTween?.kill();
      if (entry.selectHandler) {
        (entry.model as any).off("pointertap", entry.selectHandler);
      }
    });
    buildings.clear();
    controls.destroy?.();
    app.ticker.remove(updateCamera);
    app.destroy(true, { children: true, texture: false, baseTexture: false });
  };

  return {
    syncStructures,
    resize,
    destroy,
  };
};
