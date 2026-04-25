import { useEffect, useRef } from "react";

import type { CarState, ParkingScene, RectObstacle, ReplayResult } from "../../lib/schemas";

interface SceneCanvasProps {
  scene: ParkingScene;
  replay: ReplayResult;
  stepIndex: number;
  showLidar: boolean;
}

interface Viewport {
  width: number;
  height: number;
  scale: number;
  offsetX: number;
  offsetY: number;
}

type Point = [number, number];

function toCanvas(scene: ParkingScene, viewport: Viewport, point: Point): Point {
  const bounds = scene.bounds;
  const x = viewport.offsetX + (point[0] - bounds.min_x) * viewport.scale;
  const y = viewport.offsetY + (bounds.max_y - point[1]) * viewport.scale;
  return [x, y];
}

function corners(
  x: number,
  y: number,
  length: number,
  width: number,
  theta: number
): Point[] {
  const halfLength = length / 2;
  const halfWidth = width / 2;
  const local: Point[] = [
    [halfLength, halfWidth],
    [halfLength, -halfWidth],
    [-halfLength, -halfWidth],
    [-halfLength, halfWidth]
  ];
  return local.map(([localX, localY]) => [
    x + localX * Math.cos(theta) - localY * Math.sin(theta),
    y + localX * Math.sin(theta) + localY * Math.cos(theta)
  ]);
}

