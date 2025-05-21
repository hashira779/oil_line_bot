from telethon import TelegramClient, events
import winsound
import re
import logging
from gtts import gTTS
import pygame
import os
import platform
from datetime import datetime
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Telegram credentials
api_id = 11648963
api_hash = "28499669ea483648c8a3d139b3bf2071"
phone = "+855765546904"
group_chat_id = -1002578357362

client = TelegramClient('session_name', api_id, api_hash)

# Initialize pygame for gTTS audio
pygame.mixer.init()

# Bank name mappings (English to Khmer)
bank_name_mappings = {
    'ABA': 'ធនាគារ អេប៊ីអេ',
    'ACLEDA': 'ធនាគារ អេស៊ីលីដា',
    'ARDB': 'ធនាគារ អភិវឌ្ឍន៍ជនបទ',
    'APD': 'ធនាគារ អេភីឌី',
    'AMK': 'អេអឹមខេ មីក្រូហិរញ្ញវត្ថុ ភីអិលស៊ី',
    'Amret': 'អាម្រ៉េត ភីអិលស៊ី',
    'Asia Wei Luy': 'អាស៊ី វ៉ីលុយ',
    'Bank of China': 'ធនាគារ ចិន (សាខាភ្នំពេញ)',
    'BIDC': 'ធនាគារ ប៊ីអាយឌីស៊ី',
    'BongLoy': 'បង់លុយ',
    'BRED': 'ធនាគារ ប្រេដ',
    'Cambodia Asia': 'ធនាគារ កម្ពុជា អាស៊ី',
    'CPBank': 'ធនាគារ ប្រៃសណីយ៍កម្ពុជា',
    'Campu Bank': 'ធនាគារ Public Bank',
    'Canadia': 'ធនាគារ កាណាឌីយ៉ា',
    'Cathay United': 'ធនាគារ Cathay United Bank',
    'CCU': 'ធនាគារ CCU',
    'Chief': 'ធនាគារ Chief',
    'Chip Mong': 'ធនាគារ ជីប ម៉ុង',
    'CIMB': 'ធនាគារ CIMB',
    'Cool Cash': 'គូល ខែស',
    'DGB': 'ធនាគារ DGB',
    'eMoney': 'អ៊ីម៉ានី',
    'First Commercial': 'ធនាគារ First Commercial',
    'FTB': 'ធនាគារ ទំនាក់ទំនងរវាងប្រទេស',
    'Hattha': 'ធនាគារ ហត្ថា',
    'Heng Feng': 'ធនាគារ ហេងហ្វឹង',
    'Hong Leong': 'ធនាគារ ហុងលៀង',
    'ICBC': 'ធនាគារ ICBC',
    'J Trust Royal': 'ធនាគារ ជេ ត្រាស់ រ៉ូយ៉ាល់',
    'KB Prasac': 'ធនាគារ កេប៊ី ប្រាសាក់',
    'Kess': 'ខេសស៊ី (បច្ចេកវិទ្យា)',
    'Lanton Pay': 'ឡានតុនផេ',
    'LOLC': 'អេអិលអូអិលស៊ី',
    'Ly Hour': 'លីហួរ ផេ ផ្រូ',
    'Maybank': 'ធនាគារ Maybank',
    'MB Cambodia': 'ធនាគារ MB Cambodia',
    'Mohanokor': 'មហានគរ',
    'Oriental': 'ធនាគារ អូរៀនថល',
    'Panda': 'ធនាគារ ផេនដា',
    'Phillip': 'ធនាគារ Phillip',
    'PPCBank': 'ធនាគារ ភ្នំពេញ ពាណិជ្ជ',
    'Pi Pay': 'ភី ប៉េ',
    'Prince': 'ធនាគារ ព្រីនស៍',
    'RHB': 'ធនាគារ RHB',
    'Sacombank': 'ធនាគារ សាកុមប៊ែង',
    'Sathapana': 'ធនាគារ សត្ថាភណៈ',
    'SBI LY HOUR': 'ធនាគារ SBI លីហួរ',
    'Shinhan': 'ធនាគារ ស៊ីនហាន',
    'TrueMoney': 'ធនាគារ ទ្រូម៉ានី',
    'Union Commercial': 'ធនាគារ សហពាណិជ្ជកម្ម',
    'U-Pay': 'យូផេ ឌីជីថល',
    'Vattanac': 'ធនាគារ វឌ្ឍនៈ',
    'Wing': 'ធនាគារ វីង',
    'Woori': 'ធនាគារ អ៊ូរី'
}

