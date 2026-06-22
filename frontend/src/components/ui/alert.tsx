type AlertVariant = "error" | "success" | "info";

type AlertProps = {
  variant?: AlertVariant;
  title?: string;
  children: React.ReactNode;
};

export default function Alert({
  variant = "info",
  title,
  children,
}: AlertProps) {
  return (
    <div className={`ui-alert ui-alert--${variant}`} role="alert">
      {title ? <div className="ui-alert__title">{title}</div> : null}
      <div className="ui-alert__content">{children}</div>
    </div>
  );
}