import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import fs from 'fs';

// Get the directory name of the current module
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Try to find .env file in the project root
const envPath = join(__dirname, '..', '.env');
if (fs.existsSync(envPath)) {
  dotenv.config({ path: envPath });
} else {
  dotenv.config();
}

export interface Config {
  coinbaseCommerceApiKey: string;
  serverName: string;
  serverVersion: string;
}

export const config: Config = {
  coinbaseCommerceApiKey: process.env.COINBASE_COMMERCE_API_KEY || '',
  serverName: 'coinbase-commerce',
  serverVersion: '0.1.0',
};
