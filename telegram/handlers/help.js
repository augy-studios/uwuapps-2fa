import { TOKEN_EXPIRY_SECONDS } from '../config.js';

export async function helpHandler(ctx) {
  const expiryMinutes = TOKEN_EXPIRY_SECONDS / 60;
  await ctx.reply(
    '🤖 UwU Apps 2FA Bot — Help\n\n' +
    '📌 Commands:\n' +
    '  /start — Process a login request (usually opened automatically)\n' +
    '  /login — Get a one-time login code to enter in a UwU App\n' +
    '  /link — Link your Telegram to your UwU Apps account\n' +
    '  /unlink — Remove the link between Telegram and UwU Apps\n' +
    '  /status — Check which UwU Apps account is linked\n' +
    '  /help — Show this help message\n\n' +
    '🔑 Login Methods:\n\n' +
    '  Method 1 — Deep Link:\n' +
    '  Click "Login with Telegram" in a UwU App. It opens this bot automatically with a login token. Your login is approved here.\n\n' +
    `  Method 2 — OTP Code:\n` +
    `  Send /login to get a ${expiryMinutes}-minute one-time code. Enter it in the UwU App login form.\n\n` +
    '❓ Need help? Contact @uwuapps or visit uwuapps.com/support'
  );
}
