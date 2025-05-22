#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
#UTILS HOLIDAY DATABASE FULLY WRITTEN BY @abirxdhackz & @ISmartDevs & @nkka404 For time.py To Show Holidays On Button Callback

HOLIDAYS = {
    "BD": {  # Bangladesh
        (2, 21): "শহীদ দিবস 🕊️ (International Mother Language Day)",
        (3, 26): "স্বাধীনতা দিবস 🇧🇩 (Independence Day)",
        (4, 14): "বাংলা নববর্ষ 🎊 (Bengali New Year)",
        (12, 16): "বিজয় দিবস 🇧🇩 (Victory Day)",
        # Islamic holidays (fixed dates)
        (3, 10): "ঈদুল ফিতর 🕌 (Eid al-Fitr)",
        (6, 16): "ঈদুল আজহা 🐪 (Eid al-Adha)",
        (7, 7): "ইসলামিক নববর্ষ 🌙 (Islamic New Year)",
        (9, 15): "মিলাদুন্নবী ﷺ (Prophet's Birthday)"
    },
    "US": {  # United States
        (1, 1): "New Year's Day 🎉",
        (1, 15): "Martin Luther King Jr. Day ✊",
        (2, 19): "Presidents' Day 🇺🇸",
        (5, 27): "Memorial Day 🕊️",
        (6, 19): "Juneteenth 🎉",
        (7, 4): "Independence Day 🇺🇸",
        (9, 2): "Labor Day 🛠️",
        (10, 14): "Columbus Day ⛵",
        (11, 11): "Veterans Day 🎖️",
        (11, 28): "Thanksgiving 🦃",
        (12, 25): "Christmas Day 🎄"
    },
    "GB": {  # United Kingdom
        (1, 1): "New Year's Day 🎉",
        (3, 29): "Good Friday ✝️",
        (4, 1): "Easter Monday 🐣",
        (5, 6): "Early May Bank Holiday 🌸",
        (5, 27): "Spring Bank Holiday 🌷",
        (8, 26): "Summer Bank Holiday ☀️",
        (12, 25): "Christmas Day 🎄",
        (12, 26): "Boxing Day 🎁"
    },
    "ID": {  # Indonesia
        (1, 1): "Tahun Baru Masehi 🎉 (New Year's Day)",
        (5, 1): "Hari Buruh Internasional 🛠️ (Labor Day)",
        (8, 17): "Hari Kemerdekaan 🇮🇩 (Independence Day)",
        (12, 25): "Hari Natal 🎄 (Christmas)",
        # Islamic holidays (fixed dates)
        (3, 11): "Idul Fitri 🕌 (Eid al-Fitr)",
        (6, 17): "Idul Adha 🐪 (Eid al-Adha)",
        (7, 8): "Tahun Baru Islam 🌙 (Islamic New Year)",
        (9, 16): "Maulid Nabi ﷺ (Prophet's Birthday)"
    },
    "CN": {  # China
        (1, 1): "元旦 🎉 (New Year's Day)",
        (2, 10): "春节 🧧 (Chinese New Year)",
        (4, 4): "清明节 🌿 (Qingming Festival)",
        (5, 1): "劳动节 🛠️ (Labor Day)",
        (6, 10): "端午节 🎏 (Dragon Boat Festival)",
        (9, 17): "中秋节 🥮 (Mid-Autumn Festival)",
        (10, 1): "国庆节 🇨🇳 (National Day)"
    },
    "JP": {  # Japan
        (1, 1): "元日 🎍 (New Year's Day)",
        (2, 11): "建国記念日 🇯🇵 (National Foundation Day)",
        (4, 29): "昭和の日 🎎 (Showa Day)",
        (5, 3): "憲法記念日 📜 (Constitution Day)",
        (5, 4): "みどりの日 🌳 (Greenery Day)",
        (5, 5): "こどもの日 🎏 (Children's Day)",
        (8, 11): "山の日 ⛰️ (Mountain Day)",
        (11, 3): "文化の日 🎭 (Culture Day)",
        (11, 23): "勤労感謝の日 🛠️ (Labor Thanksgiving Day)",
        (12, 23): "天皇誕生日 👑 (Emperor's Birthday)"
    },
    "KR": {  # South Korea
        (1, 1): "신정 🎉 (New Year's Day)",
        (3, 1): "삼일절 🇰🇷 (Independence Movement Day)",
        (5, 5): "어린이날 🎏 (Children's Day)",
        (6, 6): "현충일 🕊️ (Memorial Day)",
        (8, 15): "광복절 🇰🇷 (Liberation Day)",
        (10, 3): "개천절 🏮 (National Foundation Day)",
        (10, 9): "한글날 🔠 (Hangeul Day)",
        (12, 25): "크리스마스 🎄 (Christmas)"
    },
    "TH": {  # Thailand
        (1, 1): "วันปีใหม่ 🎉 (New Year's Day)",
        (4, 6): "วันจักรี 👑 (Chakri Memorial Day)",
        (4, 13): "วันสงกรานต์ 💦 (Songkran Festival)",
        (5, 4): "วันฉัตรมงคล 🏯 (Coronation Day)",
        (7, 28): "วันเฉลิมพระชนมพรรษา 👑 (King's Birthday)",
        (12, 5): "วันพ่อแห่งชาติ 👨‍👧‍👦 (Father's Day)",
        (12, 10): "วันรัฐธรรมนูญ 📜 (Constitution Day)",
        (12, 31): "วันสิ้นปี 🎊 (New Year's Eve)"
    },
    "VN": {  # Vietnam
        (1, 1): "Tết Dương lịch 🎉 (New Year's Day)",
        (2, 10): "Tết Nguyên Đán 🧧 (Lunar New Year)",
        (4, 18): "Giỗ tổ Hùng Vương 🏯 (Hung Kings' Festival)",
        (4, 30): "Ngày Giải phóng 🎗️ (Reunification Day)",
        (5, 1): "Ngày Quốc tế Lao động 🛠️ (Labor Day)",
        (9, 2): "Quốc khánh 🇻🇳 (National Day)"
    },
    "RU": {  # Russia
        (1, 1): "Новый год 🎉 (New Year's Day)",
        (2, 23): "День защитника Отечества 🎖️ (Defender of the Fatherland Day)",
        (3, 8): "Международный женский день 🌸 (International Women's Day)",
        (5, 1): "Праздник весны и труда 🌷 (Spring and Labor Day)",
        (5, 9): "День Победы 🎗️ (Victory Day)",
        (6, 12): "День России 🇷🇺 (Russia Day)",
        (11, 4): "День народного единства 🤝 (Unity Day)"
    },
    "DE": {  # Germany
        (1, 1): "Neujahrstag 🎉 (New Year's Day)",
        (5, 1): "Tag der Arbeit 🛠️ (Labor Day)",
        (10, 3): "Tag der Deutschen Einheit 🇩🇪 (German Unity Day)",
        (12, 25): "Weihnachtstag 🎄 (Christmas Day)",
        (12, 26): "Zweiter Weihnachtsfeiertag 🎁 (Boxing Day)"
    },
    "FR": {  # France
        (1, 1): "Jour de l'An 🎉 (New Year's Day)",
        (5, 1): "Fête du Travail 🛠️ (Labor Day)",
        (5, 8): "Victoire 1945 🎗️ (Victory in Europe Day)",
        (7, 14): "Fête Nationale 🎆 (Bastille Day)",
        (11, 11): "Armistice 1918 🕊️ (Armistice Day)",
        (12, 25): "Noël 🎄 (Christmas Day)"
    },
    "IT": {  # Italy
        (1, 1): "Capodanno 🎉 (New Year's Day)",
        (4, 25): "Festa della Liberazione 🎗️ (Liberation Day)",
        (5, 1): "Festa dei Lavoratori 🛠️ (Labor Day)",
        (6, 2): "Festa della Repubblica 🇮🇹 (Republic Day)",
        (12, 25): "Natale 🎄 (Christmas Day)",
        (12, 26): "Santo Stefano 🎁 (St. Stephen's Day)"
    },
    "ES": {  # Spain
        (1, 1): "Año Nuevo 🎉 (New Year's Day)",
        (1, 6): "Día de Reyes 👑 (Epiphany)",
        (5, 1): "Día del Trabajador 🛠️ (Labor Day)",
        (10, 12): "Fiesta Nacional 🇪🇸 (National Day)",
        (12, 6): "Día de la Constitución 📜 (Constitution Day)",
        (12, 25): "Navidad 🎄 (Christmas Day)"
    },
    "BR": {  # Brazil
        (1, 1): "Ano Novo 🎉 (New Year's Day)",
        (4, 21): "Tiradentes ⚖️ (Tiradentes Day)",
        (5, 1): "Dia do Trabalhador 🛠️ (Labor Day)",
        (9, 7): "Independência 🇧🇷 (Independence Day)",
        (10, 12): "Nossa Senhora Aparecida 🙏 (Our Lady Aparecida)",
        (11, 2): "Finados 🕊️ (All Souls' Day)",
        (11, 15): "Proclamação da República 🏛️ (Republic Day)",
        (12, 25): "Natal 🎄 (Christmas)"
    },
    "MX": {  # Mexico
        (1, 1): "Año Nuevo 🎉 (New Year's Day)",
        (2, 5): "Día de la Constitución 📜 (Constitution Day)",
        (3, 18): "Natalicio de Juárez ⚖️ (Benito Juárez's Birthday)",
        (5, 1): "Día del Trabajo 🛠️ (Labor Day)",
        (9, 16): "Día de Independencia 🇲🇽 (Independence Day)",
        (11, 20): "Revolución Mexicana 🎗️ (Revolution Day)",
        (12, 25): "Navidad 🎄 (Christmas Day)"
    },
    "AE": {  # United Arab Emirates
        (1, 1): "رأس السنة الميلادية 🎉 (New Year's Day)",
        (12, 2): "اليوم الوطني 🇦🇪 (National Day)",
        # Islamic holidays (fixed dates)
        (3, 10): "عيد الفطر 🕌 (Eid al-Fitr)",
        (6, 16): "عيد الأضحى 🐪 (Eid al-Adha)",
        (7, 7): "رأس السنة الهجرية 🌙 (Islamic New Year)",
        (9, 15): "المولد النبوي ﷺ (Prophet's Birthday)"
    },
    "SA": {  # Saudi Arabia
        (9, 23): "اليوم الوطني 🇸🇦 (National Day)",
        # Islamic holidays (fixed dates)
        (3, 10): "عيد الفطر 🕌 (Eid al-Fitr)",
        (6, 16): "عيد الأضحى 🐪 (Eid al-Adha)",
        (7, 7): "رأس السنة الهجرية 🌙 (Islamic New Year)",
        (9, 15): "المولد النبوي ﷺ (Prophet's Birthday)"
    },
    "EG": {  # Egypt
        (1, 7): "عيد الميلاد المجيد ✝️ (Coptic Christmas)",
        (4, 25): "عيد تحرير سيناء 🎗️ (Sinai Liberation Day)",
        (7, 23): "عيد الثورة 🇪🇬 (Revolution Day)",
        (10, 6): "عيد القوات المسلحة 🎖️ (Armed Forces Day)",
        # Islamic holidays (fixed dates)
        (3, 10): "عيد الفطر 🕌 (Eid al-Fitr)",
        (6, 16): "عيد الأضحى 🐪 (Eid al-Adha)",
        (7, 7): "رأس السنة الهجرية 🌙 (Islamic New Year)",
        (9, 15): "المولد النبوي ﷺ (Prophet's Birthday)"
    },
    "ZA": {  # South Africa
        (1, 1): "New Year's Day 🎉",
        (3, 21): "Human Rights Day ✊",
        (4, 27): "Freedom Day 🕊️",
        (5, 1): "Workers' Day 🛠️",
        (6, 16): "Youth Day 🧑‍🎓",
        (8, 9): "National Women's Day 🌸",
        (9, 24): "Heritage Day 🏺",
        (12, 16): "Day of Reconciliation 🤝",
        (12, 25): "Christmas Day 🎄"
    },
    "AU": {  # Australia
        (1, 1): "New Year's Day 🎉",
        (1, 26): "Australia Day 🇦🇺",
        (4, 25): "ANZAC Day 🎖️",
        (12, 25): "Christmas Day 🎄",
        (12, 26): "Boxing Day 🎁"
    },
    "CA": {  # Canada
        (1, 1): "New Year's Day 🎉",
        (7, 1): "Canada Day 🇨🇦",
        (9, 2): "Labour Day 🛠️",
        (11, 11): "Remembrance Day 🕊️",
        (12, 25): "Christmas Day 🎄",
        (12, 26): "Boxing Day 🎁"
    },
    "MY": {  # Malaysia
        (1, 1): "Hari Tahun Baru 🎉 (New Year's Day)",
        (5, 1): "Hari Pekerja 🛠️ (Labor Day)",
        (8, 31): "Hari Kebangsaan 🇲🇾 (National Day)",
        (12, 25): "Hari Natal 🎄 (Christmas)",
        # Islamic holidays (fixed dates)
        (3, 12): "Hari Raya Puasa 🕌 (Eid al-Fitr)",
        (6, 18): "Hari Raya Haji 🐪 (Eid al-Adha)",
        (7, 9): "Awal Muharram 🌙 (Islamic New Year)",
        (9, 17): "Maulidur Rasul ﷺ (Prophet's Birthday)"
    },
    "SG": {  # Singapore
        (1, 1): "New Year's Day 🎉",
        (5, 1): "Labour Day 🛠️",
        (8, 9): "National Day 🇸🇬",
        (12, 25): "Christmas Day 🎄",
        # Chinese holidays
        (2, 10): "Chinese New Year 🧧",
        (5, 22): "Vesak Day 🕉️",
        # Islamic holidays
        (3, 11): "Hari Raya Puasa 🕌",
        (6, 17): "Hari Raya Haji 🐪"
    },
    "PH": {  # Philippines
        (1, 1): "New Year's Day 🎉",
        (6, 12): "Independence Day 🇵🇭",
        (8, 26): "National Heroes' Day 🎖️",
        (12, 25): "Christmas Day 🎄",
        (12, 30): "Rizal Day ✍️",
        # Movable dates (fixed for example)
        (4, 9): "Day of Valor 🎗️",
        (11, 1): "All Saints' Day ⛪"
    },
    "PK": {  # Pakistan
        (3, 23): "Pakistan Day 🇵🇰",
        (8, 14): "Independence Day 🎉",
        (9, 6): "Defence Day 🎖️",
        (12, 25): "Quaid-e-Azam Day 👔",
        # Islamic holidays
        (3, 12): "Eid-ul-Fitr 🕌",
        (6, 18): "Eid-ul-Adha 🐪",
        (7, 9): "Islamic New Year 🌙",
        (9, 17): "Eid Milad-un-Nabi ﷺ"
    },
    "LK": {  # Sri Lanka
        (1, 15): "Tamil Thai Pongal Day 🎊",
        (2, 4): "Independence Day 🇱🇰",
        (5, 1): "May Day 🛠️",
        (12, 25): "Christmas Day 🎄",
        # Buddhist holidays
        (1, 25): "Duruthu Full Moon Poya 🌕",
        (5, 23): "Vesak Full Moon Poya 🕉️",
        # Hindu holidays
        (10, 24): "Deepavali 🪔"
    },
    "NP": {  # Nepal
        (1, 11): "Prithvi Jayanti 👑",
        (5, 29): "Republic Day 🇳🇵",
        (9, 20): "Constitution Day 📜",
        # Hindu holidays
        (3, 25): "Holi 🎨",
        (10, 23): "Dashain 🪔",
        (11, 13): "Tihar ✨",
        # Buddhist holidays
        (5, 23): "Buddha Jayanti 🕉️"
    },
    "MM": {  # Myanmar
        (1, 4): "Independence Day 🇲🇲",
        (2, 12): "Union Day 🤝",
        (3, 2): "Peasants' Day 🌾",
        (5, 12): "404 and his girlfriend's anniversary day 🌸",
        # Thingyan holidays
        (4, 13): "Thingyan (သင်္ကြန်အကြို) 💦",
        (4, 14): "Thingyan (သင်္ကြန်အကျ) 💦",
        (4, 15): "Thingyan (သင်္ကြန်အကြတ်) 💦",
        (4, 16): "Thingyan (သင်္ကြန်အတက်) 💦",
        (4, 17): "Thingyan (နှစ်ဆန်းတစ်ရက်) 🎉",
        # Other holidays
        (4, 30): "Water Pouring Ceremony (ညောင်ရေသွန်းပွဲ) 🌳",
        (5, 1): "Labor Day (အလုပ်သမားနေ့) 💪",
        (7, 19): "Martyr's Day (အာဇာနည်နေ့) 🥀",
        # Buddhist holidays
        (7, 29): "Waso Full Moon Day (ဓမ္မစကြာနေ့) 🌕",
        (8, 29): "Waso Full Moon Day (ဓမ္မစကြာနေ့) 🌕",
        (10, 26): "Thadingyut (သီတင်းကျွတ်) 🕯️",
        (11, 24): "Tazaungdaing Festival (တန်ဆောင်တိုင်) 🎈",
        # Ethnic holidays
        (12, 1): "Kayin New Year 🎊",
        (12, 4): "National Day (အမျိုးသားနေ့) 🇲🇲❤️",
        (12, 25): "Christmas Day (ခရစ္စမတ်နေ့) 🎄"
    },
    "KH": {  # Cambodia
        (1, 7): "Victory over Genocide Day 🎗️",
        (4, 14): "Khmer New Year 🎊",
        (5, 1): "International Labor Day 🛠️",
        (11, 9): "Independence Day 🇰🇭",
        # Buddhist holidays
        (5, 22): "Visak Bochea Day 🕉️",
        (10, 3): "Pchum Ben Day 🙏"
    },
    "LA": {  # Laos
        (1, 1): "New Year's Day 🎉",
        (4, 14): "Lao New Year 💦",
        (5, 1): "Labor Day 🛠️",
        (12, 2): "National Day 🇱🇦",
        # Buddhist holidays
        (7, 21): "Boun Khao Phansa 🌕",
        (10, 8): "Boun Ok Phansa 🪔"
    },
    "TR": {  # Turkey
        (1, 1): "Yılbaşı 🎉 (New Year's Day)",
        (4, 23): "Ulusal Egemenlik ve Çocuk Bayramı 👧 (Children's Day)",
        (5, 19): "Atatürk'ü Anma, Gençlik ve Spor Bayramı 🎗️ (Youth Day)",
        (8, 30): "Zafer Bayramı 🎖️ (Victory Day)",
        (10, 29): "Cumhuriyet Bayramı 🇹🇷 (Republic Day)",
        # Islamic holidays
        (3, 11): "Ramazan Bayramı 🕌 (Eid al-Fitr)",
        (6, 17): "Kurban Bayramı 🐪 (Eid al-Adha)"
    },
    "IR": {  # Iran
        (3, 21): "Nowruz 🌸 (Persian New Year)",
        (4, 1): "Islamic Republic Day 🇮🇷",
        (6, 4): "Death of Khomeini 🕊️",
        (2, 11): "Revolution Day 🎗️",
        # Islamic holidays
        (3, 11): "Eid al-Fitr 🕌",
        (6, 17): "Eid al-Adha 🐪",
        (7, 8): "Islamic New Year 🌙",
        (9, 16): "Prophet's Birthday ﷺ"
    },
    "IL": {  # Israel
        (4, 23): "Yom HaAtzmaut 🇮🇱 (Independence Day)",
        (5, 4): "Yom HaZikaron 🕊️ (Memorial Day)",
        (9, 26): "Rosh Hashanah 🍎 (Jewish New Year)",
        (10, 5): "Yom Kippur ✡️ (Day of Atonement)",
        # Other Jewish holidays
        (3, 24): "Purim 🎭",
        (12, 23): "Hanukkah 🕎"
    },
    "NZ": {  # New Zealand
        (1, 1): "New Year's Day 🎉",
        (2, 6): "Waitangi Day 🇳🇿",
        (4, 25): "ANZAC Day 🎖️",
        (12, 25): "Christmas Day 🎄",
        (12, 26): "Boxing Day 🎁",
        # Maori holidays
        (6, 24): "Matariki 🌌 (Maori New Year)"
    },
    "AR": {  # Argentina
        (1, 1): "Año Nuevo 🎉 (New Year's Day)",
        (5, 25): "Día de la Revolución de Mayo 🎗️",
        (6, 20): "Día de la Bandera 🇦🇷 (Flag Day)",
        (7, 9): "Día de la Independencia 🎉",
        (12, 25): "Navidad 🎄 (Christmas)"
    },
    "CL": {  # Chile
        (1, 1): "Año Nuevo 🎉 (New Year's Day)",
        (5, 21): "Día de las Glorias Navales ⚓",
        (9, 18): "Fiestas Patrias 🇨🇱 (National Day)",
        (9, 19): "Día del Ejército 🎖️",
        (12, 25): "Navidad 🎄 (Christmas)"
    },
    "CO": {  # Colombia
        (1, 1): "Año Nuevo 🎉 (New Year's Day)",
        (7, 20): "Día de la Independencia 🇨🇴",
        (8, 7): "Batalla de Boyacá 🎗️",
        (12, 25): "Navidad 🎄 (Christmas)"
    },
    "PE": {  # Peru
        (1, 1): "Año Nuevo 🎉 (New Year's Day)",
        (7, 28): "Día de la Independencia 🇵🇪",
        (7, 29): "Día de la Patria 🎉",
        (12, 25): "Navidad 🎄 (Christmas)"
    },
    "VE": {  # Venezuela
        (1, 1): "Año Nuevo 🎉 (New Year's Day)",
        (6, 24): "Batalla de Carabobo 🎗️",
        (7, 5): "Día de la Independencia 🇻🇪",
        (12, 25): "Navidad 🎄 (Christmas)"
    }
}

# CREATE FUNCTION FOR IMPORTING FROM UTILS TO TIME
def get_holidays(country_code):
    return HOLIDAYS.get(country_code.upper(), {})