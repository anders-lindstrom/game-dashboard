import type { Game } from '../types';
import { MetacriticBadge } from './MetacriticBadge';
import { ESRBBadge } from './ESRBBadge';
import { SunshineBadge } from './SunshineBadge';
import { FiX, FiHardDrive, FiCalendar, FiMonitor } from 'react-icons/fi';

interface Props {
  game: Game;
  onClose: () => void;
}

function AgeSummary({ game }: { game: Game }) {
  if (game.min_age === null) {
    return <span className="text-gray-400 text-sm">Age rating not available</span>;
  }
  const color = game.kid_safe
    ? 'text-green-400'
    : game.family_friendly
      ? 'text-yellow-400'
      : 'text-red-400';

  return (
    <div className={`${color} text-sm font-medium`}>
      {game.kid_safe
        ? `Suitable for ages ${game.min_age}+`
        : game.family_friendly
          ? `Teen-appropriate (ages ${game.min_age}+)`
          : `Mature content (ages ${game.min_age}+)`}
      {game.pegi_age && (
        <span className="text-gray-500 ml-2">(PEGI {game.pegi_age})</span>
      )}
    </div>
  );
}

function SourceBadge({ name, fetched, confidence }: { name: string; fetched: string; confidence: string }) {
  const date = fetched ? new Date(fetched).toLocaleDateString() : '?';
  const confColor = confidence === 'confident'
    ? 'text-green-400'
    : confidence === 'uncertain'
      ? 'text-yellow-400'
      : 'text-red-400';

  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-gray-500">
      <span className="font-medium text-gray-400">{name}</span>
      <span className={confColor}>{confidence}</span>
      <span>{date}</span>
    </span>
  );
}

export function GameDetail({ game, onClose }: Props) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="bg-gray-800 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header image */}
        <div className="relative aspect-video">
          {game.background_image ? (
            <img
              src={game.background_image}
              alt={game.name}
              className="w-full h-full object-cover rounded-t-xl"
            />
          ) : (
            <div className="w-full h-full bg-gray-900 rounded-t-xl flex items-center justify-center">
              <span className="text-6xl text-gray-700">?</span>
            </div>
          )}
          <button
            onClick={onClose}
            className="absolute top-3 right-3 p-2 rounded-full bg-black/50 text-white hover:bg-black/70 transition-colors cursor-pointer"
          >
            <FiX className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* Title row */}
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <h2 className="text-2xl font-bold text-white">{game.name}</h2>
              {game.developers?.length > 0 && (
                <p className="text-sm text-gray-400 mt-1">
                  by {game.developers.join(', ')}
                  {game.publishers?.length > 0 && game.publishers[0] !== game.developers[0] && (
                    <span className="text-gray-500"> | {game.publishers.join(', ')}</span>
                  )}
                </p>
              )}
            </div>
            <MetacriticBadge score={game.metacritic} size="lg" />
          </div>

          {/* Badges row */}
          <div className="flex items-center gap-3 flex-wrap">
            <ESRBBadge rating={game.esrb_rating} minAge={game.min_age} size="lg" />
            <SunshineBadge active={game.in_sunshine} size="lg" />
            {game.match_quality === 'uncertain' && (
              <span className="text-xs px-2 py-1 rounded-full bg-yellow-500/20 text-yellow-400">
                Match uncertain - verify in overrides
              </span>
            )}
          </div>

          {/* Age suitability */}
          <div className="p-3 rounded-lg bg-gray-900">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Age Suitability
            </div>
            <AgeSummary game={game} />
            {game.content_descriptors?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {game.content_descriptors.map((desc) => (
                  <span key={desc} className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400">
                    {desc}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Ratings from both sources */}
          <div className="grid grid-cols-2 gap-3">
            {game.rawg_rating != null && (
              <div className="p-3 rounded-lg bg-gray-900">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">RAWG</div>
                <div className="flex items-center gap-2">
                  <span className="text-yellow-400 text-lg">
                    {'★'.repeat(Math.round(game.rawg_rating))}
                    {'☆'.repeat(5 - Math.round(game.rawg_rating))}
                  </span>
                  <span className="text-gray-300">{game.rawg_rating.toFixed(2)}</span>
                </div>
                <span className="text-gray-500 text-xs">
                  {game.rawg_ratings_count.toLocaleString()} ratings
                </span>
              </div>
            )}
            {game.igdb_rating != null && (
              <div className="p-3 rounded-lg bg-gray-900">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">IGDB</div>
                <div className="flex items-center gap-2">
                  <span className="text-indigo-400 text-xl font-bold">
                    {Math.round(game.igdb_rating)}
                  </span>
                  <span className="text-gray-500 text-sm">/ 100</span>
                </div>
                <span className="text-gray-500 text-xs">
                  {game.igdb_rating_count.toLocaleString()} ratings
                  {game.aggregated_rating != null && (
                    <> | Critics: {Math.round(game.aggregated_rating)}</>
                  )}
                </span>
              </div>
            )}
          </div>

          {/* Genres */}
          {game.genres?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {game.genres.map((genre) => (
                <span
                  key={genre}
                  className="text-sm px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}

          {/* Description */}
          {game.description && (
            <p className="text-gray-300 text-sm leading-relaxed">{game.description}</p>
          )}

          {/* Meta info */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {game.released && (
              <div className="flex items-center gap-2 text-gray-400">
                <FiCalendar className="w-4 h-4" />
                <span>Released: {game.released}</span>
              </div>
            )}
            {game.platforms?.length > 0 && (
              <div className="flex items-center gap-2 text-gray-400">
                <FiMonitor className="w-4 h-4" />
                <span className="truncate">{game.platforms.join(', ')}</span>
              </div>
            )}
          </div>

          {/* File paths */}
          <div className="pt-3 border-t border-gray-700">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
              Installed Locations
            </div>
            {game.paths?.map((p) => (
              <div key={p.path} className="flex items-center gap-2 text-sm text-gray-400 mb-1">
                <FiHardDrive className="w-3 h-3 shrink-0" />
                <span className="font-mono text-xs truncate">{p.path}</span>
              </div>
            ))}
          </div>

          {/* Tags */}
          {game.tags?.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {game.tags.map((tag) => (
                <span key={tag} className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">
                  {tag}
                </span>
              ))}
            </div>
          )}

          {/* Data sources */}
          <div className="pt-3 border-t border-gray-700">
            <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
              Data Sources
            </div>
            <div className="flex flex-wrap gap-4">
              {game.sources?.rawg && (
                <SourceBadge
                  name="RAWG"
                  fetched={game.sources.rawg.fetched_at}
                  confidence={game.sources.rawg.match_confidence}
                />
              )}
              {game.sources?.igdb && (
                <SourceBadge
                  name="IGDB"
                  fetched={game.sources.igdb.fetched_at}
                  confidence={game.sources.igdb.match_confidence}
                />
              )}
              {!game.sources?.rawg && !game.sources?.igdb && (
                <span className="text-xs text-gray-600">No external data</span>
              )}
            </div>
            {game.merged_at && (
              <div className="text-xs text-gray-600 mt-1">
                Last merged: {new Date(game.merged_at).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
