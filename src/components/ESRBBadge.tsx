interface Props {
  rating: string | null;
  minAge: number | null;
  size?: 'sm' | 'lg';
}

const ESRB_CONFIG: Record<string, { label: string; color: string; description: string }> = {
  E: { label: 'E', color: 'bg-green-600', description: 'Everyone (6+)' },
  E10: { label: 'E10+', color: 'bg-emerald-500', description: 'Everyone 10+' },
  T: { label: 'T', color: 'bg-yellow-500 text-gray-900', description: 'Teen (13+)' },
  M: { label: 'M', color: 'bg-orange-600', description: 'Mature (17+)' },
  AO: { label: 'AO', color: 'bg-red-600', description: 'Adults Only (18+)' },
};

export function ESRBBadge({ rating, minAge, size = 'sm' }: Props) {
  if (!rating) {
    return (
      <span
        className={`inline-flex items-center justify-center rounded font-bold text-gray-400 bg-gray-700 ${
          size === 'lg' ? 'px-3 py-1.5 text-base' : 'px-2 py-0.5 text-xs'
        }`}
        title="Not rated"
      >
        NR
      </span>
    );
  }

  const config = ESRB_CONFIG[rating] || { label: rating, color: 'bg-gray-600', description: rating };

  return (
    <span
      className={`inline-flex items-center justify-center rounded font-bold text-white ${config.color} ${
        size === 'lg' ? 'px-3 py-1.5 text-base' : 'px-2 py-0.5 text-xs'
      }`}
      title={`${config.description}${minAge ? ` - Ages ${minAge}+` : ''}`}
    >
      {config.label}
    </span>
  );
}
