'use client';

import { useQuery } from '@tanstack/react-query';
import { matchupApi } from '@/lib/api';
import { ArrowLeft, Loader2, TrendingUp, Shield, Target } from 'lucide-react';
import Link from 'next/link';
import { use } from 'react';

interface PageProps {
  params: Promise<{
    fighterA: string;
    fighterB: string;
  }>;
}

export default function PredictionPage({ params }: PageProps) {
  const { fighterA, fighterB } = use(params);
  const fighterAId = parseInt(fighterA);
  const fighterBId = parseInt(fighterB);

  // Fetch prediction with breakdown
  const { data: prediction, isLoading, error } = useQuery({
    queryKey: ['prediction', fighterAId, fighterBId],
    queryFn: () => matchupApi.getBreakdown(fighterAId, fighterBId).then(res => res.data),
    enabled: !isNaN(fighterAId) && !isNaN(fighterBId),
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600 font-medium">Generating AI prediction...</p>
          <p className="text-sm text-gray-500 mt-2">This may take a few seconds</p>
        </div>
      </div>
    );
  }

  if (error || !prediction) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h3 className="text-red-900 font-bold mb-2">Error Loading Prediction</h3>
          <p className="text-red-700 text-sm mb-4">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <Link
            href="/matchup"
            className="inline-block px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Back to Matchup Builder
          </Link>
        </div>
      </div>
    );
  }

  const { fighter_a, fighter_b } = prediction;
  const probA = prediction.fighter_a_win_probability * 100;
  const probB = prediction.fighter_b_win_probability * 100;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <Link href="/matchup" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Matchup Builder
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Fight Prediction</h1>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Cache indicator */}
        {prediction.from_cache && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-900">
            ⚡ Loaded from cache
          </div>
        )}

        {/* Main Matchup Display */}
        <div className="bg-white rounded-lg shadow-lg overflow-hidden mb-8">
          <div className="grid grid-cols-2 divide-x">
            {/* Fighter A */}
            <div className="p-8">
              <h2 className="text-2xl font-bold mb-2">{fighter_a.name}</h2>
              {fighter_a.nickname && (
                <p className="text-gray-600 italic mb-4">"{fighter_a.nickname}"</p>
              )}
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600">Record:</span>{' '}
                  <span className="font-semibold">
                    {fighter_a.wins}-{fighter_a.losses}-{fighter_a.draws}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Weight Class:</span>{' '}
                  <span className="font-semibold">{fighter_a.weight_class}</span>
                </div>
                <div>
                  <span className="text-gray-600">Reach:</span>{' '}
                  <span className="font-semibold">{fighter_a.reach_cm}cm</span>
                </div>
                <div>
                  <span className="text-gray-600">Stance:</span>{' '}
                  <span className="font-semibold">{fighter_a.stance}</span>
                </div>
              </div>
            </div>

            {/* Fighter B */}
            <div className="p-8">
              <h2 className="text-2xl font-bold mb-2">{fighter_b.name}</h2>
              {fighter_b.nickname && (
                <p className="text-gray-600 italic mb-4">"{fighter_b.nickname}"</p>
              )}
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-600">Record:</span>{' '}
                  <span className="font-semibold">
                    {fighter_b.wins}-{fighter_b.losses}-{fighter_b.draws}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Weight Class:</span>{' '}
                  <span className="font-semibold">{fighter_b.weight_class}</span>
                </div>
                <div>
                  <span className="text-gray-600">Reach:</span>{' '}
                  <span className="font-semibold">{fighter_b.reach_cm}cm</span>
                </div>
                <div>
                  <span className="text-gray-600">Stance:</span>{' '}
                  <span className="font-semibold">{fighter_b.stance}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Win Probability Bar */}
          <div className="border-t p-6">
            <div className="mb-4 text-center">
              <p className="text-sm text-gray-600 mb-2">Win Probability</p>
              <div className="flex items-center justify-center gap-2">
                <span className="text-xs text-gray-500">Confidence: </span>
                <span className={`text-xs font-semibold px-2 py-1 rounded ${
                  prediction.confidence === 'high' ? 'bg-green-100 text-green-800' :
                  prediction.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {prediction.confidence.toUpperCase()}
                </span>
              </div>
            </div>
            
            <div className="relative h-16 bg-gray-200 rounded-lg overflow-hidden">
              <div
                className="absolute left-0 top-0 h-full bg-blue-600 flex items-center justify-start px-4 transition-all"
                style={{ width: `${probA}%` }}
              >
                <span className="text-white font-bold text-lg">
                  {probA.toFixed(1)}%
                </span>
              </div>
              <div
                className="absolute right-0 top-0 h-full bg-red-600 flex items-center justify-end px-4 transition-all"
                style={{ width: `${probB}%` }}
              >
                <span className="text-white font-bold text-lg">
                  {probB.toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="mt-2 flex justify-between text-xs text-gray-600">
              <span>{fighter_a.name}</span>
              <span>{fighter_b.name}</span>
            </div>
          </div>
        </div>

        {/* Win Conditions */}
        {(prediction.fighter_a_win_condition || prediction.fighter_b_win_condition) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-blue-900">
                  {fighter_a.name}'s Path to Victory
                </h3>
              </div>
              <p className="text-blue-800">{prediction.fighter_a_win_condition}</p>
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-5 h-5 text-red-600" />
                <h3 className="font-bold text-red-900">
                  {fighter_b.name}'s Path to Victory
                </h3>
              </div>
              <p className="text-red-800">{prediction.fighter_b_win_condition}</p>
            </div>
          </div>
        )}

        {/* AI Breakdown */}
        {prediction.breakdown && (
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-6 h-6 text-purple-600" />
              <h2 className="text-2xl font-bold">AI Fight Breakdown</h2>
            </div>
            <div className="prose prose-lg max-w-none">
              <p className="text-gray-700 leading-relaxed whitespace-pre-line">
                {prediction.breakdown}
              </p>
            </div>
            <div className="mt-4 pt-4 border-t text-xs text-gray-500">
              Analysis generated by Claude AI • Model: {prediction.method}
            </div>
          </div>
        )}

        {/* Statistical Deltas */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold mb-6">Key Statistical Advantages</h2>
          
          <div className="space-y-4">
            {Object.entries(prediction.deltas).map(([key, value]) => {
              const numValue = value as number;
              const isPositive = numValue > 0;
              const absValue = Math.abs(numValue);
              
              // Format the label
              const label = key
                .replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());

              return (
                <div key={key} className="border-b pb-3 last:border-0">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">{label}</span>
                    <span className={`text-sm font-bold ${
                      isPositive ? 'text-blue-600' : 'text-red-600'
                    }`}>
                      {isPositive ? '+' : ''}{numValue.toFixed(2)}
                    </span>
                  </div>
                  <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`absolute top-0 h-full ${
                        isPositive ? 'bg-blue-600 left-1/2' : 'bg-red-600 right-1/2'
                      }`}
                      style={{ width: `${Math.min(absValue * 5, 50)}%` }}
                    />
                  </div>
                  <div className="mt-1 text-xs text-gray-500">
                    Favors: {isPositive ? fighter_a.name : fighter_b.name}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex justify-center gap-4">
          <Link
            href="/matchup"
            className="px-6 py-3 bg-gray-600 text-white rounded-lg font-semibold hover:bg-gray-700 transition"
          >
            Create New Matchup
          </Link>
        </div>
      </div>
    </div>
  );
}