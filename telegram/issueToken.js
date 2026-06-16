import 'dotenv/config';
import { randomBytes } from 'crypto';
import { insertToken } from './db.js';
import { TOKEN_EXPIRY_SECONDS } from './config.js';

const [,, uwuUserId, appId = 'uwuapps', appLabel = 'UwU Apps'] = process.argv;

if (!uwuUserId) {
  console.error('Usage: node issueToken.js <uwu_user_id> [app_id] [app_label]');
  process.exit(1);
}

const token = randomBytes(32).toString('base64url');
await insertToken({ token, uwuUserId, appId, appLabel, expirySeconds: TOKEN_EXPIRY_SECONDS });

console.log('Token:    ', token);
console.log('Deep link:', `https://t.me/uwuapps_2fa_bot?start=${token}`);
