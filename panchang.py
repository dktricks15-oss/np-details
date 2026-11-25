#!/usr/bin/env python3

import argparse
import datetime as dt
import json
import sys
from zoneinfo import ZoneInfo

import nepali_datetime
import swisseph as swe

# ==================================================
# KATHMANDU CONFIGURATION
# ==================================================

TIMEZONE = ZoneInfo("Asia/Kathmandu")

LATITUDE = 27.7172
LONGITUDE = 85.3240
ELEVATION = 0.0

TEMPERATURE = 15.0
PRESSURE = 0.0

swe.set_sid_mode(swe.SIDM_LAHIRI)

EPHEMERIS_FLAGS = swe.FLG_MOSEPH
SIDEREAL_FLAGS = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

GEOPOS = (LONGITUDE, LATITUDE, ELEVATION)

# ==================================================
# NEPALI DIGIT CONVERTER
# ==================================================

NEPALI_DIGITS_MAP = str.maketrans("0123456789", "०१२३४५६७८९")


def to_nepali_digits(text):
    return str(text).translate(NEPALI_DIGITS_MAP)


# ==================================================
# ASTRONOMICAL NAMES & TABLES (DEVANAGARI)
# ==================================================

TITHI_NAMES = [
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पञ्चमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पञ्चमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "अमावास्या",
]

NAKSHATRA_NAMES = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा",
    "आर्द्रा", "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा",
    "पूर्वा फाल्गुनी", "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाति",
    "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढा",
    "उत्तराषाढा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वाभाद्रपद",
    "उत्तराभाद्रपद", "रेवती",
]

YOG_NAMES = [
    "विष्कम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन",
    "अतिगण्ड", "सुकर्मा", "धृति", "शूल", "गण्ड",
    "वृद्धि", "ध्रुव", "व्याघात", "हर्षण", "वज्र",
    "सिद्धि", "व्यतीपात", "वरीयान", "परिघ", "शिव",
    "सिद्ध", "साध्य", "शुभ", "शुक्ल", "ब्रह्म",
    "ऐन्द्र", "वैधृति",
]

KARAN_MOVABLE = ["बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि"]

RASHI_NAMES = [
    "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन",
]

TRANSIT_PLANETS = {
    "सूर्य": swe.SUN,
    "मङ्गल": swe.MARS,
    "बुध": swe.MERCURY,
    "बृहस्पति": swe.JUPITER,
    "शुक्र": swe.VENUS,
    "शनि": swe.SATURN,
    "राहु": swe.MEAN_NODE,
}

VARJYAM_GHATI = [
    50, 24, 30, 40, 14, 21, 30, 20, 32, 30,
    20, 18, 21, 20, 14, 14, 10, 14, 56, 24,
    20, 10, 10, 18, 16, 24, 30,
]

AMRIT_GHATI = [
    42, 48, 54, 52, 38, 44, 54, 44, 56, 54,
    44, 42, 45, 44, 38, 38, 34, 38, 54, 48,
    44, 34, 34, 42, 40, 48, 54,
]

RAHU_SEGMENTS = {
    0: 2,  # Monday
    1: 7,  # Tuesday
    2: 5,  # Wednesday
    3: 6,  # Thursday
    4: 4,  # Friday
    5: 3,  # Saturday
    6: 8,  # Sunday
}

CHOGHADIYA_CYCLE = ["उद्वेग", "चर", "लाभ", "अमृत", "काल", "शुभ", "रोग"]

DAY_START = {
    6: "उद्वेग",  # आइतबार
    0: "अमृत",    # सोमबार
    1: "रोग",     # मंगलबार
    2: "लाभ",     # बुधबार
    3: "शुभ",     # बिहीबार
    4: "चर",      # शुक्रबार
    5: "काल",     # शनिबार
}

NIGHT_START = {
    6: "चर",      # आइतबार
    0: "काल",     # सोमबार
    1: "उद्वेग",  # मंगलबार
    2: "अमृत",    # बुधबार
    3: "रोग",     # बिहीबार
    4: "लाभ",     # शुक्रबार
    5: "शुभ",     # शनिबार
}


def choghadiya_sequence(first):
    start = CHOGHADIYA_CYCLE.index(first)
    return [CHOGHADIYA_CYCLE[(start + i) % 7] for i in range(8)]


# ==================================================
# TIME & JULIAN DAY HELPERS
# ==================================================

def local_midnight(ad_date):
    return dt.datetime.combine(ad_date, dt.time.min, tzinfo=TIMEZONE)


