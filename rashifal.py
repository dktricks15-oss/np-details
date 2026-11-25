#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path

NEPALI_DIGITS_MAP = str.maketrans("0123456789", "०१२३४५६७८९")

RASHI_NAMES = [
    "मेष", "वृष", "मिथुन", "कर्कट", "सिंह", "कन्या",
    "तुला", "वृश्चिक", "धनु", "मकर", "कुम्भ", "मीन",
]

MONTH_NAMES = {
    1: "बैशाख", 2: "जेठ", 3: "असार", 4: "श्रावण",
    5: "भाद्र", 6: "आश्विन", 7: "कार्तिक", 8: "मङ्सिर",
    9: "पौष", 10: "माघ", 11: "फाल्गुन", 12: "चैत",
}

RASHI_META = {
    "मेष": {"lord": "मङ्गल", "color": "रातो", "number": 9, "remedy": "मङ्गलबार हनुमानजी वा गणेशजीको पूजा र शनिबार पीपलमा जल चढाउनु शुभ मानिन्छ।"},
    "वृष": {"lord": "शुक्र", "color": "सेतो वा गुलाबी", "number": 6, "remedy": "शुक्रबार देवी वा महालक्ष्मीको आराधना र सेतो वस्तुको दान गर्नु लाभदायी मानिन्छ।"},
    "मिथुन": {"lord": "बुध", "color": "हरियो", "number": 5, "remedy": "बुधबार विष्णु वा गणेशजीको पूजा र हरियो वस्तुको सेवा गर्नु शुभ मानिन्छ।"},
    "कर्कट": {"lord": "चन्द्र", "color": "सेतो वा क्रिम", "number": 2, "remedy": "सोमबार शिवजीको आराधना र जलाभिषेक गर्नु मनको शान्तिका लागि राम्रो मानिन्छ।"},
    "सिंह": {"lord": "सूर्य", "color": "सुनौलो वा सुन्तला", "number": 1, "remedy": "आइतबार सूर्यदेवको स्मरण र अनुशासनमा जोड दिनु लाभदायी मानिन्छ।"},
    "कन्या": {"lord": "बुध", "color": "हरियो", "number": 5, "remedy": "बुधबार अध्ययन, सेवा र गणेशजीको उपासना गर्नु शुभ मानिन्छ।"},
    "तुला": {"lord": "शुक्र", "color": "सेतो वा हल्का निलो", "number": 6, "remedy": "शुक्रबार सन्तुलन, कला र देवीको स्मरण गर्नु अनुकूल मानिन्छ।"},
    "वृश्चिक": {"lord": "मङ्गल", "color": "गाढा रातो वा मरुन", "number": 9, "remedy": "मङ्गलबार हनुमानजीको स्मरण र धैर्यपूर्वक निर्णय गर्नु हितकर मानिन्छ।"},
    "धनु": {"lord": "बृहस्पति", "color": "पहेंलो", "number": 3, "remedy": "बिहीबार गुरु वा विष्णुको पूजा र पहेंलो वस्तुको दान गर्नु शुभ मानिन्छ।"},
    "मकर": {"lord": "शनि", "color": "कालो वा गाढा निलो", "number": 8, "remedy": "शनिबार परिश्रम, अनुशासन र पीपल वा शिवजीको स्मरण गर्नु शुभ मानिन्छ।"},
    "कुम्भ": {"lord": "शनि", "color": "आकाशी वा गाढा निलो", "number": 8, "remedy": "शनिबार सामाजिक सेवा, धैर्य र नियमित दिनचर्या अपनाउनु लाभदायी मानिन्छ।"},
    "मीन": {"lord": "बृहस्पति", "color": "पहेंलो वा सुनौलो", "number": 3, "remedy": "बिहीबार गुरु, अध्ययन र सत्सङ्गमा समय दिनु शुभ मानिन्छ।"},
}

