import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Compare.css";

const FRAMEWORKS = [
  { name: "LangGraph", tag: "图编排框架", oneLine: "精确控制 Agent 的每一步走向" },
  { name: "CrewAI", tag: "角色协作框架", oneLine: "一群角色鲜明的 Agent 协作写报告" },
  { name: "Agno", tag: "轻量工具包", oneLine: "5 分钟跑起来一个 Agent" },
  { name: "AutoGen", tag: "对话协作框架", oneLine: "多 Agent 聊天解决问题" },
  { name: "Pydantic AI", tag: "类型安全框架", oneLine: "Pydantic 重度用户首选" },
  { name: "Spring AI", tag: "Java 生态框架", oneLine: "Spring 开发者选它" },
  { name: "LlamaIndex WF", tag: "事件驱动工作流", oneLine: "LlamaIndex 生态内 RAG 编排" },
];

const DIMENSIONS = [
  "状态管理",
  "循环/条件",
  "持久化",
  "人机协作",
  "流式输出",
  "可视化",
  "多Agent",
];

const SCORES: Record<string, number[]> = {
  LangGraph: [5, 5, 5, 5, 5, 4, 5],
  CrewAI: [2, 2, 1, 1, 2, 1, 4],
  Agno: [3, 2, 1, 1, 2, 1, 1],
  AutoGen: [2, 3, 1, 4, 2, 1, 4],
  "Pydantic AI": [3, 2, 1, 1, 2, 1, 1],
  "Spring AI": [2, 2, 1, 1, 2, 1, 1],
  "LlamaIndex WF": [3, 3, 2, 1, 2, 2, 2],
};

export default function Compare({ step }: ChapterStepProps) {
  if (step === 0) return <Step0FrameworkList />;
  if (step === 1) return <Step1DimensionTable />;
  if (step === 2) return <Step2Summary />;
  return <Step3Capabilities />;
}

/* ─── Step 0: Framework list with tags ─── */
function Step0FrameworkList() {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setVisible(count);
      if (count >= FRAMEWORKS.length) clearInterval(timer);
    }, 180);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="cp-scene scene-pad">
      <div className="cp-header">
        <span className="label-mono">Frameworks · 2024-2025</span>
      </div>
      <div className="cp-fw-list">
        {FRAMEWORKS.map((fw, i) => (
          <div
            key={fw.name}
            className={`cp-fw-item ${i < visible ? "cp-visible" : ""}`}
          >
            <span className="cp-fw-name">{fw.name}</span>
            <span className="cp-fw-tag">{fw.tag}</span>
            <span className="cp-fw-line">{fw.oneLine}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Step 1: 7-dimension comparison table ─── */
function Step1DimensionTable() {
  const [visibleRows, setVisibleRows] = useState(0);

  useEffect(() => {
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setVisibleRows(count);
      if (count >= DIMENSIONS.length + 1) clearInterval(timer);
    }, 250);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="cp-scene scene-pad">
      <div className="cp-header">
        <span className="label-mono">7 Dimensions Comparison</span>
      </div>
      <div className="cp-table-wrap">
        <div className="cp-table">
          <div className={`cp-table-header ${visibleRows > 0 ? "cp-visible" : ""}`}>
            <div className="cp-cell cp-dim-cell">维度</div>
            {Object.keys(SCORES).slice(0, 6).map((fw) => (
              <div key={fw} className={`cp-cell cp-fw-cell ${fw === "LangGraph" ? "cp-lg" : ""}`}>
                {fw}
              </div>
            ))}
          </div>
          {DIMENSIONS.map((dim, i) => (
            <div
              key={dim}
              className={`cp-table-row ${visibleRows > i + 1 ? "cp-visible" : ""}`}
            >
              <div className="cp-cell cp-dim-cell">{dim}</div>
              {Object.keys(SCORES).slice(0, 6).map((fw) => {
                const score = SCORES[fw]?.[i] ?? 0;
                const isLG = fw === "LangGraph";
                return (
                  <div key={fw} className={`cp-cell cp-score-cell ${isLG ? "cp-lg" : ""}`}>
                    <div className="cp-bar-wrap">
                      <div
                        className="cp-bar"
                        style={{
                          width: `${score * 20}%`,
                          background: isLG ? "var(--accent)" : "var(--text-faint)",
                          boxShadow: isLG ? "0 0 10px var(--accent-glow)" : "none",
                        }}
                      />
                    </div>
                    <span className="cp-score-num">{score}</span>
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─── Step 2: Summary ─── */
function Step2Summary() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 150);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="cp-scene center">
      <div className={`cp-summary ${show ? "cp-in" : ""}`}>
        <div className="cp-summary-label label-mono">CONCLUSION</div>
        <div className="cp-summary-main">
          唯一七维度
          <br />
          <span className="cp-native">原生支持</span>
        </div>
        <div className="cp-summary-sub">LangGraph 是六边形战士</div>
      </div>
    </div>
  );
}

/* ─── Step 3: Key capabilities ─── */
function Step3Capabilities() {
  const [visible, setVisible] = useState(0);

  const items = [
    { icon: "◈", text: "TypedDict + Reducer 状态管理" },
    { icon: "↻", text: "循环/条件 图原生支持" },
    { icon: "◉", text: "Checkpoint 持久化" },
    { icon: "⚡", text: "interrupt 人机协作" },
    { icon: "▸", text: "5 种流式输出模式" },
    { icon: "◎", text: "Studio + Mermaid 可视化" },
    { icon: "⬡", text: "Subgraph + Handoff 多 Agent" },
  ];

  useEffect(() => {
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setVisible(count);
      if (count >= items.length) clearInterval(timer);
    }, 180);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="cp-scene scene-pad">
      <div className="cp-header">
        <span className="label-mono">Key Capabilities</span>
      </div>
      <div className="cp-cap-grid">
        {items.map((item, i) => (
          <div
            key={item.text}
            className={`cp-cap-item ${i < visible ? "cp-visible" : ""}`}
          >
            <span className="cp-cap-icon">{item.icon}</span>
            <span className="cp-cap-text">{item.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
