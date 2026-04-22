type StatusBadgeProps = {
  value: string;
};

function normalizeStatus(value: string): string {
  return value.trim().toLowerCase().replaceAll(" ", "_");
}

function getStatusClass(value: string): string {
  const normalized = normalizeStatus(value);

  if (
    normalized === "completed" ||
    normalized === "active" ||
    normalized === "registration_open" ||
    normalized === "finished"
  ) {
    return "is-success";
  }

  if (
    normalized === "cancelled" ||
    normalized === "failed" ||
    normalized === "error"
  ) {
    return "is-danger";
  }

  if (
    normalized === "in_progress" ||
    normalized === "scheduled" ||
    normalized === "registration_closed"
  ) {
    return "is-warning";
  }

  return "is-neutral";
}

export default function StatusBadge({ value }: StatusBadgeProps) {
  return (
    <span className={`ui-status-badge ${getStatusClass(value)}`}>{value}</span>
  );
}