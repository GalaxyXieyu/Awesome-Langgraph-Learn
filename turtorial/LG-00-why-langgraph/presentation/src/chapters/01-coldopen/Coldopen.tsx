import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Coldopen.css";

const FRAMEWORKS = [
  "LangChain",
  "LangGraph",
  "CrewAI",
  "AutoGen",
  "Agno",
  "Pydantic AI",
  "Spring AI",
];

export default function Coldopen({ step }: ChapterStepProps) {
  /* Step 0 — terminal boot + typewriter headline */
  if (step === 0) {
    return <Step0Typewriter />;
  }

  /* Step 1 — framework list cascade */
  if (step === 1) {
    return <Step1FrameworkList />;
  }

  /* Step 2 — the question */
  return <Step2Question />;
}

/* ─── Step 0: Typewriter headline ─── */
function Step0Typewriter() {
  const [text, setText] = useState("");
  const fullText = "2024-2025  AI Agent 框架井喷";

  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      i++;
      setText(fullText.slice(0, i));
      if (i >= fullText.length) clearInterval(timer);
    }, 80);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="co-scene center">
      <div className="co-terminal">
        <span className="co-prompt">$ </span>
        <span className="co-typewriter">{text}</span>
        <span className="co-cursor" />
      </div>
    </div>
  );
}

/* ─── Step 1: Framework list cascade ─── */
function Step1FrameworkList() {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setVisible(count);
      if (count >= FRAMEWORKS.length) clearInterval(timer);
    }, 200);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="co-scene center">
      <div className="co-list-box">
        {FRAMEWORKS.map((fw, i) => (
          <div
            key={fw}
            className={`co-list-item ${i < visible ? "co-visible" : ""}`}
          >
            <span className="co-bullet">&gt;</span>
            <span className="co-fw-name">{fw}</span>
          </div>
        ))}
        <div className={`co-list-item co-ellipsis ${visible >= FRAMEWORKS.length ? "co-visible" : ""}`}>
          <span className="co-bullet">.</span>
          <span className="co-fw-name co-dim">...</span>
        </div>
      </div>
    </div>
  );
}

/* ─── Step 2: The question ─── */
function Step2Question() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 200);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="co-scene center">
      <div className={`co-question-wrap ${show ? "co-in" : ""}`}>
        <div className="co-question">选哪个？</div>
        <div className="co-cursor-lg" />
      </div>
      <div className={`co-hint ${show ? "co-in" : ""}`}>
        Demo 很美好，生产很残酷
      </div>
    </div>
  );
}
