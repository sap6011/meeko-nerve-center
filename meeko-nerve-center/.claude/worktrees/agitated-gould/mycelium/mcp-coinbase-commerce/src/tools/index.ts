import { z } from 'zod';
import coinbaseApi from '../api/coinbase.js';

/**
 * Create Charge Tool
 * 
 * Generates a payment link via Coinbase Commerce
 */
export const createChargeSchema = {
  name: z.string().min(1).max(100).describe('Name of the payment (e.g., "Coffee Donation")'),
  description: z.string().min(1).max(200).describe('Description of what the payment is for'),
  amount: z.string().min(1).describe('Payment amount (e.g., "10.00")'),
  currency: z.string().length(3).default('USD').describe('Currency code (e.g., "USD", "EUR", "BTC")'),
  redirectUrl: z.string().url().optional().describe('URL to redirect after payment completes'),
};

export async function createCharge(params: z.infer<typeof createChargeSchema>) {
  try {
    const charge = await coinbaseApi.createCharge({
      name: params.name,
      description: params.description,
      pricingType: 'fixed_price',
      localPrice: {
        amount: params.amount,
        currency: params.currency,
      },
      redirectUrl: params.redirectUrl,
    });

    return {
      content: [
        {
          type: 'text',
          text: `Successfully created a payment link:
          
Payment Name: ${charge.name}
Description: ${charge.description}
Amount: ${charge.pricing.local.amount} ${charge.pricing.local.currency}
Payment Link: ${charge.hosted_url}
Charge ID: ${charge.id}
Created At: ${new Date(charge.created_at).toLocaleString()}
Expires At: ${new Date(charge.expires_at).toLocaleString()}

The payment link can be shared with customers to collect cryptocurrency payments.`
        }
      ]
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error creating payment link: ${error instanceof Error ? error.message : String(error)}`
        }
      ],
      isError: true
    };
  }
}

/**
 * Get Charge Tool
 * 
 * Retrieves details of an existing charge (payment)
 */
export const getChargeSchema = {
  chargeId: z.string().min(1).describe('ID of the charge to retrieve'),
};

export async function getCharge(params: z.infer<typeof getChargeSchema>) {
  try {
    const charge = await coinbaseApi.getCharge(params.chargeId);
    
    // Determine payment status from timeline
    const currentStatus = charge.timeline.length > 0 
      ? charge.timeline[charge.timeline.length - 1].status 
      : 'NEW';
    
    const paymentCount = charge.payments.length;
    
    return {
      content: [
        {
          type: 'text',
          text: `Charge Details:
          
Payment Name: ${charge.name}
Description: ${charge.description}
Amount: ${charge.pricing.local.amount} ${charge.pricing.local.currency}
Payment Link: ${charge.hosted_url}
Charge ID: ${charge.id}
Status: ${currentStatus}
Payments Received: ${paymentCount}
Created At: ${new Date(charge.created_at).toLocaleString()}
Expires At: ${new Date(charge.expires_at).toLocaleString()}

${paymentCount > 0 ? 'Payment information is available for this charge.' : 'No payments have been received for this charge yet.'}`
        }
      ]
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error retrieving charge: ${error instanceof Error ? error.message : String(error)}`
        }
      ],
      isError: true
    };
  }
}