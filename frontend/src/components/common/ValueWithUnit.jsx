

function ValueWithUnit({ value, unit, format }) {
  if (value === null || value === undefined) {
    return (
      <span className="text-sm text-gray-400 italic">
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