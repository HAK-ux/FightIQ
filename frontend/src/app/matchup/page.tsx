'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fightersApi, matchupApi, Fighter } from '@/lib/api';
import { FighterCard } from '@/components/FighterCard';
import { Search, Swords, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function MatchupPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFighterA, setSelectedFighterA] = useState<Fighter | null>(null);
  const [selectedFighterB, setSelectedFighterB] = useState<Fighter | null>(null);
  const [selectedWeightClass, setSelectedWeightClass] = useState<string>('');

  // Fetch fighters
  const { data: fighters, isLoading } = useQuery({
    queryKey: ['fighters', selectedWeightClass],
    queryFn: () => fightersApi.getAll({ 
      weight_class: selectedWeightClass || undefined,
      limit: 50 
    }).then(res => res.data),
  });

  // Fetch weight classes
  const { data: weightClasses } = useQuery({
    queryKey: ['weightClasses'],
    queryFn: () => fightersApi.getWeightClasses().then(res => res.data),
  });

  // Filter fighters by search
  const filteredFighters = fighters?.filter(f =>
    f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    f.nickname?.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  const canGeneratePrediction = selectedFighterA && selectedFighterB;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <Link href="/" className="text-2xl font-bold text-gray-900">
            FightIQ
          </Link>
          <p className="text-gray-600 mt-1">Build your matchup and get AI-powered predictions</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Selection Summary */}
        {canGeneratePrediction && (
          <div className="mb-8 p-6 bg-white rounded-lg shadow-sm border-2 border-blue-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <p className="text-sm text-gray-500">Fighter A</p>
                  <p className="font-bold text-lg">{selectedFighterA.name}</p>
                </div>
                <Swords className="w-8 h-8 text-gray-400" />
                <div className="text-center">
                  <p className="text-sm text-gray-500">Fighter B</p>
                  <p className="font-bold text-lg">{selectedFighterB.name}</p>
                </div>
              </div>
              
              <Link
                href={`/prediction/${selectedFighterA.id}/${selectedFighterB.id}`}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition flex items-center gap-2"
              >
                Generate Prediction
                <ArrowRight className="w-5 h-5" />
              </Link>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="mb-6 flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search fighters..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <select
            value={selectedWeightClass}
            onChange={(e) => setSelectedWeightClass(e.target.value)}
            className="px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">All Weight Classes</option>
            {weightClasses?.map(wc => (
              <option key={wc} value={wc}>{wc}</option>
            ))}
          </select>
        </div>

        {/* Instructions */}
        {!selectedFighterA && (
          <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-900 font-medium">👈 Select Fighter A</p>
          </div>
        )}
        {selectedFighterA && !selectedFighterB && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-900 font-medium">👈 Now select Fighter B</p>
          </div>
        )}

        {/* Fighter Grid */}
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">Loading fighters...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFighters.map(fighter => (
              <FighterCard
                key={fighter.id}
                fighter={fighter}
                selected={
                  fighter.id === selectedFighterA?.id ||
                  fighter.id === selectedFighterB?.id
                }
                onClick={() => {
                  if (!selectedFighterA) {
                    setSelectedFighterA(fighter);
                  } else if (!selectedFighterB && fighter.id !== selectedFighterA.id) {
                    setSelectedFighterB(fighter);
                  } else if (fighter.id === selectedFighterA.id) {
                    setSelectedFighterA(null);
                  } else if (fighter.id === selectedFighterB?.id) {
                    setSelectedFighterB(null);
                  }
                }}
              />
            ))}
          </div>
        )}

        {filteredFighters.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <p className="text-gray-500">No fighters found</p>
          </div>
        )}
      </div>
    </div>
  );
}