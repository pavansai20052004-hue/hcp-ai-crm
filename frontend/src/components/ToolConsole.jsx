import { Bot, FilePenLine, MailPlus, PlusCircle, Route, ShieldCheck, UserRoundSearch } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";

import { runAgentTool } from "../store/crmSlice.js";

const toolButtons = [
  {
    name: "log_interaction",
    label: "Log",
    icon: PlusCircle,
    payload: {
      channel: "AI Chat",
      interaction_type: "Quick note",
      raw_notes: "AI demo note: HCP requested concise efficacy data and payer access resources.",
      products: ["CardioFlow"],
      topics: ["efficacy", "access"]
    }
  },
  {
    name: "edit_interaction",
    label: "Edit",
    icon: FilePenLine,
    payload: {
      sentiment: "Interested",
      next_best_action: "Send evidence pack and confirm a follow-up meeting this week."
    }
  },
  { name: "get_hcp_profile", label: "Profile", icon: UserRoundSearch, payload: {} },
  { name: "suggest_next_best_action", label: "Next Action", icon: Route, payload: {} },
  { name: "draft_follow_up", label: "Email", icon: MailPlus, payload: {} },
  { name: "compliance_review", label: "Compliance", icon: ShieldCheck, payload: {} }
];

export default function ToolConsole({ hcp, interactions }) {
  const dispatch = useDispatch();
  const { toolRuns } = useSelector((state) => state.crm);
  const latestInteraction = interactions[0];

  function runTool(tool) {
    dispatch(
      runAgentTool({
        toolName: tool.name,
        hcpId: hcp.id,
        interactionId: tool.name === "edit_interaction" ? latestInteraction?.id : undefined,
        payload: tool.payload
      })
    );
  }

  return (
    <div className="toolConsole">
      <div className="sectionTitle">
        <Bot size={18} />
        <h2>LangGraph Tools</h2>
      </div>

      <div className="toolGrid">
        {toolButtons.map((tool) => {
          const Icon = tool.icon;
          return (
            <button className="toolButton" key={tool.name} onClick={() => runTool(tool)} type="button">
              <Icon size={18} />
              {tool.label}
            </button>
          );
        })}
      </div>

      <div className="toolOutput">
        {toolRuns.slice(0, 3).map((run, index) => (
          <article key={`${run.tool_name}-${index}`}>
            <span>{run.tool_name.replaceAll("_", " ")}</span>
            <p>{summarize(run)}</p>
          </article>
        ))}
      </div>
    </div>
  );
}

function summarize(run) {
  const payload = run.result;
  if (payload.interaction) return payload.interaction.summary;
  if (payload.recommendation) return payload.recommendation;
  if (payload.body) return payload.body;
  if (payload.status) return `${payload.status}: ${payload.recommended_action}`;
  if (payload.hcp) return `${payload.hcp.full_name} - ${payload.hcp.specialty}`;
  return payload.message || "Completed";
}
