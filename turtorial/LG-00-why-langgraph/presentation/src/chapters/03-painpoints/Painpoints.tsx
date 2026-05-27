import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Painpoints.css";

const SPAGHETTI_CODE = `def customer_service(user_input):
    intent = classify(user_input)

    if intent == "order":
        result = query_order(user_input)
        if result.needs_retry:        # ← 重试散落
            result = retry_query(...)
        return format(result)

    elif intent == "refund":
        result = process_refund(user_input)
        if result.high_risk:          # ← 人工介入无统一机制
            send_to_human(result)     # ← 异步？同步？状态怎么存？
            return {"status": "pending"}
        return format(result)

    elif intent == "faq":
        return search_faq(user_input)

    else:
        return escalate(user_input)
    # 加新分支 = 改函数 + 改调用方 + 改测试`;

const CREWAI_CODE = `from crewai import Agent, Task, Crew

router = Agent(role="意图识别员")
order_agent = Agent(role="订单专员")
refund_agent = Agent(role="退款专员")
faq_agent = Agent(role="客服专员")

tasks = [
    Task(description="识别意图", agent=router),
    Task(description="处理订单", agent=order_agent),
    ...
]

crew = Crew(agents=[...], tasks=[...])
crew.kickoff()

# 路由逻辑在哪里？← 隐式！
# Agent 之间传递了什么？← 不透明！
# 循环重试怎么做？← 没有原生支持！`;

const LANGGRAPH_CODE = `class AgentState(TypedDict):
    user_input: str
    intent: str
    result: str

def classify(state): ...
def handle_order(state): ...
def handle_refund(state): ...

def route(state):
    return state["intent"]  # → "order"/"refund"/"faq"/"human"

workflow = StateGraph(AgentState)
workflow.add_node("classify", classify)
workflow.add_node("order", handle_order)
workflow.add_conditional_edges("classify", route)

# 加新分支 = add_node + add_edge 两行代码`;

export default function Painpoints({ step }: ChapterStepProps) {
  if (step === 0) return <Step0Spaghetti />;
  if (step === 1) return <Step1Crewai />;
  if (step === 2) return <Step2Langgraph />;
  if (step === 3) return <Step3Stream />;
  return <Step4Loop />;
}

