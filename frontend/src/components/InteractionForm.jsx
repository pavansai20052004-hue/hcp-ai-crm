import { useState } from "react";
import { CalendarClock, Save } from "lucide-react";
import { useDispatch } from "react-redux";

import { createInteraction } from "../store/crmSlice.js";

const defaultForm = {
  channel: "In person",
  interaction_type: "Detailing",
  sentiment: "Neutral",
  raw_notes: "",
  summary: "",
  products: "CardioFlow",
  topics: "efficacy, access",
  objections: "",
  commitments: "",
  follow_up_date: "",
  follow_up_owner: "Field Rep"
};

export default function InteractionForm({ hcp }) {
  const dispatch = useDispatch();
  const [form, setForm] = useState(defaultForm);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    dispatch(
      createInteraction({
        hcp_id: hcp.id,
        channel: form.channel,
        interaction_type: form.interaction_type,
        sentiment: form.sentiment,
        summary: form.summary || undefined,
        raw_notes: form.raw_notes,
        products: splitList(form.products),
        topics: splitList(form.topics),
        objections: splitList(form.objections),
        commitments: splitList(form.commitments),
        follow_up_date: form.follow_up_date || undefined,
        follow_up_owner: form.follow_up_owner
      })
    );
    setForm((current) => ({ ...current, raw_notes: "", summary: "" }));
  }

  return (
    <form className="interactionForm" onSubmit={handleSubmit}>
      <div className="formGrid">
        <label>
          Channel
          <select value={form.channel} onChange={(event) => updateField("channel", event.target.value)}>
            <option>In person</option>
            <option>Email</option>
            <option>Phone</option>
            <option>Video call</option>
            <option>Conference</option>
          </select>
        </label>

        <label>
          Interaction type
          <select
            value={form.interaction_type}
            onChange={(event) => updateField("interaction_type", event.target.value)}
          >
            <option>Detailing</option>
            <option>Scientific exchange</option>
            <option>Access discussion</option>
            <option>Follow-up</option>
            <option>Speaker program</option>
          </select>
        </label>

        <label>
          Sentiment
          <select value={form.sentiment} onChange={(event) => updateField("sentiment", event.target.value)}>
            <option>Interested</option>
            <option>Neutral</option>
            <option>Concerned</option>
            <option>Needs evidence</option>
          </select>
        </label>

        <label>
          Follow-up date
          <span className="inputIcon">
            <CalendarClock size={16} />
            <input
              type="date"
              value={form.follow_up_date}
              onChange={(event) => updateField("follow_up_date", event.target.value)}
            />
          </span>
        </label>

        <label>
          Products
          <input value={form.products} onChange={(event) => updateField("products", event.target.value)} />
        </label>

        <label>
          Topics
          <input value={form.topics} onChange={(event) => updateField("topics", event.target.value)} />
        </label>

        <label>
          Objections
          <input
            value={form.objections}
            onChange={(event) => updateField("objections", event.target.value)}
            placeholder="access, evidence, time"
          />
        </label>

        <label>
          Commitments
          <input
            value={form.commitments}
            onChange={(event) => updateField("commitments", event.target.value)}
            placeholder="send study, book follow-up"
          />
        </label>
      </div>

      <label>
        Executive summary
        <input
          value={form.summary}
          onChange={(event) => updateField("summary", event.target.value)}
          placeholder="Optional short summary"
        />
      </label>

      <label>
        Field notes
        <textarea
          required
          value={form.raw_notes}
          onChange={(event) => updateField("raw_notes", event.target.value)}
          placeholder={`Meeting notes for ${hcp.full_name}`}
          rows={7}
        />
      </label>

      <button className="primaryButton" type="submit">
        <Save size={17} />
        Log Interaction
      </button>
    </form>
  );
}

function splitList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
