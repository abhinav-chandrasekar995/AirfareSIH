"use client";
import { useMemo } from "react";
import { Globe } from "@/components/ui/cobe-globe";
import { EmptyState } from "@/components/panels/EmptyState";
import type { PressurePoint } from "@/types/api";

// India's geographic centre (near Jabalpur, MP) - keeps the globe resting on the
// tracked basket instead of an arbitrary point on the map.
const INDIA_LAT = 22.9734;
const INDIA_LNG = 78.6569;

// Same semantic colours as PressureMap.tsx's PRESSURE_COLOR (--down-600/--warn-600/
// --up-600), converted to the [0-1] RGB float triples cobe's WebGL shader needs - a
// CSS custom property can't be read from a canvas, so the values are duplicated here
// deliberately rather than parsed at runtime.
const PRESSURE_RGB: Record<string, [number, number, number]> = {
  HIGH: [0.784, 0.137, 0.2], // --down-600 #C82333
  MEDIUM: [0.769, 0.529, 0.059], // --warn-600 #C4870F
  LOW: [0.055, 0.545, 0.31], // --up-600 #0E8B4F
};

const MARKER_RGB: [number, number, number] = [1, 0.231, 0.122]; // --signal-600 #FF3B1F
const BASE_RGB: [number, number, number] = [0.251, 0.333, 0.51]; // --navy-500 #405582
const GLOW_RGB: [number, number, number] = [0.957, 0.969, 0.988]; // --navy-50 #F4F7FC

interface AirfareGlobeProps {
  points: PressurePoint[];
  className?: string;
  /** Bigger swing + slightly faster idle motion for the full "zoomed in" page. */
  expanded?: boolean;
  /** False on the dashboard preview, where the whole card is a link to /pressure-map -
   * a draggable canvas underneath would swallow the click gesture. True (default) on
   * the dedicated page, where dragging to rotate is the point. */
  interactive?: boolean;
}

// Renders the tracked routes' real synthesized pressure_map data as airway arcs on a 3D
// globe resting on India. The dashboard card is a small, zoomed-in, non-draggable
// preview (interactive=false) that links to /pressure-map, where the same globe renders
// large and fully draggable (expanded + interactive) as the sole interactive element on
// that page - no separate flat map, so there's exactly one way to explore the routes.
export function AirfareGlobe({ points, className, expanded = false, interactive = true }: AirfareGlobeProps) {
  const { markers, arcs } = useMemo(() => {
    const markerMap = new Map<string, { id: string; location: [number, number]; label: string }>();
    const arcList = points.map((p) => {
      markerMap.set(p.origin, { id: p.origin, location: [p.origin_lat, p.origin_lon], label: p.origin_city });
      markerMap.set(p.destination, {
        id: p.destination,
        location: [p.destination_lat, p.destination_lon],
        label: p.destination_city,
      });
      return {
        id: p.route_code,
        from: [p.origin_lat, p.origin_lon] as [number, number],
        to: [p.destination_lat, p.destination_lon] as [number, number],
        label: `${p.route_code} · ${p.pressure}`,
        color: PRESSURE_RGB[p.pressure] ?? PRESSURE_RGB.LOW,
      };
    });
    return { markers: Array.from(markerMap.values()), arcs: arcList };
  }, [points]);

  if (points.length === 0) {
    return <EmptyState title="No pressure data yet" message="The index has not been computed for any route." />;
  }

  return (
    <Globe
      className={className}
      markers={markers}
      arcs={arcs}
      focusLat={INDIA_LAT}
      focusLng={INDIA_LNG}
      // Zoomed in enough that the subcontinent alone fills the frame and its domestic
      // route arcs (a few hundred to ~2000km, short relative to the whole globe) are
      // actually legible. The dashboard card is a fixed, tighter crop (India alone, most
      // of the rest of the world cropped past the frame) since it's a small non-draggable
      // preview; the expanded /pressure-map globe starts a bit wider and is scroll/pinch
      // zoomable, so the viewer can zoom in on a specific route themselves.
      scale={expanded ? 1.5 : 2.6}
      zoomable={expanded}
      minScale={0.9}
      maxScale={4.5}
      focusSwing={expanded ? 0.3 : 0.05}
      speed={expanded ? 0.0035 : 0.0018}
      theta={0.32}
      markerColor={MARKER_RGB}
      baseColor={BASE_RGB}
      arcColor={PRESSURE_RGB.LOW}
      glowColor={GLOW_RGB}
      markerSize={expanded ? 0.035 : 0.024}
      arcWidth={expanded ? 0.6 : 0.5}
      mapBrightness={expanded ? 7 : 9}
      dark={0}
      draggable={interactive}
    />
  );
}
