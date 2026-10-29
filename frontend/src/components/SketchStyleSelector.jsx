import { Check } from "lucide-react";
import { SKETCH_STYLES } from "../data/styles";

export default function SketchStyleSelector({ selected, onSelect, disabled }) {
  const move = (index, delta) => {
    const next = (index + delta + SKETCH_STYLES.length) % SKETCH_STYLES.length;
    onSelect(SKETCH_STYLES[next].id);
    document.getElementById(`style-${SKETCH_STYLES[next].id}`)?.focus();
  };

  return (
    <div className="style-grid" role="radiogroup" aria-label="Sketch style">
      {SKETCH_STYLES.map((style, index) => {
        const active = style.id === selected;
        return (
          <button
            key={style.id}
            id={`style-${style.id}`}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={`${style.name}: ${style.description}`}
            tabIndex={active ? 0 : -1}
            disabled={disabled}
            className={`style-card${active ? " active" : ""}`}
            onClick={() => onSelect(style.id)}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight" || e.key === "ArrowDown") {
                e.preventDefault();
                move(index, 1);
              } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
                e.preventDefault();
                move(index, -1);
              }
            }}
          >
            <img src={`/styles/${style.id}.jpg`} alt="" loading="lazy" width="320" height="240" />
            <span className="style-card-body">
              <span className="style-name">{style.name}</span>
              <span className="style-desc">{style.description}</span>
            </span>
            {active && (
              <span className="style-check" aria-hidden="true">
                <Check size={14} />
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
