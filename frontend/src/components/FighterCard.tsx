'use client';

import { Fighter } from '@/lib/api';
import { User } from 'lucide-react';

interface FighterCardProps {
  fighter: Fighter;
  onClick?: () => void;
  selected?: boolean;
}

export function FighterCard({ fighter, onClick, selected }: FighterCardProps) {
  const record = `${fighter.wins}-${fighter.losses}${fighter.draws > 0 ? `-${fighter.draws}` : ''}`;
  
  return (
    <div
      onClick={onClick}
      className={`
        p-4 rounded-lg border-2 cursor-pointer transition-all
        hover:shadow-lg hover:scale-105
        ${selected 
          ? 'border-blue-500 bg-blue-50' 
          : 'border-gray-200 bg-white hover:border-gray-300'
        }
      `}
    >
      <div className="flex items-start gap-3">
        <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
          <User className="w-6 h-6 text-gray-500" />
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="font-bold text-lg truncate">{fighter.name}</h3>
          {fighter.nickname && (
            <p className="text-sm text-gray-500 italic">"{fighter.nickname}"</p>
          )}
          <div className="mt-2 flex items-center gap-3 text-sm">
            <span className="font-semibold text-gray-700">{record}</span>
            <span className="text-gray-500">{fighter.weight_class}</span>
          </div>
          
          {fighter.stats && (
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-gray-500">Striking:</span>{' '}
                <span className="font-medium">
                  {fighter.stats.sig_strikes_landed_per_min.toFixed(1)} SL/min
                </span>
              </div>
              <div>
                <span className="text-gray-500">TD Def:</span>{' '}
                <span className="font-medium">
                  {fighter.stats.takedown_defense.toFixed(0)}%
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}