/* ─── Step 0: Spaghetti code ─── */
function Step0Spaghetti() {
  const [lines, setLines] = useState(0);

  useEffect(() => {
    const allLines = SPAGHETTI_CODE.split("\n");
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setLines(count);
      if (count >= allLines.length) clearInterval(timer);
    }, 80);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="pp-scene scene-pad">
      <div className="pp-header">
        <span className="label-mono">Method 1 — Script</span>
        <span className="pp-badge pp-bad">意大利面条</span>
      </div>
      <div className="pp-code-wrap">
        <pre className="pp-code">
          {SPAGHETTI_CODE.split("\n").map((line, i) => (
            <div
              key={i}
              className={`pp-code-line ${i < lines ? "pp-visible" : ""} ${
                line.includes("←") ? "pp-comment" : ""
              }`}
            >
              {line}
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}

/* ─── Step 1: CrewAI ─── */
function Step1Crewai() {
  const [lines, setLines] = useState(0);

  useEffect(() => {
    const allLines = CREWAI_CODE.split("\n");
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setLines(count);
      if (count >= allLines.length) clearInterval(timer);
    }, 80);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="pp-scene scene-pad">
      <div className="pp-header">
        <span className="label-mono">Method 2 — CrewAI</span>
        <span className="pp-badge pp-warn">路由隐式</span>
      </div>
      <div className="pp-code-wrap">
        <pre className="pp-code">
          {CREWAI_CODE.split("\n").map((line, i) => (
            <div
              key={i}
              className={`pp-code-line ${i < lines ? "pp-visible" : ""} ${
                line.includes("←") ? "pp-comment" : ""
              }`}
            >
              {line}
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}

/* ─── Step 2: LangGraph + graph viz ─── */
function Step2Langgraph() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 300);
    return () => clearTimeout(t);
  }, []);

  const lines = LANGGRAPH_CODE.split("\n");

  return (
    <div className="pp-scene scene-pad">
      <div className="pp-header">
        <span className="label-mono">Method 3 — LangGraph</span>
        <span className="pp-badge pp-good">图编排</span>
      </div>
      <div className="pp-split">
        <div className="pp-code-side">
          <pre className="pp-code">
            {lines.map((line, i) => (
              <div key={i} className={`pp-code-line pp-visible ${line.includes("#") ? "pp-comment" : ""}`}>
                {line}
              </div>
            ))}
          </pre>
        </div>
        <div className="pp-graph-side">
          <div className={`pp-graph ${show ? "pp-in" : ""}`}>
            <div className="pp-node pp-start">START</div>
            <div className="pp-edge">↓</div>
            <div className="pp-node pp-highlight">classify</div>
            <div className="pp-branch">
              <div className="pp-edge-diag">↙</div>
              <div className="pp-edge-diag">↙</div>
              <div className="pp-edge-diag">↙</div>
            </div>
            <div className="pp-branch-row">
              <div className="pp-node pp-branch-node">order</div>
              <div className="pp-node pp-branch-node">refund</div>
              <div className="pp-node pp-branch-node">faq</div>
              <div className="pp-node pp-branch-node">human</div>
            </div>
            <div className="pp-edge">↓</div>
            <div className="pp-node pp-end">END</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── Step 3: Stream state ─── */
function Step3Stream() {
  const [step, setStep] = useState(0);

  const states = [
    { label: "step 1", json: '{\n  "user_input": "我要退款",\n  "intent": "",\n  "result": ""\n}' },
    { label: "step 2", json: '{\n  "user_input": "我要退款",\n  "intent": "refund",\n  "result": ""\n}' },
    { label: "step 3", json: '{\n  "user_input": "我要退款",\n  "intent": "refund",\n  "result": "退款申请已提交"\n}' },
  ];

  useEffect(() => {
    let count = 0;
    const timer = setInterval(() => {
      count++;
      setStep(count);
      if (count >= states.length) clearInterval(timer);
    }, 1200);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="pp-scene center">
      <div className="pp-stream-wrap">
        <div className="pp-stream-label label-mono">stream_mode="values"</div>
        {states.map((s, i) => (
          <div key={i} className={`pp-state-block ${i <= step ? "pp-visible" : ""}`}>
            <div className="pp-state-label">{s.label}</div>
            <pre className="pp-state-json">{s.json}</pre>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Step 4: Loop visualization ─── */
function Step4Loop() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setShow(true), 200);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="pp-scene center">
      <div className={`pp-loop-wrap ${show ? "pp-in" : ""}`}>
        <div className="pp-loop-label label-mono">循环 = 图的一等公民</div>
        <div className="pp-loop-diagram">
          <div className="pp-loop-node">call_api</div>
          <div className="pp-loop-arrow-wrap">
            <svg className="pp-loop-svg" viewBox="0 0 200 120">
              <path
                className="pp-loop-path"
                d="M 40 20 L 160 20"
                fill="none"
                stroke="var(--accent)"
                strokeWidth="2"
              />
              <path
                className="pp-loop-path pp-loop-curve"
                d="M 160 20 C 200 20, 200 100, 160 100 L 40 100"
                fill="none"
                stroke="var(--accent)"
                strokeWidth="2"
                strokeDasharray="8 4"
                opacity="0.6"
              />
              <text x="100" y="65" textAnchor="middle" fill="var(--accent)" fontSize="12">
                retry_count &lt; 3
              </text>
            </svg>
          </div>
          <div className="pp-loop-node pp-loop-cond">should_retry</div>
        </div>
        <div className="pp-loop-note">
          条件边: failed → call_api | done → END
        </div>
      </div>
    </div>
  );
}