def round_minute(value):
    if value is None:
        return None
    if value.second >= 30:
        value += dt.timedelta(minutes=1)
    return value.replace(second=0, microsecond=0)


def format_time(value):
    if value is None:
        return "--:--"
    value = round_minute(value)
    return to_nepali_digits(value.strftime("%I:%M %p").lower())


def to_julian_day(value):
    utc = value.astimezone(dt.timezone.utc)
    decimal_hour = (
        utc.hour
        + utc.minute / 60
        + utc.second / 3600
        + utc.microsecond / 3600000000
    )
    return swe.julday(utc.year, utc.month, utc.day, decimal_hour, swe.GREG_CAL)


def julian_to_local(jd):
    year, month, day, hour = swe.revjul(jd, swe.GREG_CAL)
    seconds = round(hour * 3600)
    utc = dt.datetime(year, month, day, tzinfo=dt.timezone.utc) + dt.timedelta(seconds=seconds)
    return utc.astimezone(TIMEZONE)


# ==================================================
# PLANET POSITIONS & TRANSITS
# ==================================================

def get_planet_positions(jd_ut):
    positions = {}
    for name, planet_id in TRANSIT_PLANETS.items():
        res, _ = swe.calc_ut(jd_ut, planet_id, SIDEREAL_FLAGS)
        lon = res[0] % 360.0
        speed = res[3]
        rashi_idx = min(int(lon / 30.0), 11)
        positions[name] = {
            "longitude": round(lon, 4),
            "degreeInRashi": round(lon % 30.0, 2),
            "rashiIndex": rashi_idx,
            "rashi": RASHI_NAMES[rashi_idx],
            "isRetrograde": speed < 0 and name not in ("सूर्य", "राहु"),
        }

    rahu_lon = positions["राहु"]["longitude"]
    ketu_lon = (rahu_lon + 180.0) % 360.0
    ketu_idx = min(int(ketu_lon / 30.0), 11)
    positions["केतु"] = {
        "longitude": round(ketu_lon, 4),
        "degreeInRashi": round(ketu_lon % 30.0, 2),
        "rashiIndex": ketu_idx,
        "rashi": RASHI_NAMES[ketu_idx],
        "isRetrograde": True,
    }

    return positions


# ==================================================
# ASTRONOMICAL EVENT CALCULATION
# ==================================================

def calculate_event(ad_date, body, event_type, event_flags=0):
    jd = to_julian_day(local_midnight(ad_date))
    try:
        result, times = swe.rise_trans(
            jd,
            body,
            event_type | event_flags,
            GEOPOS,
            PRESSURE,
            TEMPERATURE,
            EPHEMERIS_FLAGS,
        )
        if result != 0:
            return None
        event = julian_to_local(times[0])
        if event.date() != ad_date:
            return None
        return event
    except Exception:
        return None


def get_sun_times(ad_date):
    sunrise = calculate_event(ad_date, swe.SUN, swe.CALC_RISE)
    sunset = calculate_event(ad_date, swe.SUN, swe.CALC_SET)
    return sunrise, sunset


def get_moon_times(ad_date):
    moonrise = calculate_event(ad_date, swe.MOON, swe.CALC_RISE)
    moonset = calculate_event(ad_date, swe.MOON, swe.CALC_SET)
    return moonrise, moonset


def _moon_sidereal_lon(dt_local):
    jd_ut = to_julian_day(dt_local)
    res, _ = swe.calc_ut(jd_ut, swe.MOON, SIDEREAL_FLAGS)
    return res[0] % 360.0


def _angular_diff_signed(current_deg, target_deg):
    """current_deg बाट target_deg सम्मको shortest signed angle (-180..+180)."""
    return ((target_deg - current_deg + 180.0) % 360.0) - 180.0


def find_moon_degree_crossing(start_dt, end_dt, target_deg, iterations=35):
    """[start_dt, end_dt] भित्र चन्द्रमा target_deg पार गर्ने सटीक समय (bisection)."""
    lo, hi = start_dt, end_dt
    for _ in range(iterations):
        mid = lo + (hi - lo) / 2
        mid_lon = _moon_sidereal_lon(mid)
        diff = _angular_diff_signed(mid_lon, target_deg)
        if diff >= 0:
            lo = mid
        else:
            hi = mid
    return lo + (hi - lo) / 2


# ==================================================
# PANCHANG ASTROLOGICAL CALCULATIONS (AT SUNRISE)
# ==================================================