BHAVA_RULES = {
    "बृहस्पति": {
        1: "आत्मविश्वास र व्यक्तित्वमा निखार आउन सक्छ, तर स्वास्थ्य र खानपानमा सन्तुलन राख्नुहोस्।",
        2: "आर्थिक पक्ष र वाणीमा सुधार देखिन्छ; बचत तथा परिवारको सल्लाह उपयोगी रहन्छ।",
        3: "प्रयासअनुसार नतिजा आउन केही समय लाग्न सक्छ; धैर्य र निरन्तरता राख्नुहोस्।",
        4: "घर-परिवार र सम्पत्तिसम्बन्धी निर्णयमा सोचविचार र संयम आवश्यक छ।",
        5: "अध्ययन, सन्तान र सिर्जनशील कामका लागि अनुकूल तथा उत्साहजनक समय देखिन्छ।",
        6: "प्रतिस्पर्धा र ऋण/खर्च व्यवस्थापनमा ध्यान दिनुपर्ने समय छ।",
        7: "साझेदारी, यात्रा र सम्बन्धमा समझदारी बढाउनुपर्ने अवस्था आउन सक्छ।",
        8: "आकस्मिक खर्च वा उतारचढाव देखिन सक्छ; जोखिमपूर्ण निर्णय टार्नुहोस्।",
        9: "भाग्य, धर्म, उच्च शिक्षा र टाढाको यात्राका लागि सकारात्मक सङ्केत देखिन्छ।",
        10: "कर्मक्षेत्र, पदोन्नति र जिम्मेवारीमा प्रगति हुने सम्भावना बलियो छ।",
        11: "आम्दानी, लाभ र इच्छापूर्तिका अवसरहरू खुल्न सक्छन्।",
        12: "खर्च, विश्राम र आध्यात्मिक चिन्तनमा ध्यान दिनुपर्ने समय छ।",
    },
    "शनि": {
        1: "आत्ममूल्याङ्कन, अनुशासन र धैर्यको परीक्षा हुने समय छ; थकानबाट जोगिनुहोस्।",
        2: "आर्थिक व्यवहार, बोली र पारिवारिक दायित्वमा सतर्कता अपनाउनुहोस्।",
        3: "परिश्रम र साहसले काम बन्ने सङ्केत छ; छोटो यात्रा हुन सक्छ।",
        4: "घरायसी सुख, आराम र सम्पत्तिसम्बन्धी विषयमा केही ढिलासुस्ती आउन सक्छ।",
        5: "अध्ययन, लगानी र सन्तानका विषयमा हतार नगरी योजनाबद्ध अघि बढ्नुहोस्।",
        6: "विरोधी वा चुनौतीमाथि नियन्त्रण राख्न सकिन्छ; स्वास्थ्यमा नियमित ध्यान दिनुहोस्।",
        7: "व्यापारिक साझेदारी र दाम्पत्य/सम्बन्धमा स्पष्टता र धैर्य चाहिन्छ।",
        8: "अढैया/उतारचढावको प्रभावले मानसिक दबाब वा ढिलाइ ल्याउन सक्छ; सावधान रहनुहोस्।",
        9: "कामको गति केही सुस्त देखिए पनि दीर्घकालीन योजना बलियो बनाउन सकिन्छ।",
        10: "कर्मक्षेत्रमा कडा मेहनतको माग छ; जिम्मेवारी पूरा गर्दा प्रतिष्ठा बढ्छ।",
        11: "निरन्तरको मिहिनेतबाट लाभ र स्थिरता मिल्ने सम्भावना रहन्छ।",
        12: "साढेसातीको प्रभावले खर्च, थकान र यात्रामा सतर्कता आवश्यक देखिन्छ।",
    },
    "राहु": {
        3: "साहस, सञ्चार र नयाँ प्रयासमा सक्रियता बढ्न सक्छ।",
        6: "प्रतिस्पर्धा र कामको चाप बढे पनि समस्या समाधान गर्ने क्षमता देखिन्छ।",
        10: "कर्मक्षेत्रमा नयाँ अवसरसँगै उतारचढाव आउन सक्छ; सोझो र पारदर्शी बाटो अपनाउनुहोस्।",
        11: "आकस्मिक लाभ, नेटवर्क विस्तार र इच्छापूर्तिको योग बन्न सक्छ।",
    },
    "केतु": {
        3: "अनावश्यक दौडधुप घटाएर मुख्य काममा केन्द्रित हुनु लाभदायी हुन्छ।",
        4: "घर-परिवार र मनको शान्तिमा ध्यान दिनुपर्ने समय छ।",
        5: "अध्ययन वा निर्णयमा एकाग्रता कमजोर हुन सक्छ; ध्यान र अभ्यास उपयोगी हुन्छ।",
        9: "परम्परा, अध्ययन र भित्री स्पष्टतामा रुचि बढ्न सक्छ।",
    },
    "सूर्य": {
        1: "आत्मबल र नेतृत्व क्षमता बढ्न सक्छ; रिस र अहङ्कारबाट बच्नुहोस्।",
        3: "काममा जोश र आत्मविश्वास बढ्ने समय छ।",
        6: "चुनौती पार गर्दै कार्यक्षेत्रमा अघि बढ्न सकिने सङ्केत छ।",
        10: "मान-सम्मान, सरकारी/प्रशासनिक काम र करियरमा सकारात्मक गति देखिन सक्छ।",
        11: "आम्दानी र उच्च व्यक्तिहरूसँगको सहकार्यबाट फाइदा हुन सक्छ।",
    },
    "मङ्गल": {
        3: "पराक्रम र काम गर्ने ऊर्जा बढ्छ, तर हतार र रिसमा नियन्त्रण राख्नुहोस्।",
        6: "कामको गति तीव्र रहन्छ; चोटपटक र तनावबाट जोगिनुहोस्।",
        10: "कार्यक्षेत्रमा सक्रियता बढ्छ; विवाद नगरी लक्ष्यमा ध्यान दिनुहोस्।",
        11: "आर्थिक प्रयासमा गति आउन सक्छ; खर्चमा पनि ध्यान दिनुहोस्।",
    },
    "चन्द्र": {
        1: "मन प्रसन्न र सक्रिय रहन सक्छ; निर्णयमा भावनात्मक नबन्नुहोस्।",
        3: "छोटो यात्रा, भेटघाट र काममा उत्साह बढ्न सक्छ।",
        4: "घरपरिवार र आराममा समय बित्न सक्छ; मनको शान्तिमा ध्यान दिनुहोस्।",
        6: "दैनिक काममा व्यस्तता बढ्न सक्छ; खानपान र स्वास्थ्यमा ख्याल राख्नुहोस्।",
        8: "अनावश्यक चिन्ता वा खर्चबाट जोगिनुहोस्; धैर्यपूर्वक काम गर्नुहोस्।",
        10: "कार्यक्षेत्रमा जिम्मेवारी र सक्रियता बढ्ने सङ्केत छ।",
        11: "आम्दानी, सहयोग र राम्रो खबर सुन्न पाइने सम्भावना रहन्छ।",
        12: "खर्च, थकान वा निद्रामा गडबडी आउन सक्छ; विश्राममा ध्यान दिनुहोस्।",
    },
}


