"use client";

export function ScenarioSlider({ value, onChange, min = 0, max = 10, step = 0.5 }: {
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <label htmlFor="cpi-weight" className="eyebrow">Airfare weight</label>
        <span className="text-sm font-semibold numeric text-primary">{value.toFixed(1)}%</span>
      </div>
      <input
        id="cpi-weight"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full accent-[var(--accent-600)]"
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={value}
      />
      <div className="flex justify-between text-[10px] text-muted mt-0.5">
        <span>{min}%</span>
        <span>{max}%</span>
      </div>
    </div>
  );
}