def calculate_panchang_details(sunrise_dt):
    if sunrise_dt is None:
        return {
            "tithi": "--:--",
            "paksha": "--:--",
            "nakshatra": "--:--",
            "yoga": "--:--",
            "karana": "--:--",
            "moonSign": "--:--",
            "planetPositions": {},
        }

    jd_ut = to_julian_day(sunrise_dt)
    planets = get_planet_positions(jd_ut)

    sun_sid = planets["सूर्य"]["longitude"]
    moon_sid = planets["चन्द्र"]["longitude"] if "चन्द्र" in planets else (
        swe.calc_ut(jd_ut, swe.MOON, SIDEREAL_FLAGS)[0][0] % 360.0
    )

    diff = (moon_sid - sun_sid) % 360.0
    tithi_idx = min(int(diff / 12.0), 29)
    paksha = "शुक्ल" if tithi_idx < 15 else "कृष्ण"
    tithi_name = TITHI_NAMES[tithi_idx]

    nak_idx = min(int(moon_sid / (360.0 / 27.0)), 26)
    nakshatra_name = NAKSHATRA_NAMES[nak_idx]

    yog_idx = min(int(((sun_sid + moon_sid) % 360.0) / (360.0 / 27.0)), 26)
    yog_name = YOG_NAMES[yog_idx]

    half_tithi = min(int(diff / 6.0), 59)
    if half_tithi == 0:
        karan_name = "किंस्तुघ्न"
    elif 1 <= half_tithi <= 56:
        karan_name = KARAN_MOVABLE[(half_tithi - 1) % 7]
    elif half_tithi == 57:
        karan_name = "शकुनि"
    elif half_tithi == 58:
        karan_name = "चतुष्पाद"
    else:
        karan_name = "नाग"

    rashi_idx = min(int(moon_sid / 30.0), 11)
    moon_sign_name = RASHI_NAMES[rashi_idx]

    return {
        "tithi": tithi_name,
        "paksha": paksha,
        "nakshatra": nakshatra_name,
        "yoga": yog_name,
        "karana": karan_name,
        "moonSign": moon_sign_name,
        "planetPositions": planets,
    }


# ==================================================
# RAHU KAAL, MUHURTAS & CHOGHADIYA
# ==================================================

def get_rahu_kaal(ad_date, sunrise, sunset):
    if sunrise is None or sunset is None:
        return None
    daylight_seconds = (sunset - sunrise).total_seconds()
    if daylight_seconds <= 0:
        return None
    segment_seconds = daylight_seconds / 8
    segment_number = RAHU_SEGMENTS[ad_date.weekday()]
    start = sunrise + dt.timedelta(seconds=segment_seconds * (segment_number - 1))
    end = sunrise + dt.timedelta(seconds=segment_seconds * segment_number)
    return f"{format_time(start)} - {format_time(end)}"