def to_nepali_digits(text):
    return str(text).translate(NEPALI_DIGITS_MAP)


def get_bhava(rashi_idx: int, planet_rashi_idx: int) -> int:
    return ((planet_rashi_idx - rashi_idx) % 12) + 1


def describe_planet_bhava(planet: str, bhava: int) -> str:
    planet_rules = BHAVA_RULES.get(planet, {})
    if bhava in planet_rules:
        return f"{planet} ({bhava}औँ भाव): {planet_rules[bhava]}"
    if bhava in (1, 5, 9, 10, 11):
        return f"{planet} ({bhava}औँ भाव): समग्रमा अनुकूल र सहयोगी प्रभाव रहने सङ्केत छ।"
    if bhava in (3, 6):
        return f"{planet} ({bhava}औँ भाव): परिश्रम र सतर्कतासहित अघि बढ्दा सकारात्मक नतिजा आउन सक्छ।"
    return f"{planet} ({bhava}औँ भाव): खर्च, तनाव वा ढिलासुस्तीप्रति सचेत रहनुपर्ने समय छ।"


def format_bs_date(day_record: dict) -> str:
    return f"{day_record['year']}-{day_record['month']:02d}-{day_record['day']:02d}"


def generate_daily_rashifal(rashi_idx: int, day_record: dict) -> dict:
    bs_str = format_bs_date(day_record)
    moon_sign = day_record.get("moonSign")
    moon_bhava = (
        get_bhava(rashi_idx, RASHI_NAMES.index(moon_sign))
        if moon_sign in RASHI_NAMES else None
    )

    positions = day_record.get("planetPositions", {})
    highlights = []
    if moon_bhava is not None:
        highlights.append(describe_planet_bhava("चन्द्र", moon_bhava))

    for major_planet in ("बृहस्पति", "शनि", "राहु", "केतु", "सूर्य", "मङ्गल"):
        p_info = positions.get(major_planet)
        if p_info:
            bhava = get_bhava(rashi_idx, p_info["rashiIndex"])
            highlights.append(describe_planet_bhava(major_planet, bhava))

    return {
        "bsDate": bs_str,
        "month": day_record["month"],
        "monthName": MONTH_NAMES.get(day_record["month"], ""),
        "day": day_record["day"],
        "ad": day_record["ad"],
        "moonSign": moon_sign,
        "moonBhava": moon_bhava,
        "highlights": highlights,
    }


