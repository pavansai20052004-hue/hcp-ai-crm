import { CalendarDays, CheckCircle2, ShieldAlert, Target } from "lucide-react";

export default function InteractionTimeline({ interactions }) {
  if (!interactions.length) {
    return <div className="emptyState">No interactions logged yet.</div>;
  }

  return (
    <div className="timeline">
      {interactions.map((interaction) => (
        <article className="timelineItem" key={interaction.id}>
          <div className="timelineHead">
            <span>
              <CheckCircle2 size={16} />
              {interaction.interaction_type}
            </span>
            <time>{new Date(interaction.occurred_at).toLocaleString()}</time>
          </div>
          <p>{interaction.summary}</p>
          <div className="tagRow">
            <span>{interaction.channel}</span>
            <span>{interaction.sentiment}</span>
            <span>{interaction.call_quality_score}% quality</span>
            {(interaction.products || []).map((product) => (
              <span key={product}>{product}</span>
            ))}
          </div>
          {interaction.objections?.length ? (
            <div className="detailLine">
              <Target size={15} />
              {interaction.objections.join(", ")}
            </div>
          ) : null}
          {interaction.compliance_flags?.length ? (
            <div className="flagLine">
              <ShieldAlert size={15} />
              {interaction.compliance_flags.join(", ")}
            </div>
          ) : null}
          {interaction.next_best_action ? (
            <div className="nextAction">
              <CalendarDays size={16} />
              {interaction.next_best_action}
            </div>
          ) : null}
        </article>
      ))}
    </div>
  );
}