def generate_muhurtas(ad_date, sunrise, sunset, next_sunrise=None):
    if sunrise is None or sunset is None:
        return [], []

    solar_noon = sunrise + (sunset - sunrise) / 2

    # शास्त्रीय निशिता मुहूर्त: रात्रि अवधिको मध्यबिन्दु (±24 मिनेट)
    if next_sunrise is not None and next_sunrise > sunset:
        night_mid = sunset + (next_sunrise - sunset) / 2
    else:
        night_mid = solar_noon + dt.timedelta(hours=12)

    nishita_start = night_mid - dt.timedelta(minutes=24)
    nishita_end = night_mid + dt.timedelta(minutes=24)

    # वर्तमान नक्षत्रको सटीक सुरु र अन्त्य समय (root-finding)
    moon_pos = _moon_sidereal_lon(sunrise)
    nak_len = 360.0 / 27.0
    nak_idx = min(int(moon_pos / nak_len), 26)

    nak_start_deg = (nak_idx * nak_len) % 360.0
    nak_end_deg = ((nak_idx + 1) * nak_len) % 360.0

    nak_start_dt = find_moon_degree_crossing(
        sunrise - dt.timedelta(hours=30),
        sunrise + dt.timedelta(hours=2),
        nak_start_deg,
    )
    nak_end_dt = find_moon_degree_crossing(
        sunrise - dt.timedelta(hours=2),
        sunrise + dt.timedelta(hours=36),
        nak_end_deg,
    )

    nak_duration_sec = max((nak_end_dt - nak_start_dt).total_seconds(), 1.0)
    ghati_sec = nak_duration_sec / 60.0

    varjyam_start_dt = nak_start_dt + dt.timedelta(seconds=VARJYAM_GHATI[nak_idx] * ghati_sec)
    varjyam_end_dt = varjyam_start_dt + dt.timedelta(seconds=4 * ghati_sec)

    amrit_start_dt = nak_start_dt + dt.timedelta(seconds=AMRIT_GHATI[nak_idx] * ghati_sec)
    amrit_end_dt = amrit_start_dt + dt.timedelta(seconds=4 * ghati_sec)

    shubh_samay = [
        {
            "name": "ब्रह्म मुहूर्त",
            "from": format_time(sunrise - dt.timedelta(hours=1, minutes=50)),
            "to": format_time(sunrise - dt.timedelta(hours=1, minutes=2)),
        },
        {
            "name": "प्रातः सन्ध्या",
            "from": format_time(sunrise - dt.timedelta(minutes=45)),
            "to": format_time(sunrise),
        },
        {
            "name": "अभिजित मुहूर्त",
            "from": format_time(solar_noon - dt.timedelta(minutes=24)),
            "to": format_time(solar_noon + dt.timedelta(minutes=24)),
        },
        {
            "name": "विजय मुहूर्त",
            "from": format_time(solar_noon + dt.timedelta(hours=1, minutes=40)),
            "to": format_time(solar_noon + dt.timedelta(hours=2, minutes=26)),
        },
        {
            "name": "गोधूलि मुहूर्त",
            "from": format_time(sunset - dt.timedelta(minutes=24)),
            "to": format_time(sunset + dt.timedelta(minutes=24)),
        },
        {
            "name": "सायाह्न सन्ध्या",
            "from": format_time(sunset),
            "to": format_time(sunset + dt.timedelta(minutes=45)),
        },
        {
            "name": "निशिता मुहूर्त",
            "from": format_time(nishita_start),
            "to": format_time(nishita_end),
        },
        {
            "name": "अमृत काल",
            "from": format_time(amrit_start_dt),
            "to": format_time(amrit_end_dt),
        },
    ]

    ashubh_samay = [
        {
            "name": "दुर्मुहूर्त",
            "from": format_time(solar_noon + dt.timedelta(minutes=30)),
            "to": format_time(solar_noon + dt.timedelta(minutes=61)),
        },
        {
            "name": "वर्ज्यम्",
            "from": format_time(varjyam_start_dt),
            "to": format_time(varjyam_end_dt),
        },
        {
            "name": "दुर्मुहूर्त",
            "from": format_time(solar_noon + dt.timedelta(hours=1, minutes=30)),
            "to": format_time(solar_noon + dt.timedelta(hours=2)),
        },
    ]

    return shubh_samay, ashubh_samay


def generate_choghadiya(ad_date, sunrise, sunset, next_sunrise=None):
    if sunrise is None or sunset is None:
        return [], []

    weekday = ad_date.weekday()
    day_phals = choghadiya_sequence(DAY_START[weekday])
    night_phals = choghadiya_sequence(NIGHT_START[weekday])

    day_sec = (sunset - sunrise).total_seconds() / 8.0
    if next_sunrise is not None and next_sunrise > sunset:
        night_sec = (next_sunrise - sunset).total_seconds() / 8.0
    else:
        night_sec = (dt.timedelta(hours=24) - (sunset - sunrise)).total_seconds() / 8.0

    khandas = ["प्रथम", "द्वितीय", "तृतीय", "चतुर्थ", "पञ्चम", "षष्ठम", "सप्तम", "अष्टम"]

    din_choghadiya = []
    current_time = sunrise
    for i, khanda in enumerate(khandas):
        next_time = current_time + dt.timedelta(seconds=day_sec)
        din_choghadiya.append({
            "khanda": khanda,
            "from": format_time(current_time),
            "to": format_time(next_time),
            "phal": day_phals[i],
        })
        current_time = next_time

    ratri_choghadiya = []
    current_time = sunset
    for i, khanda in enumerate(khandas):
        next_time = current_time + dt.timedelta(seconds=night_sec)
        ratri_choghadiya.append({
            "khanda": khanda,
            "from": format_time(current_time),
            "to": format_time(next_time),
            "phal": night_phals[i],
        })
        current_time = next_time

    return din_choghadiya, ratri_choghadiya


# ==================================================
# BS YEAR DATE ITERATION & TRANSIT DETECTION
# ==================================================

