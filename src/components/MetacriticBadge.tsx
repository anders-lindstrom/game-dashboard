interface Props {
  score: number | null;
  size?: 'sm' | 'lg';
}

export function MetacriticBadge({ score, size = 'sm' }: Props) {
  if (score === null) {
    return (
      <span
        className={`inline-flex items-center justify-center rounded font-bold text-gray-400 bg-gray-700 ${
          size === 'lg' ? 'w-12 h-12 text-xl' : 'w-8 h-8 text-xs'
        }`}
      >
        --
      </span>
    );
  }

  const bg =
    score >= 75
      ? 'bg-green-600'
      : score >= 50
        ? 'bg-yellow-500 text-gray-900'
        : 'bg-red-600';

  return (
    <span
      className={`inline-flex items-center justify-center rounded font-bold text-white ${bg} ${
        size === 'lg' ? 'w-12 h-12 text-xl' : 'w-8 h-8 text-xs'
      }`}
      title={`Metacritic: ${score}`}
    >
      {score}
    </span>
  );
}
