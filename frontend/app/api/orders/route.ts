import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    const ordersDir = path.join(process.cwd(), '..', 'backend', 'orders');
    
    if (!fs.existsSync(ordersDir)) {
      return NextResponse.json([]);
    }

    const files = fs.readdirSync(ordersDir).filter(file => file.endsWith('.json'));
    const orders = files.map(file => {
      const filePath = path.join(ordersDir, file);
      const content = fs.readFileSync(filePath, 'utf-8');
      return JSON.parse(content);
    });

    return NextResponse.json(orders);
  } catch (error) {
    return NextResponse.json([]);
  }
}