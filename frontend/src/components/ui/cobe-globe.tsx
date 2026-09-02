"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import createGlobe from "cobe";

interface Marker {
  id: string;
  location: [number, number];
  label: string;
  color?: [number, number, number];
}

interface Arc {
  id: string;
  from: [number, number];
  to: [number, number];
  label?: string;
  color?: [number, number, number];
}

interface GlobeProps {
  markers?: Marker[];
  arcs?: Arc[];
  className?: string;
  markerColor?: [number, number, number];
  baseColor?: [number, number, number];
  arcColor?: [number, number, number];
  glowColor?: [number, number, number];
  dark?: number;
  mapBrightness?: number;
  markerSize?: number;
  markerElevation?: number;
  arcWidth?: number;
  arcHeight?: number;
  speed?: number;
  theta?: number;
  diffuse?: number;
  mapSamples?: number;
  /** Latitude (degrees) the globe should rest on. Combined with focusLng to keep a
   * region in view instead of the raw continuous spin cobe does by default. */
  focusLat?: number;
  /** Longitude (degrees) the globe should rest on. */
  focusLng?: number;
  /** How far (radians) the idle animation is allowed to sway away from the focus
   * point before easing back - keeps the globe "facing" a region without freezing it. */
  focusSwing?: number;
  /** Set false to render a purely ambient, non-draggable globe - for placing inside a
   * clickable container (e.g. a card that links elsewhere) without the pointer-drag
   * handler swallowing the click or fighting the container's own gesture. */
  draggable?: boolean;
  /** Camera zoom, passed straight through to cobe's `scale`. >1 zooms in on the focus
   * point - useful when the focus region (e.g. India) is small relative to the whole
   * sphere and would otherwise render too small to make out its arcs. Doubles as the
   * starting zoom when `zoomable` is on. */
  scale?: number;
  /** Enables mouse-wheel/trackpad zoom, clamped to [minScale, maxScale]. Off by default
   * so a non-draggable dashboard preview doesn't also capture page-scroll events. */
  zoomable?: boolean;
  minScale?: number;
  maxScale?: number;
}

// Converts a geographic point into the [phi, theta] cobe needs to bring it to the front
// of the sphere. Derived from cobe's own lat/lon -> sphere projection (equirectangular
// texture, camera looking down +z): phi is the longitude rotation, theta the latitude
// tilt. This is the standard formula used across cobe-based "focus on a location" globes.
function locationToAngles(lat: number, lng: number): [number, number] {
  return [Math.PI - ((lng * Math.PI) / 180 - Math.PI / 2), (lat * Math.PI) / 180];
}

