"""Generate app/data/strings.json and app/data/forms.json.

Texts below were copied verbatim from the handlers in tools/original_main.py
(d_step*, l_step*, ph_step*, working_hours_gate, show_discover_more, ...).
Run after extract_content.py:  python tools/build_data.py
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "data"

STRINGS = {
    "offline": (
        "⏰ *Bot is Currently Offline*\n\n"
        "⏰ *ቦቱ በዚህ ሰአት ከአገልግሎት ውጭ ነው*\n\n"
        "📞 Please call us at: *{phone}*\n\n"
        "📞 እባክዎን በዚህ ቁጥር ይደውሉልን: *{phone}*\n\n"
        "Our team is available during working hours to assist you directly.\n\n"
        "ቡድናችን በዚህ ሰዓት እርሶን በቀጥታ ለመርዳት ዝግጁ ናችው።\n\n"
        "🤖 The bot will be available again after 8:00 PM Ethiopian Time.\n\n"
        "🤖 ቦቱ ከምሽቱ 2:00 ሰዓት በኋላ ነው አገልግሎት የሚሰጠው።\n\n"
        "Thank you for understanding! 🙏\n"
        "ስለተረዱን እናመሰግናለን! 🙏"),
    "payment_notice": (
        "⚠️ *IMPORTANT / አስፈላጊ* ⚠️\n\n"
        "🏦 *Bank Account Details / የባንክ አካውንት ዝርዝር*:\n\n"
        "🏧 *Commercial Bank of Ethiopia (CBE) / የኢትዮጵያ ንግድ ባንክ *\n"
        "👤 Account Name: {account_name} \n"
        "🔢 Account Number: {account_number}\n\n"
        "💵 Amount: 50% of the selected package \n\n"
        "✅ After filling this form, please send a screenshot of your 50% deposit payment to confirm your booking.\n"
        "‼️ Note: Booking will not be considered complete until the deposit is received.\n\n"
        "✅ ይህንን ቅጽ ከሞሉ በኋላ፣ ትዕዛዝዎን ለማረጋገጥ የ50% የተቀማጭ ክፍያ ስክሪን ሾት ይላኩ።\n"
        "‼️ ማሳሰቢያ፡- ተቀማጭ ገንዘብ እስኪደርስ ድረስ ትዕዛዝዎ እንደተጠናቀቀ አይቆጠርም።\n"),
    "upload_prompt": {"decor": "📤 Upload your Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
                      "limo": "📤 Upload Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:",
                      "photo": "📤 Upload Payment Screenshot / የክፍያ ስክሪን ሾት ይላኩ:"},
    "upload_error": "Please upload a photo. / እባክዎ ፎቶ ይላኩ።",
    "client_caption": "✅ Your booking is awaiting confirmation. / ማረጋገጫ በመጠበቅ ላይ።",
    "catalog_caption": "📋 Our complete services catalog / ሙሉ የአገልግሎት ዝርዝር",
    "catalog_missing": "PDF catalog will be available soon. / የአገልግሎት ዝርዝር በቅርቡ ይገኛል።",
    "welcome_choose": "🌿 Welcome! Choose Language / ቋንቋ ይምረጡ:",
    "discover_single": {
        "decor": {"en": "Why not add beautiful decor to complete your celebration?", "am": "ዝግጅታችሁን ለማስዋብ ዲኮር አሁን ይዘዙ!"},
        "limo": {"en": "Make a grand entrance with our limousine service!", "am": "በሊሙዚን አገልግሎታችን በታላቅ አቀባበል ይግቡ!"},
        "photo": {"en": "Capture every moment with our photography!", "am": "ትዝታዎችን በፎቶግራፍ ይቅረጹ!"}},
    "discover_generic": {"en": "Explore our other services!", "am": "ሌሎች አገልግሎቶቻችንን ይመልከቱ!"},
    "discover_buttons": {
        "decor": {"en": "🎁 Book Decor", "am": "🎁 ዲኮር ይዘዙ"},
        "limo": {"en": "🚗 Book Limousine", "am": "🚗 ሊሙዚን ይዘዙ"},
        "photo": {"en": "📸 Book Photography", "am": "📸 የፎቶግራፍ አገልግሎት ይዘዙ"},
        "contact": {"en": "📞 Contact Us", "am": "📞 ያግኙን"}},
    "back_to_packages": {"en": "🔙 Back to Packages", "am": "🔙 ወደ ፓኬጆች ተመለስ"},
}

L = lambda en, am: {"en": en, "am": am}  # noqa: E731
DATE_HINT = L("(e.g., 21/08/2018, Morning 4:00 AM)", "(ለምሳሌ፡ 21/08/2018, ጥዋት 4፡00)")
USERNAME = {"id": "username", "type": "username", "optional": True,
            "label": L("Your Telegram Username (e.g., @username)", "የቴሌግራም መለያዎ (ለምሳሌ፡ @username)")}
NAME = {"id": "name", "type": "text", "label": L("Full Name", "ሙሉ ስም")}
PKG = lambda en, am: {"id": "package", "type": "package", "label": L(en, am)}  # noqa: E731

FORMS = {
    "decor": {
        "prefix": "DEC", "icon": "🎁", "title": L("Decor Booking", "ዲኮር ለማዘዝ"),
        "pdf_title": "DECOR SERVICE",
        "admin_title": "🔔 <b>NEW DECOR SERVICE BOOKING / አዲስ የዲኮር ትዕዛዝ</b> 🔔",
        "file_prefix": "Decor", "client_file": "AGOS_Decor_Booking.pdf",
        "fields": [
            NAME,
            {"id": "gender", "type": "choice", "label": L("Gender of the Newborn", "የሕፃኑ ጾታ"),
             "options": [{"v": "Male", "en": "Male", "am": "ወንድ"}, {"v": "Female", "en": "Female", "am": "ሴት"},
                         {"v": "NotSure", "en": "Not Sure", "am": "እርግጠኛ አይደለሁም"}]},
            {"id": "phone", "type": "phone", "label": L("Client Phone Number", "የደንበኛ ስልክ ቁጥር")},
            USERNAME,
            {"id": "alt_phone", "type": "phone", "optional": True, "label": L("Alternative Phone Number", "አማራጭ የስልክ ቁጥር")},
            {"id": "address", "type": "textarea", "label": L("House Address for Decor Setup", "ዲኮር የሚሰራበት የቤት አድራሻ")},
            {"id": "house", "type": "choice", "label": L("House Type", "የቤት አይነት"),
             "options": [{"v": "Villa", "en": "Villa", "am": "ቪላ"}, {"v": "Apartment", "en": "Apartment", "am": "አፓርትመንት"},
                         {"v": "Condominium", "en": "Condominium", "am": "ኮንዶሚየም"},
                         {"v": "G+1", "en": "G+1", "am": "G+1"}, {"v": "G+2", "en": "G+2", "am": "G+2"}]},
            PKG("Select your preferred Decor Package", "የሚፈልጉትን የዲኮር ፓኬጅ ይምረጡ"),
            {"id": "date", "type": "datetime", "hint": DATE_HINT,
             "label": L("Preferred Date & Time for the Decor setup", "ዲኮሩን የሚፈልጉበት ቀን እና ሰአት")},
        ],
        "steps": [["name", "gender", "phone", "username", "alt_phone"], ["address", "house", "package", "date"]],
        "admin_rows": [
            ["1. CLIENT INFORMATION", [["Full Name", "name"], ["Baby Gender", "gender"], ["Primary Contact", "phone"],
                                       ["Telegram", "username"], ["Alternative Contact", "alt_phone"]]],
            ["2. SERVICE DETAILS", [["Package", "package"], ["Service Address", "address"], ["House Type", "house"],
                                    ["Preferred Date", "date"]]]],
        "pdf_rows": [
            ["1. CLIENT INFORMATION", [["Full Name", "name"], ["Gender of Newborn", "gender"], ["Primary Contact Number", "phone"],
                                       ["Telegram Username", "username"], ["Alternative Contact Number", "alt_phone"]]],
            ["2. SERVICE DETAILS", [["Selected Package", "package"], ["Service Address", "address"], ["House Type", "house"],
                                    ["Preferred Date & Time", "date"]]]],
    },
    "limo": {
        "prefix": "LIMO", "icon": "🚗", "title": L("Limousine Booking", "ሊሙዚን ማዘዣ"),
        "pdf_title": "LIMOUSINE SERVICE",
        "admin_title": "🔔 <b>NEW LIMOUSINE SERVICE BOOKING / አዲስ የሊሙዚን ትዕዛዝ</b> 🔔",
        "file_prefix": "Limousine", "client_file": "AGOS_Limousine_Booking.pdf",
        "fields": [
            NAME,
            {"id": "phone", "type": "phone", "label": L("Phone Number", "ስልክ ቁጥር")},
            USERNAME,
            {"id": "date", "type": "datetime", "hint": DATE_HINT, "label": L("Preferred Date & Time", "የሚፈልጉት ቀን እና ሰዓት")},
            {"id": "address", "type": "textarea", "label": L("Pickup Address & Destination", "የሚነሱበት አድራሻ & መዳረሻ / የቤትዎ አድራሻ"),
             "hint": L("(e.g., from 4 Kilo Hemen Hospital to Kality)", "(ለምሳሌ፡ ከ 4 ኪሎ ሄመን ሆስፒታል ወደ ቃሊቲ)")},
            PKG("Select Package", "ፓኬጅ ይምረጡ"),
        ],
        "steps": [["name", "phone", "username"], ["date", "address", "package"]],
        "admin_rows": [
            ["1. CLIENT INFORMATION", [["Full Name", "name"], ["Contact Number", "phone"], ["Telegram", "username"]]],
            ["2. SERVICE DETAILS", [["Package", "package"], ["Scheduled Date", "date"], ["Pickup & Destination", "address"]]]],
        "pdf_rows": [
            ["1. CLIENT INFORMATION", [["Full Name", "name"], ["Contact Number", "phone"], ["Telegram Username", "username"]]],
            ["2. SERVICE DETAILS", [["Selected Package", "package"], ["Scheduled Date & Time", "date"],
                                    ["Pickup Address & Destination", "address"]]]],
    },
    "photo": {
        "prefix": "PHOTO", "icon": "📸",
        "title": L("Photograph / videography Services Booking", "የፎቶግራፍ አገልግሎት ማዘዣ"),
        "pdf_title": "PHOTOGRAPHY & VIDEOGRAPHY",
        "admin_title": "🔔 <b>NEW PHOTOGRAPHY & VIDEOGRAPHY BOOKING / አዲስ የፎቶግራፍ ትዕዛዝ</b> 🔔",
        "file_prefix": "Photography", "client_file": "AGOS_Photography_Booking.pdf",
        "fields": [
            NAME,
            {"id": "phone", "type": "phone", "label": L("Phone Number", "ስልክ ቁጥር")},
            USERNAME,
            {"id": "date", "type": "datetime", "hint": DATE_HINT, "label": L("Event Date & Time", "የዝግጅቱ ቀን እና ሰዓት")},
            {"id": "address", "type": "textarea", "label": L("Event Address", "የዝግጅቱ አድራሻ")},
            PKG("Select Package", "ፓኬጅ ይምረጡ"),
        ],
        "steps": [["name", "phone", "username"], ["date", "address", "package"]],
        "admin_rows": [
            ["1. CLIENT INFORMATION", [["Full Name", "name"], ["Contact Number", "phone"], ["Telegram", "username"]]],
            ["2. SERVICE DETAILS", [["Package", "package"], ["Event Date", "date"], ["Event Address", "address"]]]],
        "pdf_rows": [
            ["1. CLIENT INFORMATION", [["Full Name", "name"], ["Contact Number", "phone"], ["Telegram Username", "username"]]],
            ["2. SERVICE DETAILS", [["Selected Package", "package"], ["Event Date & Time", "date"], ["Event Address", "address"]]]],
    },
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "strings.json").write_text(json.dumps(STRINGS, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "forms.json").write_text(json.dumps(FORMS, ensure_ascii=False, indent=2), encoding="utf-8")
    print("strings.json + forms.json written")