function fillPolygon(
  ctx: CanvasRenderingContext2D,
  scene: ParkingScene,
  viewport: Viewport,
  points: Point[],
  fill: string,
  stroke: string
) {
  ctx.beginPath();
  points.forEach((point, index) => {
    const [x, y] = toCanvas(scene, viewport, point);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = fill;
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 1.5;
  ctx.fill();
  ctx.stroke();
}

function drawObstacle(
  ctx: CanvasRenderingContext2D,
  scene: ParkingScene,
  viewport: Viewport,
  obstacle: RectObstacle
) {
  fillPolygon(
    ctx,
    scene,
    viewport,
    corners(obstacle.x, obstacle.y, obstacle.width, obstacle.height, obstacle.theta),
    obstacle.id.includes("wall") || obstacle.id === "curb" ? "#535a51" : "#b86b58",
    "#2f332f"
  );
}

function drawCar(
  ctx: CanvasRenderingContext2D,
  scene: ParkingScene,
  viewport: Viewport,
  state: CarState,
  fill: string,
  stroke: string
) {
  fillPolygon(
    ctx,
    scene,
    viewport,
    corners(state.x, state.y, scene.car_spec.length, scene.car_spec.width, state.theta),
    fill,
    stroke
  );

  const nose = toCanvas(scene, viewport, [
    state.x + (scene.car_spec.length / 2) * Math.cos(state.theta),
    state.y + (scene.car_spec.length / 2) * Math.sin(state.theta)
  ]);
  const center = toCanvas(scene, viewport, [state.x, state.y]);
  ctx.beginPath();
  ctx.moveTo(center[0], center[1]);
  ctx.lineTo(nose[0], nose[1]);
  ctx.strokeStyle = stroke;
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawGoal(ctx: CanvasRenderingContext2D, scene: ParkingScene, viewport: Viewport) {
  ctx.save();
  ctx.setLineDash([7, 5]);
  fillPolygon(
    ctx,
    scene,
    viewport,
    corners(
      scene.goal.x,
      scene.goal.y,
      scene.car_spec.length,
      scene.car_spec.width,
      scene.goal.theta
    ),
    "rgba(93, 150, 108, 0.16)",
    "#3b7b4c"
  );
  ctx.restore();
}

function drawTrajectory(
  ctx: CanvasRenderingContext2D,
  scene: ParkingScene,
  viewport: Viewport,
  replay: ReplayResult,
  stepIndex: number
) {
  const points = [scene.start, ...replay.steps.slice(0, stepIndex + 1).map((step) => step.state)];
  if (points.length < 2) return;

  ctx.beginPath();
  points.forEach((point, index) => {
    const [x, y] = toCanvas(scene, viewport, [point.x, point.y]);
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = "#287b8f";
  ctx.lineWidth = 3;
  ctx.stroke();
}

function drawLidar(
  ctx: CanvasRenderingContext2D,
  scene: ParkingScene,
  viewport: Viewport,
  state: CarState
) {
  const rays = scene.lidar.rays;
  const start = -scene.lidar.fov / 2;
  const step = rays > 1 ? scene.lidar.fov / (rays - 1) : 0;
  const origin = toCanvas(scene, viewport, [state.x, state.y]);

  ctx.strokeStyle = "rgba(40, 123, 143, 0.16)";
  ctx.lineWidth = 1;
  for (let index = 0; index < rays; index += 1) {
    const angle = state.theta + start + index * step;
    const end = toCanvas(scene, viewport, [
      state.x + scene.lidar.max_distance * Math.cos(angle),
      state.y + scene.lidar.max_distance * Math.sin(angle)
    ]);
    ctx.beginPath();
    ctx.moveTo(origin[0], origin[1]);
    ctx.lineTo(end[0], end[1]);
    ctx.stroke();
  }
}

function drawGrid(ctx: CanvasRenderingContext2D, scene: ParkingScene, viewport: Viewport) {
  ctx.strokeStyle = "rgba(68, 79, 73, 0.14)";
  ctx.lineWidth = 1;
  for (let x = Math.ceil(scene.bounds.min_x); x <= scene.bounds.max_x; x += 1) {
    const top = toCanvas(scene, viewport, [x, scene.bounds.max_y]);
    const bottom = toCanvas(scene, viewport, [x, scene.bounds.min_y]);
    ctx.beginPath();
    ctx.moveTo(top[0], top[1]);
    ctx.lineTo(bottom[0], bottom[1]);
    ctx.stroke();
  }
  for (let y = Math.ceil(scene.bounds.min_y); y <= scene.bounds.max_y; y += 1) {
    const left = toCanvas(scene, viewport, [scene.bounds.min_x, y]);
    const right = toCanvas(scene, viewport, [scene.bounds.max_x, y]);
    ctx.beginPath();
    ctx.moveTo(left[0], left[1]);
    ctx.lineTo(right[0], right[1]);
    ctx.stroke();
  }
}

export function SceneCanvas({ scene, replay, stepIndex, showLidar }: SceneCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const canvasElement = canvas;

    function render() {
      const parent = canvasElement.parentElement;
      if (!parent) return;
      const rect = parent.getBoundingClientRect();
      if (rect.width <= 0 || rect.height <= 0) return;

      const dpr = window.devicePixelRatio || 1;
      canvasElement.width = Math.floor(rect.width * dpr);
      canvasElement.height = Math.floor(rect.height * dpr);

      const ctx = canvasElement.getContext("2d");
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, rect.width, rect.height);

      const margin = 32;
      const worldWidth = scene.bounds.max_x - scene.bounds.min_x;
      const worldHeight = scene.bounds.max_y - scene.bounds.min_y;
      const scale = Math.min((rect.width - margin * 2) / worldWidth, (rect.height - margin * 2) / worldHeight);
      const viewport = {
        width: rect.width,
        height: rect.height,
        scale,
        offsetX: (rect.width - worldWidth * scale) / 2,
        offsetY: (rect.height - worldHeight * scale) / 2
      };

      ctx.fillStyle = "#eef1ec";
      ctx.fillRect(0, 0, rect.width, rect.height);
      drawGrid(ctx, scene, viewport);
      drawGoal(ctx, scene, viewport);
      scene.obstacles.forEach((obstacle) => drawObstacle(ctx, scene, viewport, obstacle));
      drawTrajectory(ctx, scene, viewport, replay, stepIndex);

      const currentState = replay.steps[stepIndex]?.state ?? scene.start;
      if (showLidar) drawLidar(ctx, scene, viewport, currentState);
      drawCar(ctx, scene, viewport, scene.start, "rgba(54, 73, 88, 0.18)", "#667582");
      drawCar(ctx, scene, viewport, currentState, "#e8b84c", "#3a3527");
    }

    render();
    const observer = new ResizeObserver(render);
    observer.observe(canvasElement.parentElement ?? canvasElement);
    return () => observer.disconnect();
  }, [scene, replay, stepIndex, showLidar]);

  return <canvas ref={canvasRef} className="scene-canvas" aria-label="Parking scene canvas" />;
}
