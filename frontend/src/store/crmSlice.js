import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), options.timeoutMs || 12000);
  const { timeoutMs, ...fetchOptions } = options;

  try {
    const response = await fetch(`${API_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(fetchOptions.headers || {})
      },
      ...fetchOptions,
      signal: fetchOptions.signal || controller.signal
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(formatApiError(response.status, detail));
    }
    return response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(`Backend timed out at ${API_URL}. Check the Render service health.`);
    }
    if (error instanceof TypeError) {
      throw new Error(`Cannot reach backend at ${API_URL}. Check VITE_API_URL and CORS_ORIGINS.`);
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export const fetchHealth = createAsyncThunk("crm/fetchHealth", async () => api("/health", { timeoutMs: 6000 }));

export const fetchHcps = createAsyncThunk("crm/fetchHcps", async () => api("/hcps"));

export const fetchInteractions = createAsyncThunk("crm/fetchInteractions", async (hcpId) => {
  const query = hcpId ? `?hcp_id=${hcpId}` : "";
  return api(`/interactions${query}`);
});

export const fetchInsights = createAsyncThunk("crm/fetchInsights", async (hcpId) => {
  const query = hcpId ? `?hcp_id=${hcpId}` : "";
  return api(`/insights/summary${query}`);
});

export const createInteraction = createAsyncThunk("crm/createInteraction", async (payload) =>
  api("/interactions", {
    method: "POST",
    body: JSON.stringify(payload)
  })
);

export const updateInteraction = createAsyncThunk("crm/updateInteraction", async ({ id, payload }) =>
  api(`/interactions/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  })
);

export const sendAgentMessage = createAsyncThunk("crm/sendAgentMessage", async ({ message, hcp_id }) =>
  api("/agent/chat", {
    method: "POST",
    body: JSON.stringify({ message, hcp_id })
  })
);

export const runAgentTool = createAsyncThunk(
  "crm/runAgentTool",
  async ({ toolName, hcpId, interactionId, payload = {} }) =>
    api(`/agent/tools/${toolName}`, {
      method: "POST",
      body: JSON.stringify({
        hcp_id: hcpId,
        interaction_id: interactionId,
        payload
      })
    })
);

const initialState = {
  hcps: [],
  interactions: [],
  selectedHcpId: null,
  selectedTab: "form",
  status: "idle",
  error: null,
  apiHealth: {
    status: "checking",
    model: null
  },
  chatMessages: [
    {
      role: "agent",
      content: "Ready for HCP context."
    }
  ],
  insights: {
    total_interactions: 0,
    flagged_interactions: 0,
    average_quality_score: 0,
    top_topics: []
  },
  toolRuns: []
};

const crmSlice = createSlice({
  name: "crm",
  initialState,
  reducers: {
    selectHcp(state, action) {
      state.selectedHcpId = action.payload;
    },
    selectTab(state, action) {
      state.selectedTab = action.payload;
    },
    clearError(state) {
      state.error = null;
    },
    pushUserMessage(state, action) {
      state.chatMessages.push({ role: "user", content: action.payload });
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.pending, (state) => {
        state.status = "loading";
      })
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.hcps = action.payload;
        state.selectedHcpId = state.selectedHcpId || action.payload[0]?.id || null;
        state.status = "idle";
      })
      .addCase(fetchHcps.rejected, (state, action) => {
        state.error = action.error.message;
        state.status = "error";
      })
      .addCase(fetchHealth.pending, (state) => {
        state.apiHealth.status = "checking";
      })
      .addCase(fetchHealth.fulfilled, (state, action) => {
        state.apiHealth = {
          status: "connected",
          model: action.payload.model
        };
      })
      .addCase(fetchHealth.rejected, (state, action) => {
        state.apiHealth = {
          status: "offline",
          model: null
        };
        state.error = action.error.message;
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.interactions = action.payload;
        state.insights = buildInsights(action.payload);
      })
      .addCase(fetchInsights.fulfilled, (state, action) => {
        state.insights = action.payload;
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        const interaction = action.payload.result.interaction;
        state.interactions = [interaction, ...state.interactions.filter((item) => item.id !== interaction.id)];
        state.insights = buildInsights(state.interactions);
        state.toolRuns.unshift(action.payload);
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        const interaction = action.payload.result.interaction;
        state.interactions = state.interactions.map((item) => (item.id === interaction.id ? interaction : item));
        state.insights = buildInsights(state.interactions);
        state.toolRuns.unshift(action.payload);
      })
      .addCase(sendAgentMessage.pending, (state) => {
        state.status = "thinking";
      })
      .addCase(sendAgentMessage.fulfilled, (state, action) => {
        state.status = "idle";
        state.toolRuns.unshift(action.payload);
        state.chatMessages.push({
          role: "agent",
          content: formatAgentResult(action.payload)
        });
        if (action.payload.result.interaction) {
          const interaction = action.payload.result.interaction;
          state.interactions = [interaction, ...state.interactions.filter((item) => item.id !== interaction.id)];
          state.insights = buildInsights(state.interactions);
        }
      })
      .addCase(runAgentTool.fulfilled, (state, action) => {
        state.toolRuns.unshift(action.payload);
        if (action.payload.result.interaction) {
          const interaction = action.payload.result.interaction;
          state.interactions = [interaction, ...state.interactions.filter((item) => item.id !== interaction.id)];
          state.insights = buildInsights(state.interactions);
        }
      })
      .addMatcher(
        (action) => action.type.startsWith("crm/") && action.type.endsWith("/rejected"),
        (state, action) => {
          state.status = "error";
          state.error = action.error.message;
        }
      );
  }
});

function formatAgentResult(result) {
  const { tool_name: toolName, result: payload } = result;
  if (payload.message && payload.interaction) {
    return `${payload.message}: ${payload.interaction.summary}`;
  }
  if (payload.recommendation) {
    return payload.recommendation;
  }
  if (payload.body) {
    return payload.body;
  }
  if (payload.hcp) {
    return `${payload.hcp.full_name}, ${payload.hcp.specialty}, tier ${payload.hcp.tier}.`;
  }
  return `${toolName} completed.`;
}

function buildInsights(interactions) {
  const topicCounts = new Map();
  interactions.forEach((interaction) => {
    (interaction.topics || []).forEach((topic) => {
      topicCounts.set(topic, (topicCounts.get(topic) || 0) + 1);
    });
  });
  const total = interactions.length;
  const qualityTotal = interactions.reduce((sum, interaction) => sum + (interaction.call_quality_score || 0), 0);
  return {
    total_interactions: total,
    flagged_interactions: interactions.filter((interaction) => interaction.compliance_flags?.length).length,
    average_quality_score: total ? Math.round(qualityTotal / total) : 0,
    top_topics: Array.from(topicCounts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4)
      .map(([name, count]) => ({ name, count }))
  };
}

function formatApiError(status, detail) {
  try {
    const parsed = JSON.parse(detail);
    return parsed.detail ? `${status}: ${parsed.detail}` : `${status}: API request failed`;
  } catch {
    return detail ? `${status}: ${detail}` : `${status}: API request failed`;
  }
}

export const { clearError, pushUserMessage, selectHcp, selectTab } = crmSlice.actions;
export default crmSlice.reducer;
