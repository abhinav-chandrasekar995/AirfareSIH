"use client";
import { useEffect, useRef } from "react";

// Lightweight scroll-reveal, shared by the marketing site and the app.
//
// FAIL-SAFE BY DESIGN: elements are visible by default (no CSS `opacity: 0` default
// anywhere). This hook only pre-hides an element - via an inline style it sets and
// later clears itself - for elements it actually catches *before* they enter the
// viewport. Anything the observer never reaches (most commonly: panels that don't
// exist in the DOM yet because they're behind an async data fetch, e.g. every app page
// built on TanStack Query) is simply never touched and stays at its natural, visible
// state. The previous version hid elements via a CSS class by default and relied on
// this hook to un-hide them; a one-time `querySelectorAll` at mount could not see
// elements added to the DOM later (after a query resolved), so those panels were
// permanently invisible - the exact "blank page" regression this rewrite fixes.
export function useRevealOnScroll<T extends HTMLElement = HTMLDivElement>(
  selector = ".b-reveal",
) {
  const ref = useRef<T>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const items = node.querySelectorAll<HTMLElement>(selector);
    if (items.length === 0 || reduceMotion) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const el = entry.target as HTMLElement;
          if (entry.isIntersecting) {
            const delay = Number(el.dataset.revealDelay ?? 0);
            setTimeout(() => {
              el.style.transition = "opacity 280ms cubic-bezier(0.16,1,0.3,1), transform 280ms cubic-bezier(0.16,1,0.3,1)";
              el.style.opacity = "";
              el.style.transform = "";
            }, delay);
            observer.unobserve(el);
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -30px 0px" },
    );

    items.forEach((el, i) => {
      const rect = el.getBoundingClientRect();
      const alreadyOnScreen = rect.top < window.innerHeight && rect.bottom > 0;
      // Only pre-hide elements that are NOT already visible in the viewport - anything
      // above the fold at mount time is left alone entirely, so it can never get stuck
      // hidden regardless of what the observer does afterwards.
      if (!alreadyOnScreen) {
        el.style.opacity = "0";
        el.style.transform = "translateY(10px)";
        if (!el.dataset.revealDelay) el.dataset.revealDelay = String(i * 40);
      }
      observer.observe(el);
    });

    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selector]);

  return ref;
}
