import crypto from 'crypto';
import type { DeliveryStatus } from './types';
const store = new Map<string, DeliveryStatus>();
export const buildDedupeKey = (id: string) => crypto.createHash('sha256').update(`github-delivery:${id}`).digest('hex');
export function claimDelivery(key: string): boolean { if (store.has(key)) return false; store.set(key, 'pending'); return true; }
export const finaliseDelivery = (key: string, s: DeliveryStatus) => store.set(key, s);
export const getDeliveryStatus = (key: string) => store.get(key);
