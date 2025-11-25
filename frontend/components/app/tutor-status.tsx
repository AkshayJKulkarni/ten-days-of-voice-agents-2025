'use client';

import { useState, useEffect } from 'react';
import { useRoomContext } from '@livekit/components-react';
import { DataPacket_Kind, RemoteParticipant } from 'livekit-client';

interface TutorState {
  mode: string;
  concept: string;
}

export function TutorStatus() {
  const [tutorState, setTutorState] = useState<TutorState>({ mode: '', concept: '' });
  const room = useRoomContext();

  useEffect(() => {
    const handleDataReceived = (payload: Uint8Array, participant?: RemoteParticipant, kind?: DataPacket_Kind) => {
      try {
        const message = JSON.parse(new TextDecoder().decode(payload));
        if (message.type === 'tutor_state') {
          setTutorState(message.data);
        }
      } catch (error) {
        console.error('Failed to parse tutor state:', error);
      }
    };

    room.on('dataReceived', handleDataReceived);
    return () => room.off('dataReceived', handleDataReceived);
  }, [room]);

  if (!tutorState.mode && !tutorState.concept) return null;

  return (
    <div className="fixed top-4 left-4 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-3 z-40">
      <h3 className="text-sm font-semibold mb-2 text-gray-900 dark:text-white">Learning Status</h3>
      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Mode:</span>
          <span className="font-medium text-gray-900 dark:text-white capitalize">
            {tutorState.mode || 'Not selected'}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Concept:</span>
          <span className="font-medium text-gray-900 dark:text-white capitalize">
            {tutorState.concept || 'Not selected'}
          </span>
        </div>
      </div>
    </div>
  );
}