# Phonetic mappings for natural English pronunciation
bank_phonetic_mappings = {
    'ABA': 'A B A',
    'ACLEDA': 'AC leda',
    'ARDB': 'Agricultural and Rural Development Bank',
    'APD': 'APD Bank',
    'AMK': 'AMK Microfinance',
    'Amret': 'Amret',
    'Asia Wei Luy': 'Asia Wei Luy',
    'Bank of China': 'Bank of China',
    'BIDC': 'BIDC Bank',
    'BongLoy': 'Bong Loy',
    'BRED': 'Bred Bank',
    'Cambodia Asia': 'Cambodia Asia Bank',
    'CPBank': 'Cambodia Post Bank',
    'Campu Bank': 'Campu Bank',
    'Canadia': 'Canadia Bank',
    'Cathay United': 'Cathay United Bank',
    'CCU': 'CCU Bank',
    'Chief': 'Chief Bank',
    'Chip Mong': 'Chip Mong Bank',
    'CIMB': 'CIMB Bank',
    'Cool Cash': 'Cool Cash',
    'DGB': 'DGB Bank',
    'eMoney': 'eMoney',
    'First Commercial': 'First Commercial Bank',
    'FTB': 'Foreign Trade Bank',
    'Hattha': 'Hattha Bank',
    'Heng Feng': 'Heng Feng Bank',
    'Hong Leong': 'Hong Leong Bank',
    'ICBC': 'ICBC Bank',
    'J Trust Royal': 'J Trust Royal Bank',
    'KB Prasac': 'KB Prasac Bank',
    'Kess': 'Kess Innovation',
    'Lanton Pay': 'Lanton Pay',
    'LOLC': 'LOLC Cambodia',
    'Ly Hour': 'Ly Hour Pay Pro',
    'Maybank': 'Maybank',
    'MB Cambodia': 'MB Cambodia Bank',
    'Mohanokor': 'Mohanokor',
    'Oriental': 'Oriental Bank',
    'Panda': 'Panda Bank',
    'Phillip': 'Phillip Bank',
    'PPCBank': 'Phnom Penh Commercial Bank',
    'Pi Pay': 'Pi Pay',
    'Prince': 'Prince Bank',
    'RHB': 'RHB Bank',
    'Sacombank': 'Sacombank',
    'Sathapana': 'Sathapana Bank',
    'SBI LY HOUR': 'SBI Ly Hour Bank',
    'Shinhan': 'Shinhan Bank',
    'TrueMoney': 'True Money',
    'Union Commercial': 'Union Commercial Bank',
    'U-Pay': 'U Pay Digital',
    'Vattanac': 'Vattanac Bank',
    'Wing': 'Wing Bank',
    'Woori': 'Woori Bank'
}

def play_alert_sound(amount_str):
    try:
        amount_value = float(re.search(r'\d+\.\d+', amount_str).group())
    except (AttributeError, ValueError):
        logger.warning("Failed to parse amount, using default $1.00")
        amount_value = 1.0
    frequency = int(1000 + amount_value * 2000)
    duration = int(300 + amount_value * 500)
    frequency = min(max(frequency, 1000), 3000)
    duration = min(max(duration, 300), 800)
    logger.info(f"Playing sound: frequency={frequency}Hz, duration={duration}ms for amount={amount_str}")
    try:
        if platform.system() == "Windows":
            for _ in range(2):
                winsound.Beep(frequency, duration)
        else:
            logger.warning("Sound alerts (winsound) are only supported on Windows.")
    except Exception as e:
        logger.error(f"Failed to play sound: {e}")