export function Globe({
  markers = [],
  arcs = [],
  className = "",
  markerColor = [0.3, 0.45, 0.85],
  baseColor = [1, 1, 1],
  arcColor = [0.3, 0.45, 0.85],
  glowColor = [0.94, 0.93, 0.91],
  dark = 0,
  mapBrightness = 10,
  markerSize = 0.025,
  markerElevation = 0.01,
  arcWidth = 0.5,
  arcHeight = 0.25,
  speed = 0.003,
  theta = 0.2,
  diffuse = 1.5,
  mapSamples = 16000,
  focusLat,
  focusLng,
  focusSwing = 0.5,
  draggable = true,
  scale = 1,
  zoomable = false,
  minScale = 0.6,
  maxScale = 4,
}: GlobeProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pointerInteracting = useRef<{ x: number; y: number } | null>(null);
  const lastPointer = useRef<{ x: number; y: number; t: number } | null>(null);
  const dragOffset = useRef({ phi: 0, theta: 0 });
  const velocity = useRef({ phi: 0, theta: 0 });
  const phiOffsetRef = useRef(0);
  const thetaOffsetRef = useRef(0);
  const isPausedRef = useRef(false);
  const scaleRef = useRef(scale);
  // Which marker/arc label is currently shown - hover-only, otherwise a fully-populated
  // globe shows every front-facing label at once and turns into unreadable clutter.
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    pointerInteracting.current = { x: e.clientX, y: e.clientY };
    if (canvasRef.current) canvasRef.current.style.cursor = "grabbing";
    isPausedRef.current = true;
  }, []);

  const handlePointerMove = useCallback((e: PointerEvent) => {
    if (pointerInteracting.current !== null) {
      const deltaX = e.clientX - pointerInteracting.current.x;
      const deltaY = e.clientY - pointerInteracting.current.y;
      dragOffset.current = { phi: deltaX / 300, theta: deltaY / 1000 };
      const now = Date.now();
      if (lastPointer.current) {
        const dt = Math.max(now - lastPointer.current.t, 1);
        const maxVelocity = 0.15;
        velocity.current = {
          phi: Math.max(-maxVelocity, Math.min(maxVelocity, ((e.clientX - lastPointer.current.x) / dt) * 0.3)),
          theta: Math.max(-maxVelocity, Math.min(maxVelocity, ((e.clientY - lastPointer.current.y) / dt) * 0.08)),
        };
      }
      lastPointer.current = { x: e.clientX, y: e.clientY, t: now };
    }
  }, []);

  const handlePointerUp = useCallback(() => {
    if (pointerInteracting.current !== null) {
      phiOffsetRef.current += dragOffset.current.phi;
      thetaOffsetRef.current += dragOffset.current.theta;
      dragOffset.current = { phi: 0, theta: 0 };
      lastPointer.current = null;
    }
    pointerInteracting.current = null;
    if (canvasRef.current) canvasRef.current.style.cursor = "grab";
    isPausedRef.current = false;
  }, []);

  useEffect(() => {
    window.addEventListener("pointermove", handlePointerMove, { passive: true });
    window.addEventListener("pointerup", handlePointerUp, { passive: true });
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };
  }, [handlePointerMove, handlePointerUp]);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    let globe: ReturnType<typeof createGlobe> | null = null;
    let animationId: number;

    const [focusPhi, focusTheta] =
      focusLat !== undefined && focusLng !== undefined ? locationToAngles(focusLat, focusLng) : [0, theta];
    const baseTheta = focusLat !== undefined && focusLng !== undefined ? focusTheta : theta;

    scaleRef.current = scale;
    let frame = 0;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      // deltaY < 0 is scroll-up/pinch-out - zoom in, matching every map control's convention.
      const next = scaleRef.current - e.deltaY * 0.0015;
      scaleRef.current = Math.min(maxScale, Math.max(minScale, next));
    };
    if (zoomable) canvas.addEventListener("wheel", onWheel, { passive: false });

    function init() {
      const width = canvas.offsetWidth;
      if (width === 0 || globe) return;

      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      globe = createGlobe(canvas, {
        devicePixelRatio: dpr,
        width,
        height: width,
        phi: focusPhi,
        theta: baseTheta,
        dark,
        diffuse,
        mapSamples,
        mapBrightness,
        baseColor,
        markerColor,
        glowColor,
        markerElevation,
        markers: markers.map((m) => ({
          location: m.location,
          size: markerSize,
          id: m.id,
          color: m.color,
        })),
        arcs: arcs.map((a) => ({
          from: a.from,
          to: a.to,
          id: a.id,
          color: a.color,
        })),
        arcColor,
        arcWidth,
        arcHeight,
        opacity: 0.7,
        scale: scaleRef.current,
      });

      function animate() {
        frame += 1;
        if (!isPausedRef.current) {
          // Idle motion sways around the focus point instead of doing full laps, so a
          // region the caller asked to focus on (focusLat/focusLng) stays "primarily"
          // in view even while the globe keeps a sense of ambient motion.
          const sway = Math.sin(frame * speed) * focusSwing;

          if (
            Math.abs(velocity.current.phi) > 0.0001 ||
            Math.abs(velocity.current.theta) > 0.0001
          ) {
            phiOffsetRef.current += velocity.current.phi;
            thetaOffsetRef.current += velocity.current.theta;
            velocity.current.phi *= 0.95;
            velocity.current.theta *= 0.95;
          } else {
            // No active drag momentum: ease phi back toward the ambient sway target so a
            // manual drag always relaxes back to "facing" the focus point.
            phiOffsetRef.current += (sway - phiOffsetRef.current) * 0.02;
          }

          const thetaMin = -0.4,
            thetaMax = 0.4;
          if (thetaOffsetRef.current < thetaMin) {
            thetaOffsetRef.current += (thetaMin - thetaOffsetRef.current) * 0.1;
          } else if (thetaOffsetRef.current > thetaMax) {
            thetaOffsetRef.current += (thetaMax - thetaOffsetRef.current) * 0.1;
          }
        }
        globe!.update({
          phi: focusPhi + phiOffsetRef.current + dragOffset.current.phi,
          theta: baseTheta + thetaOffsetRef.current + dragOffset.current.theta,
          scale: scaleRef.current,
          dark,
          mapBrightness,
          markerColor,
          baseColor,
          arcColor,
          markerElevation,
          markers: markers.map((m) => ({
            location: m.location,
            size: markerSize,
            id: m.id,
            color: m.color,
          })),
          arcs: arcs.map((a) => ({
            from: a.from,
            to: a.to,
            id: a.id,
            color: a.color,
          })),
        });
        animationId = requestAnimationFrame(animate);
      }
      animate();
      setTimeout(() => canvas && (canvas.style.opacity = "1"));
    }

    if (canvas.offsetWidth > 0) {
      init();
    } else {
      const ro = new ResizeObserver((entries) => {
        if (entries[0]?.contentRect.width > 0) {
          ro.disconnect();
          init();
        }
      });
      ro.observe(canvas);
    }

    return () => {
      if (animationId) cancelAnimationFrame(animationId);
      if (zoomable) canvas.removeEventListener("wheel", onWheel);
      if (globe) globe.destroy();
    };
  }, [
    markers,
    arcs,
    markerColor,
    baseColor,
    arcColor,
    glowColor,
    dark,
    mapBrightness,
    markerSize,
    markerElevation,
    arcWidth,
    arcHeight,
    speed,
    theta,
    diffuse,
    mapSamples,
    focusLat,
    focusLng,
    focusSwing,
    scale,
    zoomable,
    minScale,
    maxScale,
  ]);

  return (
    <div className={`relative aspect-square select-none ${className}`}>
      <canvas
        ref={canvasRef}
        onPointerDown={draggable ? handlePointerDown : undefined}
        style={{
          width: "100%",
          height: "100%",
          cursor: draggable ? "grab" : "inherit",
          opacity: 0,
          transition: "opacity 1.2s ease",
          borderRadius: "50%",
          touchAction: "none",
        }}
      />
      {markers.map((m) => (
        <div key={m.id}>
          {/* Small hoverable hit-target sitting exactly on the marker dot. Cobe has no
              hover/hit-testing API of its own, so this DOM overlay (positioned via the
              same CSS Anchor Positioning cobe drives) is what actually detects hover;
              it also re-runs handlePointerDown so dragging still works if a drag
              happens to start inside this small area. */}
          <div
            onMouseEnter={() => setHoveredId(m.id)}
            onMouseLeave={() => setHoveredId((cur) => (cur === m.id ? null : cur))}
            onPointerDown={draggable ? handlePointerDown : undefined}
            style={{
              position: "absolute",
              positionAnchor: `--cobe-${m.id}`,
              top: "anchor(center)",
              left: "anchor(center)",
              translate: "-50% -50%",
              width: 16,
              height: 16,
              borderRadius: "50%",
              cursor: draggable ? "grab" : "pointer",
              // Only cobe (inside the WebGL frame loop) knows this value at any instant,
              // not React - opacity is a live CSS var reference the browser resolves
              // itself, so it fades correctly with occlusion; pointerEvents can't be
              // conditioned the same way, but the label above stays gated on the same
              // var either way, so an occluded marker never shows a label even if this
              // now-invisible hit target still technically catches the hover.
              opacity: `var(--cobe-visible-${m.id}, 0)`,
              pointerEvents: "auto",
            }}
          />
          <div
            style={{
              position: "absolute",
              positionAnchor: `--cobe-${m.id}`,
              bottom: "anchor(top)",
              left: "anchor(center)",
              translate: "-50% 0",
              marginBottom: 8,
              padding: "2px 6px",
              background: "#1a1a2e",
              color: "#fff",
              fontFamily: "monospace",
              fontSize: "0.6rem",
              letterSpacing: "0.08em",
              textTransform: "uppercase" as const,
              whiteSpace: "nowrap" as const,
              pointerEvents: "none" as const,
              opacity: hoveredId === m.id ? `var(--cobe-visible-${m.id}, 0)` : 0,
              filter: `blur(calc((1 - var(--cobe-visible-${m.id}, 0)) * 8px))`,
              transition: "opacity 0.15s, filter 0.8s",
            }}
          >
            {m.label}
            <span
              style={{
                position: "absolute",
                top: "100%",
                left: "50%",
                transform: "translate3d(-50%, -1px, 0)",
                border: "5px solid transparent",
                borderTopColor: "#1a1a2e",
              }}
            />
          </div>
        </div>
      ))}
      {arcs
        .filter((a) => a.label)
        .map((a) => (
          <div key={a.id}>
            {/* Hit-target at the arc's label anchor (its midpoint) - an arc is a curve,
                not a point, so this only covers hovering near its middle rather than its
                full length, which is the best granularity cobe's anchor API exposes. */}
            <div
              onMouseEnter={() => setHoveredId(a.id)}
              onMouseLeave={() => setHoveredId((cur) => (cur === a.id ? null : cur))}
              onPointerDown={draggable ? handlePointerDown : undefined}
              style={{
                position: "absolute",
                positionAnchor: `--cobe-arc-${a.id}`,
                top: "anchor(center)",
                left: "anchor(center)",
                translate: "-50% -50%",
                width: 28,
                height: 18,
                borderRadius: 9,
                cursor: draggable ? "grab" : "pointer",
                opacity: `var(--cobe-visible-arc-${a.id}, 0)`,
                pointerEvents: "auto",
              }}
            />
            <div
              style={{
                position: "absolute",
                positionAnchor: `--cobe-arc-${a.id}`,
                bottom: "anchor(top)",
                left: "anchor(center)",
                translate: "-50% 0",
                marginBottom: 8,
                padding: "2px 6px",
                background: "#fff",
                color: "#1a1a2e",
                fontFamily: "monospace",
                fontSize: "0.6rem",
                letterSpacing: "0.08em",
                textTransform: "uppercase" as const,
                whiteSpace: "nowrap" as const,
                pointerEvents: "none" as const,
                boxShadow: "0 1px 4px rgba(0,0,0,0.1)",
                opacity: hoveredId === a.id ? `var(--cobe-visible-arc-${a.id}, 0)` : 0,
                filter: `blur(calc((1 - var(--cobe-visible-arc-${a.id}, 0)) * 8px))`,
                transition: "opacity 0.15s, filter 0.8s",
              }}
            >
              {a.label}
              <span
                style={{
                  position: "absolute",
                  top: "100%",
                  left: "50%",
                  transform: "translate3d(-50%, -1px, 0)",
                  border: "5px solid transparent",
                  borderTopColor: "#fff",
                }}
              />
            </div>
          </div>
        ))}
    </div>
  );
}
