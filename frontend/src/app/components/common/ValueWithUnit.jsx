

function ValueWithUnit({ value, unit, format }) {
  if (value === null || value === undefined) {
    return (
      <span className="text-sm text-muted-foreground italic">
        No data provided
      </span>
    );
  }

  return (
    <>
      {format(value)}
      {unit}
    </>
  );
}

export default ValueWithUnit