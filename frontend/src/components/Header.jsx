import { PenLine } from "lucide-react";

export default function Header() {
  return (
    <header className="site-header">
      <div className="container header-inner">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <PenLine size={18} />
          </span>
          <span className="brand-name">Sketchify Studio</span>
        </div>
        <span className="header-tag">Image to Sketch</span>
      </div>
    </header>
  );
}
