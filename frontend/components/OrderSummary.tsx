'use client';

import { useState, useEffect } from 'react';

interface Order {
  drinkType: string;
  size: string;
  milk: string;
  extras: string[];
  name: string;
}

export function OrderSummary() {
  const [order, setOrder] = useState<Order | null>(null);

  const fetchOrders = () => {
    fetch('/api/orders')
      .then(res => res.json())
      .then(orders => {
        if (orders.length > 0) {
          setOrder(orders[orders.length - 1]);
        }
      });
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 2000);
    
    const handleMessage = (event: MessageEvent) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'final_order') {
          setOrder(message.data);
        }
      } catch (error) {
        console.error('Failed to parse message:', error);
      }
    };
    
    window.addEventListener('message', handleMessage);
    return () => {
      clearInterval(interval);
      window.removeEventListener('message', handleMessage);
    };
  }, []);

  if (!order) return null;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border p-4 max-w-sm">
      <h3 className="text-lg font-semibold mb-3">Latest Order</h3>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-600">Drink:</span>
          <span className="font-medium">{order.drinkType}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Size:</span>
          <span className="font-medium">{order.size}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Milk:</span>
          <span className="font-medium">{order.milk}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Extras:</span>
          <span className="font-medium">{order.extras.join(', ') || 'None'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">Name:</span>
          <span className="font-medium">{order.name}</span>
        </div>
      </div>
    </div>
  );
}