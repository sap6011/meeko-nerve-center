import axios from 'axios';
import { config } from '../config.js';

interface LocalPrice {
  amount: string;
  currency: string;
}

interface ChargeOptions {
  name: string;
  description: string;
  pricingType: 'fixed_price' | 'no_price';
  localPrice: LocalPrice;
  redirectUrl?: string;
  cancelUrl?: string;
}

interface Charge {
  id: string;
  name: string;
  description: string;
  hosted_url: string;
  created_at: string;
  expires_at: string;
  pricing: {
    local: LocalPrice;
    bitcoin?: { amount: string; currency: string };
    ethereum?: { amount: string; currency: string };
    usdc?: { amount: string; currency: string };
  };
  payments: Array<any>;
  timeline: Array<{
    time: string;
    status: string;
  }>;
}

/**
 * Coinbase Commerce API client
 */
export class CoinbaseCommerceApi {
  private apiKey: string;
  private baseUrl: string = 'https://api.commerce.coinbase.com';

  constructor() {
    this.apiKey = config.coinbaseCommerceApiKey;
    if (!this.apiKey) {
      throw new Error('COINBASE_COMMERCE_API_KEY is not defined in environment variables');
    }
  }

  /**
   * Create a new charge (payment link)
   */
  async createCharge(options: ChargeOptions): Promise<Charge> {
    try {
      const response = await axios.post(
        `${this.baseUrl}/charges`,
        {
          name: options.name,
          description: options.description,
          pricing_type: options.pricingType,
          local_price: options.localPrice,
          redirect_url: options.redirectUrl,
          cancel_url: options.cancelUrl,
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'X-CC-Api-Key': this.apiKey,
            'X-CC-Version': '2018-03-22',
          },
        }
      );

      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Coinbase Commerce API Error: ${error.response.status} - ${error.response.data.error.message}`);
      }
      throw new Error(`Error creating charge: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Get details of an existing charge
   */
  async getCharge(chargeId: string): Promise<Charge> {
    try {
      const response = await axios.get(`${this.baseUrl}/charges/${chargeId}`, {
        headers: {
          'X-CC-Api-Key': this.apiKey,
          'X-CC-Version': '2018-03-22',
        },
      });

      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        throw new Error(`Coinbase Commerce API Error: ${error.response.status} - ${error.response.data.error.message}`);
      }
      throw new Error(`Error fetching charge: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}

export default new CoinbaseCommerceApi();