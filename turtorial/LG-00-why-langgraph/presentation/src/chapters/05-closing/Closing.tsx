import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Closing.css";

const LINES = [
  "链太线，图更全；",
  "要可控，LangGraph 行；",
  "状态明，循环轻；",
  "人机能，生产顶。",
];

export default function Closing({ step: _step }: ChapterStepProps) {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setVisible(count);
      if (count >= LINES.length) clearInterval(timer);
    }, 600);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="cl-scene center">
      <div className="cl-content">
        <div className="cl-lines">
          {LINES.map((line, i) => (
            <div
              key={i}
              className={`cl-line ${i < visible ? "cl-visible" : ""}`}
            >
              {line}
            </div>
          ))}
        </div>
        <div className={`cl-next ${visible >= LINES.length ? "cl-visible" : ""}`}>
          LG-01: State · Node · Edge
        </div>
        <div className={`cl-cursor ${visible >= LINES.length ? "cl-blink" : ""}`} />
      </div>
    </div>
  );
}