def transliterate_name_to_khmer(name):
    """Dynamically transliterate English names to Khmer phonetics or preserve Khmer names."""
    import re

    # Check if the name is already in Khmer
    if re.match(r'[\u1780-\u17FF\s]+', name):
        return name

    # Comprehensive mapping of Khmer characters to Latin sounds
    khmer_to_latin = {
        # Consonants
        'ក': 'k', 'ខ': 'kh', 'ង': 'ng', 'ច': 'ch', 'ឆ': 'chh', 'ជ': 'j',
        'ញ': 'nh', 'ដ': 'd', 'ត': 't', 'ថ': 'th', 'ន': 'n', 'ប': 'b',
        'ព': 'p', 'ភ': 'ph', 'ម': 'm', 'យ': 'y', 'រ': 'r', 'ល': 'l',
        'វ': 'v', 'ស': 's', 'ហ': 'h', 'អ': 'a',
        # Vowels and diphthongs
        'ា': 'a', 'ိ': 'i', 'ី': 'i', 'ុ': 'u', 'ូ': 'o', 'ួ': 'ua',
        'ើ': 'ae', 'ឿ': 'ue', 'ៀ': 'ia', 'េ': 'e', 'ែ': 'ae', 'ៃ': 'ai',
        'ោ': 'ao', 'ៅ': 'au', 'ឹ': 'ue', 'ឺ': 'eu', '័យ': 'oy'
    }
    latin_to_khmer = {v: k for k, v in khmer_to_latin.items()}

    # Phonetic mappings for English sounds
    sound_mappings = {
        # Consonant clusters
        'ph': 'ភ', 'th': 'ថ', 'ch': 'ច', 'chh': 'ឆ', 'kh': 'ខ', 'sh': 'ស',
        'zh': 'ជ', 'ng': 'ង', 'nh': 'ញ', 'f': 'ហ្វ', 'z': 'ហ្ស',
        # Vowels and diphthongs
        'a': 'ា', 'e': 'េ', 'i': 'ិ', 'o': 'ោ', 'u': 'ុ',
        'ea': 'ៀ', 'ee': 'ី', 'ai': 'ៃ', 'ay': 'ៃ', 'oi': '័យ', 'oy': 'ុយ',
        'ou': 'ូ', 'ow': 'ោ', 'au': 'ៅ', 'aw': 'ៅ', 'ie': 'ៀ', 'ue': 'ឿ',
        'er': 'ឹ', 'ar': 'ា', 'or': 'ៅ', 'on': 'ុន', 'an': 'ាន', 'en': 'េន',
        'in': 'ិន', 'un': 'ុន', 'oo': 'ូ'
    }

    # Split name into parts (e.g., "Chhoy Too" -> ["Chhoy", "Too"])
    parts = name.strip().split()
    khmer_parts = []

    for part in parts:
        part_lower = part.lower()
        syllables = []
        i = 0
        while i < len(part_lower):
            found = False

            # Handle "Too" explicitly
            if part_lower == 'too':
                syllables.append('ទូ')
                i = len(part_lower)
                found = True
                break

            # Try matching longer patterns first (up to 4 characters)
            for length in [4, 3, 2, 1]:
                if i + length <= len(part_lower):
                    substr = part_lower[i:i+length]
                    if substr in sound_mappings:
                        syllables.append(sound_mappings[substr])
                        i += length
                        found = True
                        break

            if not found:
                # Handle single characters
                char = part_lower[i]
                if char in 'bcdfghjklmnpqrstvwxyz':
                    consonant_map = {
                        'b': 'ប', 'c': 'ក', 'd': 'ដ', 'f': 'ហ្វ', 'g': 'ក',
                        'h': 'ហ', 'j': 'ជ', 'k': 'ក', 'l': 'ល', 'm': 'ម',
                        'n': 'ន', 'p': 'ព', 'q': 'ក', 'r': 'រ', 's': 'ស',
                        't': 'ត', 'v': 'វ', 'w': 'វ', 'x': 'ស', 'y': 'យ', 'z': 'ហ្ស'
                    }
                    syllables.append(consonant_map.get(char, 'ក'))
                elif char in 'aeiou':
                    vowel_map = {
                        'a': 'ា', 'e': 'េ', 'i': 'ិ', 'o': 'ោ', 'u': 'ុ'
                    }
                    syllables.append(vowel_map.get(char, 'ា'))
                i += 1

        # Build Khmer syllable with proper structure
        khmer_syllable = ''
        i = 0
        while i < len(syllables):
            current = syllables[i]
            khmer_syllable += current

            # Add subscript for specific final consonants
            if (i < len(syllables) - 1 and current in khmer_to_latin and
                    syllables[i+1] in ['យ', 'រ', 'ល', 'វ']):
                khmer_syllable += '្'
            # Skip adding vowel if next is a vowel or at word end
            elif (i < len(syllables) - 1 and syllables[i+1] in
                  'ាិីុូួើឿៀេែៃោៅឹឺ័យ'):
                pass
            i += 1

        khmer_parts.append(khmer_syllable)

    return ' '.join(khmer_parts) if khmer_parts else name