def get_bs_dates(bs_year):
    current = nepali_datetime.date(bs_year, 1, 1)
    dates = []
    while current.year == bs_year:
        dates.append(current)
        current += dt.timedelta(days=1)
    if not dates:
        raise ValueError(f"No dates found for BS year {bs_year}")
    return dates


def detect_transit_events(data_list):
    """दैनिक planetPositions तुलना गरेर कुन BS मितिमा कुन ग्रहले राशि बदल्यो पत्ता लगाउँछ।"""
    events = []
    if not data_list:
        return events

    prev_positions = data_list[0].get("planetPositions", {})
    for day_record in data_list[1:]:
        curr_positions = day_record.get("planetPositions", {})
        for planet_name, curr_info in curr_positions.items():
            prev_info = prev_positions.get(planet_name)
            if prev_info and prev_info["rashiIndex"] != curr_info["rashiIndex"]:
                events.append({
                    "bsDate": f"{day_record['year']}-{day_record['month']:02d}-{day_record['day']:02d}",
                    "month": day_record["month"],
                    "day": day_record["day"],
                    "ad": day_record["ad"],
                    "planet": planet_name,
                    "fromRashi": prev_info["rashi"],
                    "toRashi": curr_info["rashi"],
                    "isRetrograde": curr_info["isRetrograde"],
                })
        prev_positions = curr_positions

    return events


# ==================================================
# DAILY & FULL YEAR JSON GENERATOR
# ==================================================

def generate_day(bs_date, next_ad_date=None):
    ad_date = bs_date.to_datetime_date()
    if next_ad_date is None:
        next_ad_date = ad_date + dt.timedelta(days=1)

    sunrise, sunset = get_sun_times(ad_date)
    next_sunrise, _ = get_sun_times(next_ad_date)
    moonrise, moonset = get_moon_times(ad_date)
    rahu = get_rahu_kaal(ad_date, sunrise, sunset)

    panchang = calculate_panchang_details(sunrise)
    shubh, ashubh = generate_muhurtas(ad_date, sunrise, sunset, next_sunrise)
    din_chog, ratri_chog = generate_choghadiya(ad_date, sunrise, sunset, next_sunrise)

    return {
        "year": bs_date.year,
        "month": bs_date.month,
        "day": bs_date.day,
        "ad": ad_date.strftime("%Y-%m-%d"),
        **panchang,
        "sunrise": format_time(sunrise),
        "sunset": format_time(sunset),
        "moonrise": format_time(moonrise),
        "moonset": format_time(moonset),
        "rahuKaal": rahu,
        "dinChoghadiya": din_chog,
        "ratriChoghadiya": ratri_chog,
        "shubhSamay": shubh,
        "ashubhSamay": ashubh,
    }


def generate_year(bs_year):
    print(f"\nविक्रम संवत् {bs_year} को पञ्चाङ्ग र गोचर डेटा तयार गर्दैछ (Lahiri Ayanamsa)...")

    bs_dates = get_bs_dates(bs_year)
    data_list = []

    for index, bs_date in enumerate(bs_dates):
        next_ad_date = (
            bs_dates[index + 1].to_datetime_date()
            if index + 1 < len(bs_dates)
            else (bs_date + dt.timedelta(days=1)).to_datetime_date()
        )
        record = generate_day(bs_date, next_ad_date)
        data_list.append(record)
        if (index + 1) % 30 == 0 or (index + 1) == len(bs_dates):
            print(f"प्रगति: {index + 1}/{len(bs_dates)} दिनहरू प्रशोधन भयो...")

    transit_events = detect_transit_events(data_list)

    output = {
        "year": bs_year,
        "transitEvents": transit_events,
        "data": data_list,
    }

    filename = f"panchang_{bs_year}.json"
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(output, file, ensure_ascii=False, indent=4)

    print(
        f"\nसफलतापूर्वक फाइल तयार भयो: {filename} "
        f"(कुल दिन: {len(data_list)}, गोचर परिवर्तन: {len(transit_events)})"
    )


# ==================================================
# COMMAND LINE
# ==================================================

def main():
    parser = argparse.ArgumentParser(
        description="Kathmandu Panchang & Transit JSON Generator (Lahiri Ayanamsa)"
    )
    parser.add_argument("year", nargs="?", type=int, help="Bikram Sambat year, e.g. 2083")

    args = parser.parse_args()

    if args.year is None:
        parser.error("कृपया विक्रम संवत् वर्ष दिनुहोस् (उदाहरण: python3 panchang.py 2083)")

    try:
        generate_year(args.year)
    except Exception as error:
        print(f"\nERROR: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()