def generate_weekly_rashifal(rashi_name: str, rashi_idx: int, days: list, transit_events: list) -> list:
    weeks = []
    for idx in range(0, len(days), 7):
        chunk = days[idx:idx + 7]
        if not chunk:
            continue
        week_num = (idx // 7) + 1
        start_rec = chunk[0]
        end_rec = chunk[-1]
        mid_rec = chunk[len(chunk) // 2]

        ad_set = {d["ad"] for d in chunk}
        week_transits = [ev for ev in transit_events if ev.get("ad") in ad_set]
        transit_notes = []
        for ev in week_transits:
            new_bhava = get_bhava(rashi_idx, RASHI_NAMES.index(ev["toRashi"]))
            retro_text = " (वक्री)" if ev.get("isRetrograde") else ""
            transit_notes.append(
                f"{ev['bsDate']} मा {ev['planet']}{retro_text} {ev['fromRashi']} बाट {ev['toRashi']} ({new_bhava}औँ भाव) मा प्रवेश।"
            )

        moon_bhavas = []
        for d in chunk:
            ms = d.get("moonSign")
            if ms in RASHI_NAMES:
                mb = get_bhava(rashi_idx, RASHI_NAMES.index(ms))
                if not moon_bhavas or moon_bhavas[-1] != mb:
                    moon_bhavas.append(mb)

        mid_positions = mid_rec.get("planetPositions", {})
        highlights = []
        for major_planet in ("बृहस्पति", "शनि", "राहु", "केतु", "सूर्य", "मङ्गल"):
            p_info = mid_positions.get(major_planet)
            if p_info:
                bhava = get_bhava(rashi_idx, p_info["rashiIndex"])
                highlights.append(describe_planet_bhava(major_planet, bhava))

        weeks.append({
            "week": week_num,
            "bsRange": f"{format_bs_date(start_rec)} देखि {format_bs_date(end_rec)}",
            "adRange": f"{start_rec['ad']} देखि {end_rec['ad']}",
            "moonBhavas": moon_bhavas,
            "transits": transit_notes,
            "highlights": highlights,
        })
    return weeks


def generate_monthly_rashifal(rashi_idx: int, month: int, month_days: list, month_transits: list) -> dict:
    first_day = month_days[0]
    mid_day = month_days[len(month_days) // 2]
    last_day = month_days[-1]

    ref_positions = mid_day.get("planetPositions", {})
    highlights = []
    for major_planet in ("बृहस्पति", "शनि", "राहु", "केतु", "सूर्य", "मङ्गल"):
        p_info = ref_positions.get(major_planet)
        if p_info:
            bhava = get_bhava(rashi_idx, p_info["rashiIndex"])
            highlights.append(describe_planet_bhava(major_planet, bhava))

    transit_notes = []
    for ev in month_transits:
        new_bhava = get_bhava(rashi_idx, RASHI_NAMES.index(ev["toRashi"]))
        retro_text = " (वक्री)" if ev.get("isRetrograde") else ""
        transit_notes.append(
            f"{ev['bsDate']} मा {ev['planet']}{retro_text} {ev['fromRashi']} बाट {ev['toRashi']} ({new_bhava}औँ भाव) मा प्रवेश।"
        )

    return {
        "month": month,
        "monthName": MONTH_NAMES[month],
        "bsRange": f"{format_bs_date(first_day)} देखि {format_bs_date(last_day)}",
        "adRange": f"{first_day['ad']} देखि {last_day['ad']}",
        "transits": transit_notes,
        "highlights": highlights,
    }


def generate_rashi_report(rashi_name: str, year: int, days: list, transit_events: list, period: str) -> dict:
    rashi_idx = RASHI_NAMES.index(rashi_name)
    meta = RASHI_META[rashi_name]

    major_transits = [
        ev for ev in transit_events
        if ev["planet"] in ("बृहस्पति", "शनि", "राहु", "केतु")
    ]

    first_pos = days[0].get("planetPositions", {}) if days else {}
    saturn_bhava = (
        get_bhava(rashi_idx, first_pos["शनि"]["rashiIndex"])
        if "शनि" in first_pos else None
    )
    jupiter_bhava = (
        get_bhava(rashi_idx, first_pos["बृहस्पति"]["rashiIndex"])
        if "बृहस्पति" in first_pos else None
    )

    overview_parts = [
        f"वि.सं. {year} मा {rashi_name} राशिका लागि समग्रमा गोचर र भावअनुसार सन्तुलित तथा सतर्कता अपनाउनुपर्ने समय देखिन्छ।"
    ]
    if saturn_bhava == 12:
        overview_parts.append("वर्षको सुरुवातमा शनि १२औँ भावमा रहेकाले खर्च, थकान र काममा ढिलासुस्तीप्रति ध्यान दिनुहोस्।")
    elif saturn_bhava == 1:
        overview_parts.append("शनिको प्रभावले धैर्य, अनुशासन र नियमित दिनचर्यामा जोड दिनुपर्ने देखिन्छ।")
    if jupiter_bhava:
        overview_parts.append(f"वर्षको प्रारम्भमा बृहस्पति {jupiter_bhava}औँ भावमा रहँदा सोहीअनुसार योजना र निर्णय लिनु लाभदायी हुन्छ।")

    report = {
        "rashi": rashi_name,
        "year": year,
        "lord": meta["lord"],
        "luckyColor": meta["color"],
        "luckyNumber": meta["number"],
        "remedy": meta["remedy"],
    }

    if period in ("yearly", "all"):
        report["yearly"] = {
            "overview": " ".join(overview_parts),
            "majorPlanetTransits": [
                f"{ev['bsDate']}: {ev['planet']} ({ev['fromRashi']} -> {ev['toRashi']}, {get_bhava(rashi_idx, RASHI_NAMES.index(ev['toRashi']))}औँ भाव)"
                for ev in major_transits
            ],
        }

    if period in ("monthly", "all"):
        months_output = []
        for month in range(1, 13):
            month_days = [d for d in days if d["month"] == month]
            if not month_days:
                continue
            month_transits = [ev for ev in transit_events if ev["month"] == month]
            months_output.append(
                generate_monthly_rashifal(rashi_idx, month, month_days, month_transits)
            )
        report["monthly"] = months_output

    if period in ("weekly", "all"):
        report["weekly"] = generate_weekly_rashifal(rashi_name, rashi_idx, days, transit_events)

    if period in ("daily", "all"):
        report["daily"] = [generate_daily_rashifal(rashi_idx, d) for d in days]

    return report


def build_markdown(year: int, reports: list, period: str) -> str:
    lines = [f"# राशिफल ({period}) — वि.सं. {year}\n"]
    for rep in reports:
        lines.append(f"## {rep['rashi']} (स्वामी: {rep['lord']})\n")
        lines.append(f"- **शुभ रङ्ग:** {rep['luckyColor']} | **शुभ अङ्क:** {to_nepali_digits(rep['luckyNumber'])}")
        lines.append(f"- **उपाय/सुझाव:** {rep['remedy']}\n")

        if "yearly" in rep:
            y = rep["yearly"]
            lines.append("### वार्षिक राशिफल")
            lines.append(f"{y['overview']}\n")
            if y["majorPlanetTransits"]:
                lines.append("#### प्रमुख गोचर परिवर्तन (बृहस्पति, शनि, राहु, केतु)")
                for item in y["majorPlanetTransits"]:
                    lines.append(f"- {item}")
                lines.append("")

        if "monthly" in rep:
            lines.append("### महिनागत राशिफल")
            for m in rep["monthly"]:
                lines.append(f"#### {m['monthName']} ({m['bsRange']} / {m['adRange']})")
                for t in m["transits"]:
                    lines.append(f"- *गोचर:* {t}")
                for h in m["highlights"][:4]:
                    lines.append(f"- {h}")
                lines.append("")

        if "weekly" in rep:
            lines.append("### साप्ताहिक राशिफल")
            for w in rep["weekly"]:
                bhava_str = ", ".join(f"{b}औँ" for b in w["moonBhavas"])
                lines.append(f"#### हप्ता {to_nepali_digits(w['week'])} ({w['bsRange']} | चन्द्र भाव: {bhava_str})")
                for t in w["transits"]:
                    lines.append(f"- *गोचर:* {t}")
                for h in w["highlights"][:3]:
                    lines.append(f"- {h}")
                lines.append("")

        if "daily" in rep:
            lines.append("### दैनिक राशिफल")
            for d in rep["daily"]:
                lines.append(f"#### {d['bsDate']} ({d['ad']}) — चन्द्र राशि: {d['moonSign']} ({d['moonBhava']}औँ भाव)")
                for h in d["highlights"][:3]:
                    lines.append(f"- {h}")
                lines.append("")

        lines.append("---\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate daily, weekly, monthly, and yearly Rashifal from Panchang JSON without external APIs"
    )
    parser.add_argument("panchang_json", help="Path to panchang_<year>.json")
    parser.add_argument("--rashi", help="Optional single rashi in Nepali, e.g. मेष")
    parser.add_argument(
        "--period",
        choices=["daily", "weekly", "monthly", "yearly", "all"],
        default="all",
        help="Period type to generate (default: all)",
    )
    parser.add_argument("--out-json", default="rashifal_output.json", help="Output JSON filename")
    parser.add_argument("--out-md", default="rashifal_output.md", help="Output Markdown filename")

    args = parser.parse_args()
    input_path = Path(args.panchang_json)
    if not input_path.exists():
        print(f"ERROR: फाइल भेटिएन: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        panchang_data = json.load(f)

    year = panchang_data.get("year", 2083)
    days = panchang_data.get("data", [])
    transit_events = panchang_data.get("transitEvents", [])

    target_rashis = [args.rashi] if args.rashi else RASHI_NAMES
    for r in target_rashis:
        if r not in RASHI_NAMES:
            print(f"ERROR: अमान्य राशि नाम '{r}'। मान्य नामहरू: {', '.join(RASHI_NAMES)}", file=sys.stderr)
            sys.exit(1)

    reports = [
        generate_rashi_report(rashi, year, days, transit_events, args.period)
        for rashi in target_rashis
    ]

    with open(args.out_json, "w", encoding="utf-8") as f:
        json.dump({"year": year, "period": args.period, "rashifal": reports}, f, ensure_ascii=False, indent=2)

    with open(args.out_md, "w", encoding="utf-8") as f:
        f.write(build_markdown(year, reports, args.period))

    print(f"सफलतापूर्वक तयार भयो: {args.out_json} र {args.out_md} (period={args.period})")


if __name__ == "__main__":
    main()