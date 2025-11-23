'use client';

import { useState, useEffect } from 'react';
import { useRoomContext } from '@livekit/components-react';
import { DataPacket_Kind, RemoteParticipant } from 'livekit-client';

interface OrderState {
  drinkType: string;
  size: string;
  milk: string;
  extras: string[];
  name: string;
}

export function OrderSummary() {
  const [orderState, setOrderState] = useState<OrderState>({
    drinkType: '',
    size: '',
    milk: '',
    extras: [],
    name: ''
  });

  const room = useRoomContext();

  useEffect(() => {
    const handleDataReceived = (payload: Uint8Array, participant?: RemoteParticipant, kind?: DataPacket_Kind) => {
      try {
        const message = JSON.parse(new TextDecoder().decode(payload));
        if (message.type === 'order_state') {
          setOrderState(message.data);
        }
      } catch (error) {
        console.error('Failed to parse order message:', error);
      }
    };

    room.on('dataReceived', handleDataReceived);
    return () => room.off('dataReceived', handleDataReceived);
  }, [room]);

  return (
    <div className="fixed top-4 right-4 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-4 z-40">
      <h3 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">Order Summary</h3>
      
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Drink:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {orderState.drinkType || '-'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Size:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {orderState.size || '-'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Milk:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {orderState.milk || '-'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Extras:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {orderState.extras.length > 0 ? orderState.extras.join(', ') : '-'}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span className="text-gray-600 dark:text-gray-400">Name:</span>
          <span className="font-medium text-gray-900 dark:text-white">
            {orderState.name || '-'}
          </span>
        </div>
      </div>
    </div>
  );
}