def number_to_khmer(num):
    """Convert number to Khmer words."""
    numbers = {
        '0': 'សូន្យ', '1': 'មួយ', '2': 'ពីរ', '3': 'បី', '4': 'បួន',
        '5': 'ប្រាំ', '6': 'ប្រាំមួយ', '7': 'ប្រាំពីរ', '8': 'ប្រាំបី', '9': 'ប្រាំបួន',
        '10': 'ដប់', '11': 'ដប់មួយ', '12': 'ដប់ពីរ', '13': 'ដប់បី', '14': 'ដប់បួន',
        '15': 'ដប់ប្រាំ', '16': 'ដប់ប្រាំមួយ', '17': 'ដប់ប្រាំពីរ', '18': 'ដប់ប្រាំបី', '19': 'ដប់ប្រាំបួន',
        '20': 'ម្ភៃ', '30': 'សាមសិប', '40': 'សែសិប', '50': 'ហាសិប', '60': 'ហុកសិប',
        '70': 'ចិតសិប', '80': 'ប៉ែតសិប', '90': 'កៅសិប'
    }
    num_str = str(num)
    if num_str in numbers:
        return numbers[num_str]
    elif len(num_str) == 2 and int(num_str) < 100:
        tens = int(num_str[0]) * 10
        ones = int(num_str[1])
        if tens in numbers and ones in numbers:
            return f"{numbers[str(tens)]}{numbers[str(ones)]}"
    return num_str

