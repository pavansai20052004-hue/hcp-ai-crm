import { useState } from "react";
import { SendHorizonal } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";

import { pushUserMessage, sendAgentMessage } from "../store/crmSlice.js";

export default function AgentChat({ hcp }) {
  const dispatch = useDispatch();
  const { chatMessages, status } = useSelector((state) => state.crm);
  const [message, setMessage] = useState(
    `I met ${hcp.full_name} today. They asked for more efficacy evidence and want a follow-up next week.`
  );

  function sendMessage(event) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) return;
    dispatch(pushUserMessage(trimmed));
    dispatch(sendAgentMessage({ message: trimmed, hcp_id: hcp.id }));
    setMessage("");
  }

  return (
    <section className="chatPanel">
      <div className="messages">
        {chatMessages.map((item, index) => (
          <div className={`message ${item.role}`} key={`${item.role}-${index}`}>
            {item.content}
          </div>
        ))}
        {status === "thinking" ? <div className="message agent">Processing with LangGraph...</div> : null}
      </div>

      <form className="chatComposer" onSubmit={sendMessage}>
        <textarea value={message} onChange={(event) => setMessage(event.target.value)} rows={4} />
        <button className="iconButton send" type="submit" title="Send to AI agent">
          <SendHorizonal size={19} />
        </button>
      </form>
    </section>
  );
}

