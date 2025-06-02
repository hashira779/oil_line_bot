from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import CONFIG, SERVICES
import logging

logger = logging.getLogger(__name__)

async def send_station_info(message, station):
    """Send detailed information about a specific station."""
    latitude = float(station.get("latitude", "0")) if station.get("latitude") != "0" else None
    longitude = float(station.get("longitude", "0")) if station.get("longitude") != "0" else None
    title, address, province = station.get("title", "Unknown Station"), station.get("address", ""), station.get("province", "")
    status, description, products = station.get("status", "").lower(), station.get("description", []), station.get("product", [])
    other_products, services, promotions = station.get("other_product", []), station.get("service", []), station.get("promotion", [])

    current_time = datetime.now().time()
    status_text = "Open (24/7)" if status == "24h" else (
                                                            "Open" if CONFIG["DEFAULT_OPEN_TIME"] <= current_time <= CONFIG["DEFAULT_CLOSE_TIME"] else "Closed"
                                                        ) + (" (5:00 AM - 8:30 PM)" if status != "24h" else "")
    status_emoji = "🟢" if (status == "24h" or CONFIG["DEFAULT_OPEN_TIME"] <= current_time <= CONFIG["DEFAULT_CLOSE_TIME"]) else "🔴"

    map_link = f"https://www.google.com/maps?q={latitude},{longitude}" if latitude and longitude else None
    direction_link = f"https://www.google.com/maps/dir/?api=1&destination={latitude},{longitude}" if latitude and longitude else None

    lines = [f"⛽ **{title.upper()}**", "══════════════════", f"{status_emoji} **Status:** {status_text}\n",
             "📍 **LOCATION**"]
    if address: lines.append(f"🗺️ _{address}_")
    if province: lines.append(f"🏙️ {province}")
    lines.append("")

    if products or other_products:
        lines.append("⛽ **FUEL PRODUCTS**")
        lines.append("• " + "\n• ".join([f"{p.upper()}" for p in products]) if products else "• (None)")
        lines.append("\n🔧 **OTHER PRODUCTS**")
        lines.append("• " + "\n• ".join([f"{p.upper()}" for p in other_products]) if other_products else "• (None)")
        lines.append("")

    if description:
        lines.append("🏬 **AMENITIES & SERVICES**")
        lines.extend([f"{SERVICES.get(svc.strip(), {'icon': '✨', 'name': svc.capitalize()})['icon']} {SERVICES.get(svc.strip(), {'icon': '✨', 'name': svc.capitalize()})['name']}" for svc in description])
        lines.append("")

    if services:
        lines.append("💳 **PAYMENT METHODS**")
        lines.append("  ".join([f"{SERVICES.get(svc.strip(), {'icon': '💲', 'name': svc.capitalize()})['icon']} {SERVICES.get(svc.strip(), {'icon': '💲', 'name': svc.capitalize()})['name']}" for svc in services]))
        lines.append("")

    if promotions:
        lines.append("🎉 **CURRENT PROMOTIONS**")
        lines.append("• " + "\n• ".join(promotions))
        lines.append("")

    lines.extend(["══════════════════", "🧭 **NAVIGATION**", "\n🏁 **End of station details. Search for another station?**"])

    text = "\n".join(lines)
    keyboard = []
    if map_link and direction_link:
        keyboard.append([InlineKeyboardButton("🗺️ View on Map", url=map_link), InlineKeyboardButton("🚗 Get Directions", url=direction_link)])
        if latitude and longitude:
            keyboard.append([InlineKeyboardButton("🌐 Share Location", callback_data=f"share_{station['id']}_{latitude}_{longitude}")])
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    try:
        if hasattr(message, 'edit_message_text'):
            await message.edit_message_text(text=text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)
        else:
            sent_message = await message.reply_text(text=text, parse_mode="Markdown", disable_web_page_preview=True, reply_markup=reply_markup)
            try:
                await sent_message.pin(disable_notification=True)
            except Exception as e:
                logger.warning(f"Failed to pin message for {title}: {e}")
                await sent_message.reply_text("📌 This message couldn't be pinned. Use the buttons above to navigate.")
    except Exception as e:
        logger.error(f"Error sending station info for {title}: {e}")
        raise