def translate_to_khmer(amount, payer, date_time, trx_id, bank_name):
    """Translate transaction details to Khmer, using Khmer bank name."""
    numbers = {
        '0': 'សូន្យ', '1': 'មួយ', '2': 'ពីរ', '3': 'បី', '4': 'បួន',
        '5': 'ប្រាំ', '6': 'ប្រាំមួយ', '7': 'ប្រាំពីរ', '8': 'ប្រាំបី', '9': 'ប្រាំបួន'
    }
    payer_kh = transliterate_name_to_khmer(payer)
    bank_name_kh = bank_name
    # Extract full bank name from parentheses or use bank_name directly
    bank_part = re.search(r'\(([^\)]+)', bank_name)
    bank_core = bank_part.group(1) if bank_part else bank_name
    # Sort keys by length to prioritize specific matches (e.g., "TrueMoney" over "eMoney")
    for eng_name, kh_name in sorted(bank_name_mappings.items(), key=lambda x: -len(x[0])):
        if eng_name.lower() in bank_core.lower():
            bank_name_kh = kh_name
            break
    try:
        amount_value = float(re.search(r'\d+\.\d+', amount).group())
        dollar = int(amount_value)
        cent = int((amount_value - dollar) * 100)
        if cent > 0:
            amount_kh = f"{number_to_khmer(cent)} សេន"
        else:
            amount_kh = f"{numbers[str(dollar)]} ដុល្លារ"
    except:
        amount_kh = "មួយ ដុល្លារ"
    try:
        dt = datetime.strptime(date_time, '%B %d, %I:%M %p')
        day = numbers[str(dt.day)] if str(dt.day) in numbers else str(dt.day)
        month = {
            'May': 'ឧសភា', 'January': 'មករា', 'February': 'កុម្ភៈ', 'March': 'មីនា',
            'April': 'មេសា', 'June': 'មិថុនា', 'July': 'កក្កដា', 'August': 'សីហា',
            'September': 'កញ្ញា', 'October': 'តុលា', 'November': 'វិច្ឆិកា', 'December': 'ធ្នូ'
        }.get(dt.strftime('%B'), 'ខែមិនស្គាល់')
        # Handle 12 PM/AM correctly
        hour = dt.hour if dt.hour <= 12 else dt.hour - 12
        hour = 12 if hour == 0 else hour  # Convert 0 to 12 for 12 AM/PM
        hour_kh = number_to_khmer(str(hour))
        minute = number_to_khmer(str(dt.minute).zfill(2))
        period = 'ល្ងាច' if dt.strftime('%p') == 'PM' else 'ព្រឹក'
        date_time_kh = f"ថ្ងៃទី{day} {month} ម៉ោង{hour_kh}និង{minute}នាទី {period}"
    except:
        date_time_kh = "ម៉ោងមិនស្គាល់"
    trx_id_kh = ''.join(numbers.get(d, d) for d in str(trx_id))
    khmer_message = f"ទទួលបាន {amount_kh} ពី {payer_kh} តាម {bank_name_kh} នៅ {date_time_kh}"
    return khmer_message

def parse_bank_message(text):
    """Parse transaction messages from different banks."""
    # Pattern for ABA PAY
    aba_pay_pattern = r'\$(\d+\.\d+) paid by ([\u1780-\u17FF\s]+|[A-Za-z\s]+)\s*(?:\([^\)]+\))?\s*on ([\w\s, :]+ PM|AM)\s*via ABA PAY\s*at [A-Z\s]+.*Trx\. ID: (\d+)'
    aba_pay_match = re.search(aba_pay_pattern, text)
    if aba_pay_match:
        return {
            'bank': 'ABA',
            'amount': aba_pay_match.group(1),
            'payer': aba_pay_match.group(2).strip(),
            'date_time': aba_pay_match.group(3).strip(),
            'trx_id': aba_pay_match.group(4)
        }
    # Pattern for ABA KHQR
    aba_pattern = r'\$(\d+\.\d+) paid by ([\u1780-\u17FF\s]+|[A-Za-z\s]+)\s*(?:\([^\)]+\))?\s*on ([\w\s, :]+ PM|AM)\s*via (ABA KHQR \([^\)]+\))\s*at [A-Z\s]+.*Trx\. ID: (\d+)'
    aba_match = re.search(aba_pattern, text)
    if aba_match:
        return {
            'bank': aba_match.group(4),
            'amount': aba_match.group(1),
            'payer': aba_match.group(2).strip(),
            'date_time': aba_match.group(3).strip(),
            'trx_id': aba_match.group(5)
        }
    # Pattern for Canadia Bank
    canadia_pattern = r'Canadia Bank: \$(\d+\.\d+) paid by ([\u1780-\u17FF\s]+|[A-Za-z\s]+) on ([\w\s, :]+ PM|AM)\. Transaction ID: (\d+)'
    canadia_match = re.search(canadia_pattern, text)
    if canadia_match:
        return {
            'bank': 'Canadia',
            'amount': canadia_match.group(1),
            'payer': canadia_match.group(2).strip(),
            'date_time': canadia_match.group(3).strip(),
            'trx_id': canadia_match.group(4)
        }
    # Pattern for Wing
    wing_pattern = r'Wing: \$(\d+\.\d+) from ([\u1780-\u17FF\s]+|[A-Za-z\s]+) on ([\w\s, :]+ PM|AM), Trans ID: (\d+)'
    wing_match = re.search(wing_pattern, text)
    if wing_match:
        return {
            'bank': 'Wing',
            'amount': wing_match.group(1),
            'payer': wing_match.group(2).strip(),
            'date_time': wing_match.group(3).strip(),
            'trx_id': wing_match.group(4)
        }
    return None

