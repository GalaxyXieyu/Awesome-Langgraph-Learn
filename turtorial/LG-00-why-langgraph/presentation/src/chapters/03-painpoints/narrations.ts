import type { Narration } from "../../registry/types";

export const narrations: Narration[] = [
  "传统脚本写法。if 订单查询嵌套重试，elif 退款嵌套人工审核。逻辑一复杂就是意大利面条。",
  "CrewAI 写法。定义四个角色创建团队，但路由逻辑隐式。谁来决定用哪个 Agent？",
  "LangGraph 写法。定义状态和节点，添加条件边路由到四个分支。结构清晰，扩展简单。",
  "传统框架调试 print 满天飞，LangGraph stream 输出每一步的完整状态。",
  "LangGraph 里循环就是 add_edge 来回连，重试用条件边加计数器。",
];
