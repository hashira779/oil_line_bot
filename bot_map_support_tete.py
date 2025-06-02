import asyncio
import logging
from datetime import datetime, time
import haversine as hs
import requests
from fuzzywuzzy import fuzz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Configuration
CONFIG = {
    "BOT_TOKEN": "7305046364:AAGHE_yJ84H63C_eBHGw_YKK1JVLmE8XTgo",
    "STATION_DATA_URL": "https://raw.githubusercontent.com/Ratana-tep/PTT_STATION_MAP/master/data/markers.json",
    "DEFAULT_OPEN_TIME": time(5, 0),  # 5:00 AM
    "DEFAULT_CLOSE_TIME": time(20, 30),  # 8:30 PM
}

# Service configuration with multiple command aliases
SERVICES = {
    "Amazon": {"name": "Amazon Coffee", "icon": "☕", "commands": ["amazon"]},
    "7-Eleven": {"name": "7-Eleven Store", "icon": "🏪", "commands": ["7eleven", "7-eleven", "7eleven" ]},
    "Otr": {"name": "Otteri Store", "icon": "👕", "commands": ["otr"]},
    "Fleet card": {"name": "Fleet Card Accepted", "icon": "💳", "commands": ["fleet", "fleet card", "wing"]},
    "KHQR": {"name": "KHQR Payment", "icon": "📍", "commands": ["khqr"]},
    "Cash": {"name": "Cash Payment", "icon": "💸", "commands": ["cash"]},
    "EV": {"name": "EV Charging Station", "icon": "⚡", "commands": ["ev"]}
}

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.stations = []
        self.application = None

    async def fetch_station_data(self):
        """Fetch station data from the configured URL."""
        try:
            response = await asyncio.to_thread(requests.get, CONFIG["STATION_DATA_URL"], timeout=10)
            response.raise_for_status()
            data = response.json()
            self.stations = data.get("STATION", [])
            for station in self.stations:
                station["id"] = str(station.get("id", ""))
                station["latitude"] = str(station.get("latitude", ""))
                station["longitude"] = str(station.get("longitude", ""))
                station["service"] = station.get("service", []) or []
                station["other_product"] = station.get("other_product", []) or []
                station["description"] = station.get("description", []) or []
            logger.info(f"Successfully loaded {len(self.stations)} stations.")
            return self.stations
        except Exception as e:
            logger.error(f"Error fetching station data: {e}")
            return []

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula."""
        try:
            coord1 = (float(lat1), float(lon1))
            coord2 = (float(lat2), float(lon2))
            return hs.haversine(coord1, coord2, unit=hs.Unit.KILOMETERS)
        except (ValueError, Exception) as e:
            logger.error(f"Error calculating distance: {e}")
            return float('inf')

    async def find_nearest_stations(self, update: Update, context: ContextTypes.DEFAULT_TYPE,
                                    service_key: str = None):
        """Find nearest stations, optionally filtered by service or product."""
        user_location = context.user_data.get('location')
        if not user_location:
            service_info = SERVICES.get(service_key, {"name": "stations", "icon": "📍"}) if service_key else {"name": "stations", "icon": "📍"}
            await update.message.reply_text(
                f"{service_info['icon']} Please share your location to find the nearest {service_info['name'].lower()}.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📍 Share Location", callback_data="location")]])
            )
            return

        user_lat, user_lon = user_location
        stations_with_distance = []
        for station in self.stations:
            if service_key and service_key not in (station["service"] + station["other_product"]+ station["description"] ):
                continue
            station_lat = station.get("latitude")
            station_lon = station.get("longitude")
            if station_lat and station_lon:
                distance = self.calculate_distance(user_lat, user_lon, station_lat, station_lon)
                time_minutes = int((distance / 5) * 60) if distance > 0 else 0
                stations_with_distance.append((station, distance, time_minutes))

        stations_with_distance.sort(key=lambda x: x[1])
        nearest_stations = stations_with_distance[:10]

        if not nearest_stations:
            service_name = SERVICES.get(service_key, {"name": "stations"})["name"] if service_key else "stations"
            await update.message.reply_text(f"🚫 No {service_name.lower()} found with valid coordinates.")
            return

        keyboard = [[InlineKeyboardButton(
            f"{station['title']} ({distance:.2f} km, ~{time} min)",
            callback_data=f"station_{station['id']}"
        )] for station, distance, time in nearest_stations if station.get("id") and station.get("title")]

        service_info = SERVICES.get(service_key, {"name": "stations", "icon": "📍"}) if service_key else {"name": "stations", "icon": "📍"}
        await update.message.reply_text(
            f"{service_info['icon']} Found {len(nearest_stations)} {service_info['name'].lower()} near your location. Please select one:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user-shared location."""
        user_location = update.message.location
        if not user_location:
            await update.message.reply_text("🚫 No location data received. Please share your location again.")
            logger.warning("No location data in message")
            return

        user_lat, user_lon = user_location.latitude, user_location.longitude
        context.user_data['location'] = (user_lat, user_lon)
        logger.info(f"User location: ({user_lat}, {user_lon})")
        await self.find_nearest_stations(update, context)

    async def send_station_info(self, message, station):
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

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming text messages from users."""
        user_input = update.message.text.strip().lower()
        if not user_input:
            await update.message.reply_text("🚫 Please enter a station name or service to search.")
            return

        # Check for service commands
        for service_key, service_info in SERVICES.items():
            if user_input in service_info["commands"]:
                await self.find_nearest_stations(update, context, service_key=service_key)
                return

        # Search for stations by name
        matches = [s for s in self.stations if fuzz.partial_ratio(user_input, s.get("title", "").lower()) > 80]

        if not matches:
            await update.message.reply_text("🚫 No matching stations found.")
            return

        if len(matches) == 1:
            await self.send_station_info(update.message, matches[0])
            return

        keyboard = [[InlineKeyboardButton(s["title"], callback_data=f"station_{s['id']}")] for s in matches if s.get("id") and s.get("title")]
        await update.message.reply_text("🔍 Multiple stations found. Please select one:", reply_markup=InlineKeyboardMarkup(keyboard))

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks."""
        query = update.callback_query
        await query.answer()

        if query.data == "allow_location" or query.data == "location":
            location_keyboard = ReplyKeyboardMarkup([[KeyboardButton("📍 Send My Location", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)
            await query.message.reply_text("📍 Click the button below to share your location.", parse_mode="Markdown", reply_markup=location_keyboard)
            return
        elif query.data == "skip_location":
            await query.edit_message_text("⏭️ Location access skipped. You can search for a station by typing its name or a service (e.g., 'ev', 'fleet', 'wing', 'amazon').", parse_mode="Markdown")
            return
        elif query.data.startswith("station_"):
            station_id = query.data.split("_", 1)[1]
            station = next((s for s in self.stations if s.get("id") == station_id), None)
            if not station:
                await query.edit_message_text("❌ Station not found.", parse_mode="Markdown")
                return
            if not all([station.get(k) for k in ["latitude", "longitude", "title"]]):
                station = {
                    "id": "601",
                    "latitude": "11.5704444444444",
                    "longitude": "104.905083333333",
                    "title": "PTT Station Neak Vorn",
                    "address": "Russian Federation Blvd (St.110), Sangkat Srah Chak, Khan Doun Penh, Cambodia",
                    "province": "Phnom Penh",
                    "status": "24h",
                    "description": ["Amazon", "7-Eleven", "Otr"],
                    "product": ["ULG 95", "ULR 91", "HSD"],
                    "other_product": ["EV"],
                    "service": ["Fleet card", "KHQR", "Cash"],
                    "promotion": []
                }
            await self.send_station_info(query, station)
            return
        raise ValueError("Invalid callback data")

    async def handle_share_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location sharing callbacks."""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("share_"):
            _, station_id, latitude, longitude = query.data.split("_")
            map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
            station = next((s for s in self.stations if s.get("id") == station_id), None)
            if not station:
                await query.message.reply_text("🚫 Station not found. Please try again.")
                return

            message_lines = [
                "📍 **SHARE STATION LOCATION**",
                "══════════════════════",
                f"⛽ **{station.get('title', 'Unknown Station').upper()}**",
                f"🌐 **Location Link:** {map_link}",
                "══════════════════════",
                "🏁 **Location sharing complete. Search for another station?**"
            ]
            await query.message.reply_text("\n".join(message_lines), parse_mode="Markdown", disable_web_page_preview=True)
            return
        await query.message.reply_text("⚡ Invalid share request")

    async def debug_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Fallback callback for unhandled callbacks."""
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("⚡ **Debug**: Callback received but not processed. Check logs.")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors during update processing."""
        logger.error(f"Update {update} caused error {context.error}", exc_info=True)
        if update and hasattr(update, 'message') and update.message:
            await update.message.reply_text("⚡ An error occurred. Please try again later.")

    async def post_init(self, application: Application):
        """Initialize bot data after startup."""
        logger.info("🔄 Loading station data...")
        self.stations = await self.fetch_station_data()
        logger.info(f"✅ Loaded {len(self.stations)} stations")

    def setup_handlers(self):
        """Set up bot command and message handlers."""
        self.application = Application.builder().token(CONFIG["BOT_TOKEN"]).post_init(self.post_init).build()
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.application.add_handler(MessageHandler(filters.LOCATION, self.handle_location))
        self.application.add_handler(CallbackQueryHandler(self.button_callback, pattern=r"^(station_|location|allow_location|skip_location)"))
        self.application.add_handler(CallbackQueryHandler(self.handle_share_location, pattern=r"^share_"))
        self.application.add_handler(CallbackQueryHandler(self.debug_callback))
        self.application.add_error_handler(self.error_handler)
        logger.info("Handlers registered successfully")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        welcome_message = (
            "👋 **Welcome to the PTT Station Bot!**\n\n"
            "I can help you find PTT stations and their details. To provide the best experience, "
            "would you like to share your location? This will allow me to show you the nearest stations.\n\n"
            "You can also:\n"
            "- Type a station name (e.g., 'Neak Vorn') to get its details.\n"
            "- Type a service (e.g., 'ev', 'fleet', 'wing', 'amazon') to find stations offering that service."
        )
        keyboard = [[InlineKeyboardButton("📍 Allow Location Access", callback_data="allow_location")],
                    [InlineKeyboardButton("⏭️ Skip", callback_data="skip_location")]]
        await update.message.reply_text(welcome_message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    def run(self):
        """Start the bot."""
        self.setup_handlers()
        logger.info("🚀 Bot is running...")
        self.application.run_polling(drop_pending_updates=True, timeout=30, allowed_updates=["message", "callback_query", "location"])

if __name__ == "__main__":
    bot = BotManager()
    asyncio.run(bot.run())