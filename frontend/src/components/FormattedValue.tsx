interface FormattedValueProps {
  value: unknown;
}

function humanizeLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function FormattedValue({ value }: FormattedValueProps) {
  if (value === null || value === undefined) {
    return <span className="text-slate-400">Not available</span>;
  }

  if (typeof value === "string") {
    const lines = value.split("\n").filter((line) => line.trim());
    if (lines.length > 1) {
      return (
        <div className="space-y-2">
          {lines.map((line, index) => (
            <p key={index} className="leading-relaxed text-slate-800">
              {line}
            </p>
          ))}
        </div>
      );
    }
    return <p className="leading-relaxed text-slate-800">{value}</p>;
  }

  if (typeof value === "number") {
    return <p className="font-medium text-slate-800">{value}</p>;
  }

  if (typeof value === "boolean") {
    return <p className="text-slate-800">{value ? "Yes" : "No"}</p>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) {
      return <span className="text-slate-400">Empty list</span>;
    }

    if (value.every((item) => typeof item === "string")) {
      return (
        <ul className="list-disc space-y-1.5 pl-5 text-slate-800">
          {(value as string[]).map((item, index) => (
            <li key={index} className="leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
      );
    }

    return (
      <div className="space-y-4">
        {value.map((item, index) => (
          <div
            key={index}
            className="rounded-lg border border-slate-100 bg-slate-50/80 p-3"
          >
            <FormattedValue value={item} />
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>).filter(
      ([, child]) => child !== null && child !== undefined && child !== "",
    );

    if (entries.length === 0) {
      return <span className="text-slate-400">No details</span>;
    }

    return (
      <dl className="space-y-3">
        {entries.map(([key, child]) => (
          <div key={key}>
            <dt className="text-xs font-medium text-slate-500">
              {humanizeLabel(key)}
            </dt>
            <dd className="mt-1">
              <FormattedValue value={child} />
            </dd>
          </div>
        ))}
      </dl>
    );
  }

  return <p className="text-slate-800">{String(value)}</p>;
}
