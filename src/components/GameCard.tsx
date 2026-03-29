import type { Game } from '../types';
import { MetacriticBadge } from './MetacriticBadge';
import { ESRBBadge } from './ESRBBadge';
import { SunshineBadge } from './SunshineBadge';

interface Props {
  game: Game;
  onClick: (game: Game) => void;
}

export function GameCard({ game, onClick }: Props) {
  return (
    <button
      onClick={() => onClick(game)}
      className="group relative bg-gray-800 rounded-lg overflow-hidden text-left transition-all hover:ring-2 hover:ring-indigo-500 hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
    >
      {/* Cover image */}
      <div className="aspect-video bg-gray-900 relative overflow-hidden">
        {game.background_image ? (
          <img
            src={game.background_image}
            alt={game.name}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-600">
            <span className="text-4xl">?</span>
          </div>
        )}

        {/* Metacritic overlay */}
        <div className="absolute top-2 right-2">
          <MetacriticBadge score={game.metacritic} />
        </div>

        {/* Sunshine overlay */}
        <div className="absolute top-2 left-2">
          <SunshineBadge active={game.in_sunshine} />
        </div>
      </div>

      {/* Info */}
      <div className="p-3 space-y-2">
        <h3 className="font-semibold text-white text-sm leading-tight truncate" title={game.name}>
          {game.name}
        </h3>

        <div className="flex items-center gap-2 flex-wrap">
          <ESRBBadge rating={game.esrb_rating} minAge={game.min_age} />
          {game.genres?.slice(0, 2).map((genre) => (
            <span
              key={genre}
              className="text-xs px-2 py-0.5 rounded-full bg-gray-700 text-gray-300"
            >
              {genre}
            </span>
          ))}
        </div>

        {game.rawg_rating != null && (
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <span className="text-yellow-400">{'★'.repeat(Math.round(game.rawg_rating))}</span>
            <span>{game.rawg_rating.toFixed(1)}</span>
          </div>
        )}
      </div>
    </button>
  );
}
