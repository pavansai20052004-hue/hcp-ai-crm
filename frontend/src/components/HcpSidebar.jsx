import { Mail, MapPin, Stethoscope } from "lucide-react";
import { useDispatch, useSelector } from "react-redux";

import { selectHcp } from "../store/crmSlice.js";

export default function HcpSidebar() {
  const dispatch = useDispatch();
  const { hcps, selectedHcpId } = useSelector((state) => state.crm);

  return (
    <div className="hcpList">
      {hcps.map((hcp) => (
        <button
          className={`hcpButton ${selectedHcpId === hcp.id ? "selected" : ""}`}
          key={hcp.id}
          onClick={() => dispatch(selectHcp(hcp.id))}
          type="button"
        >
          <span className="avatar">{hcp.full_name.split(" ").slice(-1)[0][0]}</span>
          <span className="hcpMeta">
            <strong>{hcp.full_name}</strong>
            <span>
              <Stethoscope size={13} />
              {hcp.specialty}
            </span>
            <span>
              <MapPin size={13} />
              {hcp.territory}
            </span>
            <span>
              <Mail size={13} />
              {hcp.preferred_channel}
            </span>
          </span>
          <em>Tier {hcp.tier}</em>
        </button>
      ))}
    </div>
  );
}

