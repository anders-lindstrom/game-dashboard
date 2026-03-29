import { FiCast } from 'react-icons/fi';

interface Props {
  active: boolean;
  size?: 'sm' | 'lg';
}

export function SunshineBadge({ active, size = 'sm' }: Props) {
  if (!active) return null;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full bg-amber-500/20 text-amber-400 font-medium ${
        size === 'lg' ? 'px-3 py-1 text-sm' : 'px-2 py-0.5 text-xs'
      }`}
      title="Available for Sunshine streaming"
    >
      <FiCast className={size === 'lg' ? 'w-4 h-4' : 'w-3 h-3'} />
      {size === 'lg' && 'Sunshine'}
    </span>
  );
}
