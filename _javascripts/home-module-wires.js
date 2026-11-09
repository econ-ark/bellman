const edges = {
  top: [0, 1, 2, 3, 0],
  sides: [[0, 4, 7, 6, 5, 1], [3, 7], [2, 6]],
  tip: [1, 8, 2],
};

function moveAlong(context, points, vertices) {
  const first = points[vertices[0]];
  context.moveTo(first.x, first.y);
  for (let index = 1; index < vertices.length; index++) {
    const point = points[vertices[index]];
    context.lineTo(point.x, point.y);
  }
}

function matrix(transform) {
  return transform === "none" ? new DOMMatrix() : new DOMMatrix(transform);
}

function useSvg(scene) {
  for (const {element} of scene.tiles) element.classList.remove("pm-projected-wires");
}

function project(scene) {
  const {field, plane, tiles, canvas, context} = scene;
  if (canvas.hidden) return;
  const fieldStyle = getComputedStyle(field);
  const planeStyle = getComputedStyle(plane);
  const width = parseFloat(fieldStyle.width);
  const height = parseFloat(fieldStyle.height);
  const ratio = Math.min(devicePixelRatio, Math.sqrt(8_000_000 / (width * height)));
  const canvasWidth = Math.round(width * ratio);
  const canvasHeight = Math.round(height * ratio);
  if (!canvasWidth || !canvasHeight) return;
  if (canvas.width !== canvasWidth) canvas.width = canvasWidth;
  if (canvas.height !== canvasHeight) canvas.height = canvasHeight;

  context.setTransform(canvasWidth / width, 0, 0, canvasHeight / height, 0, 0);
  context.clearRect(0, 0, width, height);
  context.lineCap = "round";
  context.lineJoin = "round";

  const [px, py] = fieldStyle.perspectiveOrigin.split(" ").map(parseFloat);
  const [ox, oy] = planeStyle.transformOrigin.split(" ").map(parseFloat);
  const x = parseFloat(planeStyle.left);
  const y = parseFloat(planeStyle.top);
  const pitch = parseFloat(planeStyle.gridTemplateColumns);
  const columns = Number(plane.style.getPropertyValue("--cols"));
  const depth = parseFloat(getComputedStyle(tiles[0].element.querySelector(".pm-face--left")).width);
  const perspective = new DOMMatrix();
  perspective.m34 = -1 / parseFloat(fieldStyle.perspective);
  // Apply the field perspective around its origin after the plane transform.
  const view = new DOMMatrix().translate(px, py).multiply(perspective)
    .translate(x + ox - px, y + oy - py).multiply(matrix(planeStyle.transform)).translate(-ox, -oy);

  const animate = planeStyle.animationName === "pm-flyback";
  const changed = [];
  for (const [index, {element, tip}] of tiles.entries()) {
    const painted = animate && paintTile(context, view, getComputedStyle(element), tip, index, columns, pitch, depth);
    if (element.classList.contains("pm-projected-wires") !== painted) changed.push([element, painted]);
  }

  for (const [element, painted] of changed) element.classList.toggle("pm-projected-wires", painted);
}

function paintTile(context, view, style, tip, index, columns, pitch, depth) {
  const size = parseFloat(style.width);
  const col = index % columns;
  const row = Math.floor(index / columns);
  const transform = view.translate((col + .5) * pitch, (row + .5) * pitch)
    .multiply(matrix(style.transform)).translate(-size / 2, -size / 2);
  const tipStyle = getComputedStyle(tip);
  const tipOpen = tipStyle.visibility === "visible";
  const tipX = size * (1 + (tipOpen ? .7 * matrix(tipStyle.transform).a : 0));
  const points = [
    [0, 0, 0], [size, 0, 0], [size, size, 0], [0, size, 0],
    [0, 0, -depth], [size, 0, -depth], [size, size, -depth], [0, size, -depth],
    [tipX, size / 2, 0],
  ].map(([x, y, z]) => transform.transformPoint({x, y, z}));
  if (points.some(point => !Number.isFinite(point.w) || point.w <= .01)) return false;
  for (const point of points) {
    point.x /= point.w;
    point.y /= point.w;
  }

  const faceSpan = Math.hypot(points[1].x - points[0].x, points[1].y - points[0].y);
  const projectedScale = faceSpan / size;
  context.lineWidth = Math.max(.7, 1 / context.getTransform().a, Math.min(1.8, projectedScale * 1.2));
  context.globalAlpha = Math.min(1, .28 + projectedScale * 1.25);
  context.strokeStyle = style.getPropertyValue("--pm-side-edge");
  context.beginPath();
  for (const side of edges.sides) moveAlong(context, points, side);
  context.stroke();

  context.strokeStyle = style.getPropertyValue("--pm-top-edge");
  context.beginPath();
  moveAlong(context, points, edges.top);
  context.stroke();

  if (tipOpen) {
    context.strokeStyle = style.getPropertyValue("--pm-tip-edge");
    context.beginPath();
    moveAlong(context, points, edges.tip);
    context.stroke();
  }
  return true;
}

export function drawModuleWires(home) {
  if (!("IntersectionObserver" in window) || !("DOMMatrix" in window) || !("ResizeObserver" in window)) return;
  const scenes = new Map();
  const visible = new Set();
  let frame;

  function scheduleDraw() {
    if (frame !== undefined || !visible.size) return;
    frame = requestAnimationFrame(() => {
      frame = undefined;
      for (const field of visible) project(scenes.get(field));
    });
  }

  const observer = new IntersectionObserver(entries => {
    for (const {target, isIntersecting} of entries) {
      if (isIntersecting) {
        visible.add(target);
      } else {
        visible.delete(target);
        const scene = scenes.get(target);
        scene.canvas.width = 0;
        useSvg(scene);
      }
    }
    scheduleDraw();
  });

  document.addEventListener("scroll", scheduleDraw, {passive: true});
  window.addEventListener("resize", scheduleDraw);
  matchMedia("(prefers-reduced-motion: reduce)").addEventListener("change", scheduleDraw);
  document.fonts.ready.then(scheduleDraw);
  const resizeObserver = new ResizeObserver(scheduleDraw);

  for (const field of home.querySelectorAll(".pm-field")) {
    const plane = field.querySelector(".pm-plane");
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");
    if (!context) break;
    canvas.className = "pm-wires";
    canvas.width = 0;
    field.append(canvas);
    const tiles = Array.from(plane.children, element => ({element, tip: element.querySelector(".pm-tip")}));
    const scene = {field, plane, tiles, canvas, context};
    canvas.addEventListener("contextlost", () => {
      canvas.hidden = true;
      useSvg(scene);
    });
    canvas.addEventListener("contextrestored", () => {
      canvas.hidden = false;
      scheduleDraw();
    });
    scenes.set(field, scene);
    observer.observe(field);
    resizeObserver.observe(field);
  }
}
