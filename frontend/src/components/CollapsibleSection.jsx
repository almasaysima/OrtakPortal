import { useState } from "react";

export default function CollapsibleSection({
  title,
  subtitle,
  children,
  defaultOpen = false,
  badge,
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <section className={`card collapsible-card ${open ? "is-open" : ""}`}>
      <button
        type="button"
        className="collapsible-trigger"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <div className="collapsible-heading">
          <div>
            <h2>{title}</h2>
            {subtitle ? <p>{subtitle}</p> : null}
          </div>
          {badge !== undefined && badge !== null ? (
            <span className="collapsible-count">{badge}</span>
          ) : null}
        </div>

        <span className="collapsible-chevron" aria-hidden="true">
          {open ? "−" : "+"}
        </span>
      </button>

      <div className="collapsible-content" data-open={open}>
        <div className="collapsible-content-inner">{children}</div>
      </div>
    </section>
  );
}
