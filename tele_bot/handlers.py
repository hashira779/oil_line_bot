from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from fuzzywuzzy import fuzz
from config import CONFIG, SERVICES
from data_manager import DataManager
from utils import calculate_distance
from station_info import send_station_info
import logging
import asyncio

logger = logging.getLogger(__name__)

class BotHandlers:
    def __init__(self):
        self.data_manager = DataManager(CONFIG["STATION_DATA_URL"])

    async def post_init(self, application: Application):
        """Initialize bot data after startup."""
        logger.info("🔄 Loading station data...")
        self.data_manager.stations = await self.data_manager.fetch_station_data()
        logger.info(f"✅ Loaded {len(self.data_manager.stations)} stations")

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        welcome_message = (
            "👋 **Welcome to the PTT Station Bot!**\n\n"
            "I can help you find PTT stations and their details. To provide the best experience, "
            "would you like to share your location? This will allow me to show you the nearest stations.\n\n"
            "You can also:\n"
            "- Type a station name (e.g., 'Neak Vorn') to get its details.\n"
            "- Type a service (e.g., 'ev', 'fleet', 'wing', 'amazon') to find stations offering that service.\n"
            "- Use /clear to clear recent messages in this chat."
        )
        keyboard = [[InlineKeyboardButton("📍 Allow Location Access", callback_data="allow_location")],
                    [InlineKeyboardButton("⏭️ Skip", callback_data="skip_location")]]
        await update.message.reply_text(welcome_message, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    async def clear(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /clear command to delete recent messages in the chat."""
        chat_id = update.message.chat_id
        current_message_id = update.message.message_id
        chat_type = update.message.chat.type
        max_messages_to_delete = 50  # Reduced default limit for faster performance
        batch_size = 10  # Process in batches to avoid rate limits

        try:
            if chat_type != "private":
                # Try bulk deletion for group/supergroup chats
                message_ids = list(range(current_message_id - max_messages_to_delete, current_message_id + 1))
                try:
                    await context.bot.delete_messages(chat_id=chat_id, message_ids=message_ids)
                    await update.message.reply_text(f"🧹 Cleared up to {len(message_ids)} recent messages.")
                    return
                except Exception as e:
                    logger.debug(f"Bulk deletion failed: {e}. Falling back to individual deletion.")

            # Individual deletion for private chats or fallback for groups
            deleted_count = 0
            for start_id in range(current_message_id, current_message_id - max_messages_to_delete, -batch_size):
                batch_ids = range(max(start_id - batch_size + 1, current_message_id - max_messages_to_delete), start_id + 1)
                delete_tasks = [
                    context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                    for message_id in batch_ids
                ]
                results = await asyncio.gather(*delete_tasks, return_exceptions=True)
                deleted_count += sum(1 for result in results if not isinstance(result, Exception))
                await asyncio.sleep(0.1)  # Small delay to respect rate limits

            await update.message.reply_text(
                f"🧹 Cleared {deleted_count} recent message{'s' if deleted_count != 1 else ''}."
            )
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            await update.message.reply_text(
                "⚡ Failed to clear messages. Please ensure I have permission to delete messages."
            )

    async def find_nearest_stations(self, update: Update, context: ContextTypes.DEFAULT_TYPE, service_key: str = None):
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
        for station in self.data_manager.stations:
            if service_key and service_key not in (station["service"] + station["other_product"] + station["description"]):
                continue
            station_lat = station.get("latitude")
            station_lon = station.get("longitude")
            if station_lat and station_lon:
                distance = calculate_distance(user_lat, user_lon, station_lat, station_lon)
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
        matches = [s for s in self.data_manager.stations if fuzz.partial_ratio(user_input, s.get("title", "").lower()) > 80]

        if not matches:
            await update.message.reply_text("🚫 No matching stations found.")
            return

        if len(matches) == 1:
            await send_station_info(update.message, matches[0])
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
            station = next((s for s in self.data_manager.stations if s.get("id") == station_id), None)
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
            await send_station_info(query, station)
            return
        raise ValueError("Invalid callback data")

    async def handle_share_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location sharing callbacks."""
        query = update.callback_query
        await query.answer()

        if query.data.startswith("share_"):
            _, station_id, latitude, longitude = query.data.split("_")
            map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
            station = next((s for s in self.data_manager.stations if s.get("id") == station_id), None)
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

    def setup_handlers(self, application: Application):
        """Set up bot command and message handlers."""
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("clear", self.clear))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(MessageHandler(filters.LOCATION, self.handle_location))
        application.add_handler(CallbackQueryHandler(self.button_callback, pattern=r"^(station_|location|allow_location|skip_location)"))
        application.add_handler(CallbackQueryHandler(self.handle_share_location, pattern=r"^share_"))
        application.add_handler(CallbackQueryHandler(self.debug_callback))
        application.add_error_handler(self.error_handler)
        logger.info("Handlers registered successfully")