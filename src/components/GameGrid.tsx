import type { Game } from '../types';
import { GameCard } from './GameCard';

interface Props {
  games: Game[];
  totalCount: number;
  onSelect: (game: Game) => void;
}

export function GameGrid({ games, totalCount, onSelect }: Props) {
  if (games.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500 py-20">
        <div className="text-center">
          <p className="text-xl mb-2">No games match your filters</p>
          <p className="text-sm">Try adjusting your search or filters</p>
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 sm:px-6 pb-8">
      {games.length !== totalCount && (
        <p className="text-xs text-gray-500 mb-3">
          Showing {games.length} of {totalCount} games
        </p>
      )}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {games.map((game) => (
          <GameCard key={game.id} game={game} onClick={onSelect} />
        ))}
      </div>
    </div>
  );
}
