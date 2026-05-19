import { Gauge, ListChecks, ShieldAlert, Tags } from "lucide-react";
import { useSelector } from "react-redux";

export default function InsightsStrip() {
  const { insights } = useSelector((state) => state.crm);
  const topTopic = insights.top_topics?.[0]?.name || "No topic yet";

  const items = [
    {
      label: "Interactions",
      value: insights.total_interactions,
      icon: ListChecks
    },
    {
      label: "Quality score",
      value: `${insights.average_quality_score || 0}%`,
      icon: Gauge
    },
    {
      label: "Compliance flags",
      value: insights.flagged_interactions,
      icon: ShieldAlert
    },
    {
      label: "Top topic",
      value: topTopic,
      icon: Tags
    }
  ];

  return (
    <section className="insightsStrip" aria-label="HCP interaction insights">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <article key={item.label}>
            <Icon size={18} />
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </article>
        );
      })}
    </section>
  );
}

