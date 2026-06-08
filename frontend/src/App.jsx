import { useEffect, useMemo } from "react";
import { Activity, BrainCircuit, ClipboardList, MessageSquareText, Server, ShieldCheck, Sparkles } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";

import AgentChat from "./components/AgentChat.jsx";
import HcpSidebar from "./components/HcpSidebar.jsx";
import InteractionForm from "./components/InteractionForm.jsx";
import InteractionTimeline from "./components/InteractionTimeline.jsx";
import InsightsStrip from "./components/InsightsStrip.jsx";
import ToolConsole from "./components/ToolConsole.jsx";
import { fetchHcps, fetchHealth, fetchInsights, fetchInteractions, selectTab } from "./store/crmSlice.js";

export default function App() {
  const dispatch = useDispatch();
  const { apiHealth, hcps, interactions, selectedHcpId, selectedTab, status, error } = useSelector((state) => state.crm);
  const selectedHcp = useMemo(
    () => hcps.find((hcp) => hcp.id === selectedHcpId),
    [hcps, selectedHcpId]
  );

  useEffect(() => {
    dispatch(fetchHealth());
    dispatch(fetchHcps());
  }, [dispatch]);

  useEffect(() => {
    if (selectedHcpId) {
      dispatch(fetchInteractions(selectedHcpId));
      dispatch(fetchInsights(selectedHcpId));
    }
  }, [dispatch, selectedHcpId]);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark">
            <BrainCircuit size={22} />
          </div>
          <div>
            <p>AI-First CRM</p>
            <strong>HCP Module</strong>
          </div>
        </div>
        <HcpSidebar />
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Log Interaction Screen</p>
            <h1>{selectedHcp ? selectedHcp.full_name : "HCP Interactions"}</h1>
          </div>
          <div className="statusCluster">
            <span className="modelBadge">
              <Sparkles size={15} />
              Groq {apiHealth.model || "gemma2-9b-it"}
            </span>
            <span className={`modelBadge api ${apiHealth.status}`}>
              <Server size={15} />
              {apiHealth.status === "connected"
                ? "API Connected"
                : apiHealth.status === "offline"
                  ? "API Offline"
                  : "API Checking"}
            </span>
            <span className="modelBadge compliance">
              <ShieldCheck size={15} />
              Compliance Guarded
            </span>
            <span className={`systemStatus ${status}`}>{status === "thinking" ? "Agent thinking" : "Ready"}</span>
          </div>
        </header>

        {error ? <div className="errorBanner">{error}</div> : null}

        {selectedHcp ? (
          <div className="grid">
            <InsightsStrip />

            <section className="primaryPanel">
              <div className="hcpContext">
                <div>
                  <p className="eyebrow">{selectedHcp.specialty}</p>
                  <h2>{selectedHcp.organization}</h2>
                  <p>{selectedHcp.persona_notes}</p>
                </div>
                <div className="hcpFacts">
                  <span>Tier {selectedHcp.tier}</span>
                  <span>{selectedHcp.territory}</span>
                  <span>{selectedHcp.preferred_channel}</span>
                </div>
              </div>

              <div className="segment">
                <button
                  className={selectedTab === "form" ? "active" : ""}
                  onClick={() => dispatch(selectTab("form"))}
                  type="button"
                >
                  <ClipboardList size={16} />
                  Form
                </button>
                <button
                  className={selectedTab === "chat" ? "active" : ""}
                  onClick={() => dispatch(selectTab("chat"))}
                  type="button"
                >
                  <MessageSquareText size={16} />
                  AI Chat
                </button>
              </div>

              {selectedTab === "form" ? <InteractionForm hcp={selectedHcp} /> : <AgentChat hcp={selectedHcp} />}
            </section>

            <section className="sidePanel">
              <ToolConsole hcp={selectedHcp} interactions={interactions} />
            </section>

            <section className="timelinePanel">
              <div className="sectionTitle">
                <Activity size={18} />
                <h2>Interaction Timeline</h2>
              </div>
              <InteractionTimeline interactions={interactions} />
            </section>
          </div>
        ) : (
          <div className="emptyState">Loading HCP workspace...</div>
        )}
      </section>
    </main>
  );
}
