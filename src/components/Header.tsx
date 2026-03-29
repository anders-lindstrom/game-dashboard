import type { Game } from '../types';

interface Props {
  games: Game[];
  totalCount: number;
}

export function Header({ games, totalCount }: Props) {
  const sunshineCount = games.filter((g) => g.in_sunshine).length;
  const withMetacritic = games.filter((g) => g.metacritic !== null);
  const avgMetacritic =
    withMetacritic.length > 0
      ? Math.round(
          withMetacritic.reduce((sum, g) => sum + (g.metacritic ?? 0), 0) /
            withMetacritic.length
        )
      : null;

  return (
    <header className="py-6 px-4 sm:px-6">
      <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight">
        Game Library
      </h1>
      <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-400">
        <span>
          <span className="text-white font-medium">{totalCount}</span> games
        </span>
        <span>
          <span className="text-amber-400 font-medium">{sunshineCount}</span> streaming
        </span>
        {avgMetacritic && (
          <span>
            Avg Metacritic: <span className="text-green-400 font-medium">{avgMetacritic}</span>
          </span>
        )}
        {games.length !== totalCount && (
          <span>
            Showing <span className="text-indigo-400 font-medium">{games.length}</span> results
          </span>
        )}
      </div>
    </header>
  );
}
