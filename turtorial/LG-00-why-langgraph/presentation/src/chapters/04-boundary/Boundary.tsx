import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Boundary.css";

const SCENES = [
  { scene: "5 分钟搭 Demo", fw: "Agno", reason: "最快上手，最小样板" },
  { scene: "角色扮演协作", fw: "CrewAI", reason: "角色抽象最自然" },
  { scene: "Java 技术栈", fw: "Spring AI", reason: "生态一致" },
  { scene: "多 Agent 聊天", fw: "AutoGen", reason: "对话模型成熟" },
  { scene: "强类型偏好", fw: "Pydantic AI", reason: "类型安全" },
  { scene: "LlamaIndex RAG", fw: "Workflows", reason: "生态内集成" },
];

export default function Boundary({ step }: ChapterStepProps) {
  if (step === 0) return <Step0Cards />;
  return <Step1Summary />;
}

function Step0Cards() {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setVisible(count);
      if (count >= SCENES.length) clearInterval(timer);
    }, 200);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="bd-scene scene-pad">
      <div className="bd-header">
        <span className="label-mono">When NOT to choose LangGraph</span>
      </div>
      <div className="bd-grid">
        {SCENES.map((s, i) => (
          <div
            key={s.scene}
            className={`bd-card ${i < visible ? "bd-visible" : ""}`}
          >
            <div className="bd-card-scene">{s.scene}</div>
            <div className="bd-card-fw">→ {s.fw}</div>
            <div className="bd-card-reason">{s.reason}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Step1Summary() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 200);
    return () => clearTimeout(t);
  }, []);

  const keywords = ["精确控制", "状态透明", "可持久化", "可人机协作"];

  return (
    <div className="bd-scene center">
      <div className={`bd-summary ${show ? "bd-in" : ""}`}>
        <div className="bd-summary-label label-mono">LangGraph IS for</div>
        <div className="bd-keywords">
          {keywords.map((kw, i) => (
            <span key={kw} className="bd-keyword" style={{ animationDelay: `${i * 150}ms` }}>
              {kw}
            </span>
          ))}
        </div>
        <div className="bd-arrow">↓</div>
        <div className="bd-choose">选 LangGraph</div>
      </div>
    </div>
  );
}