def read_message_aloud(text):
    try:
        parsed = parse_bank_message(text)
        if not parsed:
            logger.warning("Unrecognized bank message format")
            return
        khmer_message = translate_to_khmer(
            parsed['amount'],
            parsed['payer'],
            parsed['date_time'],
            parsed['trx_id'],
            parsed['bank']
        )
        logger.info(f"Khmer TTS message: {khmer_message}")
        bank_name = parsed['bank']
        phonetic_bank_name = bank_name
        # Extract core bank name for TTS (e.g., "TrueMoney" from "TrueMoney Cambodia")
        bank_part = re.search(r'\(([^\)]+)', bank_name)
        bank_core = bank_part.group(1).split()[0] if bank_part else bank_name
        # Sort keys by length to prioritize specific matches (e.g., "TrueMoney" over "eMoney")
        for eng_name, phonetic in sorted(bank_phonetic_mappings.items(), key=lambda x: -len(x[0])):
            if eng_name.lower() in bank_core.lower():
                phonetic_bank_name = f"ABA K H Q R {phonetic}"
                break
        logger.info(f"English TTS message: via {phonetic_bank_name}")
        khmer_file = f"temp_tts_khmer_{int(time.time() * 1000)}.mp3"
        english_file = f"temp_tts_english_{int(time.time() * 1000)}.mp3"
        tts_khmer = gTTS(text=khmer_message, lang='km')
        tts_khmer.save(khmer_file)
        bank_message = f"via {phonetic_bank_name}"
        tts_english = gTTS(text=bank_message, lang='en')
        tts_english.save(english_file)
        pygame.mixer.music.load(khmer_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        pygame.mixer.music.load(english_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        pygame.mixer.music.stop()
        for temp_file in [khmer_file, english_file]:
            for _ in range(3):
                try:
                    os.remove(temp_file)
                    break
                except PermissionError:
                    logger.warning(f"Retrying deletion of {temp_file}")
                    time.sleep(0.1)
        logger.info("TTS completed with gTTS")
    except Exception as e:
        logger.error(f"TTS error: {e}")

@client.on(events.NewMessage(chats=group_chat_id))
async def handler(event):
    message = event.message
    sender = await message.get_sender()
    logger.info(f"New message received: {message.text}")
    logger.info(f"Sender: {sender.username if sender else 'Unknown'}")
    if sender and sender.username in ["PayWayByABA_bot", "chhoy_too"]:
        text = message.text
        logger.info(f"Message from @{sender.username}: {text}")
        parsed = parse_bank_message(text)
        if parsed:
            play_alert_sound(parsed['amount'])
            read_message_aloud(text)
            logger.info("Message processed with alert and TTS")
        else:
            logger.warning("Message format not recognized, skipping processing")

async def main():
    try:
        await client.start(phone=phone)
        logger.info("Message processing bot is running...")
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Bot failed: {e}")

if __name__ == "__main__":
    import asyncio
    if platform.system() != "Windows":
        logger.warning("Sound alerts (winsound) are only supported on Windows.")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Main loop error: {e}")