"""Zone 1 dataset generator for Indian regional dishes.

This version normalizes the exported CSVs to the requested schema:
- English regional aliases
- gi_status / gi_tag_details set to NA when no GI tag exists
- cooking_method uses short category labels
- ingredients, community identity, and dish image URL are always populated
- occasional dishes keep consumption_time empty
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests


PROJECT_ROOT = Path(__file__).resolve().parent
BASE_DISH_CSV = PROJECT_ROOT / "base_dish.csv"
VARIANTS_CSV = PROJECT_ROOT / "dish_variants.csv"

REGION = "North"

ZONE_1_STATES = [
    "Rajasthan",
    "Punjab",
    "Haryana",
    "Himachal Pradesh",
    "Uttarakhand",
    "Uttar Pradesh",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Chandigarh",
]

STATE_CITIES = {
    "Rajasthan": ["Jaipur", "Jodhpur", "Udaipur", "Bikaner"],
    "Punjab": ["Amritsar", "Ludhiana", "Patiala", "Jalandhar"],
    "Haryana": ["Hisar", "Karnal", "Rohtak", "Kurukshetra"],
    "Himachal Pradesh": ["Shimla", "Kullu", "Mandi", "Dharamshala"],
    "Uttarakhand": ["Dehradun", "Nainital", "Almora", "Pauri"],
    "Uttar Pradesh": ["Lucknow", "Varanasi", "Agra", "Kanpur"],
    "Delhi": ["Old Delhi", "New Delhi", "Nizamuddin", "Chandni Chowk"],
    "Jammu and Kashmir": ["Srinagar", "Jammu", "Anantnag", "Baramulla"],
    "Ladakh": ["Leh", "Kargil", "Nubra", "Zanskar"],
    "Chandigarh": ["Sector 17", "Sector 22", "Manimajra", "Tricity"],
}

STATE_COMMUNITIES = {
    "Rajasthan": "Rajasthani",
    "Punjab": "Punjabi",
    "Haryana": "Haryanvi",
    "Himachal Pradesh": "Himachali",
    "Uttarakhand": "Garhwali/Kumaoni",
    "Uttar Pradesh": "Awadhi",
    "Delhi": "Delhite",
    "Jammu and Kashmir": "Kashmiri",
    "Ladakh": "Ladakhi",
    "Chandigarh": "Punjabi",
}

STYLE_OPTIONS = [
    {"name": "Home Style", "alias": "Home Style", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Street Style", "alias": "Street Style", "consumption_type": "everyday", "consumption_time": "snack", "occasion_description": ""},
    {"name": "Dhaba Style", "alias": "Dhaba Style", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Tawa Style", "alias": "Tawa Style", "consumption_type": "everyday", "consumption_time": "breakfast", "occasion_description": ""},
    {"name": "Tandoor Style", "alias": "Tandoor Style", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Family Thali", "alias": "Family Thali", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Weekend Special", "alias": "Weekend Special", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Village Plate", "alias": "Village Plate", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Packed Lunch", "alias": "Packed Lunch", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Late-Night Stall", "alias": "Late-Night Stall", "consumption_type": "everyday", "consumption_time": "snack", "occasion_description": ""},
    {"name": "Tea-Time Plate", "alias": "Tea-Time Plate", "consumption_type": "everyday", "consumption_time": "snack", "occasion_description": ""},
    {"name": "Winter Bowl", "alias": "Winter Bowl", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Summer Plate", "alias": "Summer Plate", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Smoky Pot", "alias": "Smoky Pot", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Crisp Skillet", "alias": "Crisp Skillet", "consumption_type": "everyday", "consumption_time": "snack", "occasion_description": ""},
    {"name": "Millet Bowl", "alias": "Millet Bowl", "consumption_type": "everyday", "consumption_time": "breakfast", "occasion_description": ""},
    {"name": "Picnic Pack", "alias": "Picnic Pack", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Monsoon Plate", "alias": "Monsoon Plate", "consumption_type": "everyday", "consumption_time": "snack", "occasion_description": ""},
    {"name": "Copper Pot Version", "alias": "Copper Pot Version", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Earth-Oven Batch", "alias": "Earth-Oven Batch", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Comfort Meal", "alias": "Comfort Meal", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Market Special", "alias": "Market Special", "consumption_type": "everyday", "consumption_time": "snack", "occasion_description": ""},
    {"name": "Soft Set", "alias": "Soft Set", "consumption_type": "everyday", "consumption_time": "breakfast", "occasion_description": ""},
    {"name": "Flaky Version", "alias": "Flaky Version", "consumption_type": "everyday", "consumption_time": "breakfast", "occasion_description": ""},
    {"name": "Rich Gravy Bowl", "alias": "Rich Gravy Bowl", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Travel-Friendly Pack", "alias": "Travel-Friendly Pack", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Rustic Bowl", "alias": "Rustic Bowl", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Festival Plate", "alias": "Festival Plate", "consumption_type": "occasional", "consumption_time": "", "occasion_description": "Prepared during regional festivals and family gatherings."},
    {"name": "Heritage Platter", "alias": "Heritage Platter", "consumption_type": "occasional", "consumption_time": "", "occasion_description": "Served as a heritage-style preparation on special occasions."},
    {"name": "Royal Spread", "alias": "Royal Spread", "consumption_type": "occasional", "consumption_time": "", "occasion_description": "Associated with ceremonial and royal-style meals."},
    {"name": "Family Feast", "alias": "Family Feast", "consumption_type": "occasional", "consumption_time": "", "occasion_description": "Prepared for family celebrations and large community meals."},
    {"name": "Courtyard Feast", "alias": "Courtyard Feast", "consumption_type": "occasional", "consumption_time": "", "occasion_description": "Prepared for courtyard gatherings and festive hosting."},
    {"name": "Heritage Bowl", "alias": "Heritage Bowl", "consumption_type": "occasional", "consumption_time": "", "occasion_description": "An old-style bowl served during commemorative feasts."},
    {"name": "Celebration Tray", "alias": "Celebration Tray", "consumption_type": "occasional", "consumption_time": "", "occasion_description": "A celebratory tray served during weddings or major festivals."},
    {"name": "Evening Snack", "alias": "Evening Snack", "consumption_type": "everyday", "consumption_time": "snack", "occasion_description": ""},
    {"name": "Lodge Meal", "alias": "Lodge Meal", "consumption_type": "everyday", "consumption_time": "dinner", "occasion_description": ""},
    {"name": "Soft Tiffin", "alias": "Soft Tiffin", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
    {"name": "Quick Serve", "alias": "Quick Serve", "consumption_type": "everyday", "consumption_time": "breakfast", "occasion_description": ""},
    {"name": "Courtyard Plate", "alias": "Courtyard Plate", "consumption_type": "everyday", "consumption_time": "lunch", "occasion_description": ""},
]

BASE_DISH_COLUMNS = [
    "dish_id",
    "base_dish_name",
    "regional_alias_name",
    "english_translated_name",
    "region",
    "state",
    "city_or_district",
    "community_identity",
    "gi_status",
    "gi_tag_details",
    "famousness_tier",
    "dish_type",
    "consumption_type",
    "consumption_time",
    "occasion_description",
    "cooking_method",
    "ingredients_used",
    "dish_image_url",
    "source_type",
    "source_url",
]

VARIANT_COLUMNS = [
    "dish_id",
    "variant_dish_name",
    "regional_alias_name",
    "english_translated_name",
    "region",
    "state",
    "city_or_district",
    "community_identity",
    "gi_status",
    "gi_tag_details",
    "famousness_tier",
    "dish_type",
    "consumption_type",
    "consumption_time",
    "occasion_description",
    "cooking_method",
    "ingredients_used",
    "dish_image_url",
    "source_type",
    "source_url",
]


def _source_type_for(source_url: str) -> str:
    if "wikipedia.org" in source_url:
        return "Wikipedia"
    return "web/official/food article"


@lru_cache(maxsize=None)
def _dish_image_url(source_url: str, dish_name: str) -> str:
    if "wikipedia.org/wiki/" in source_url:
        title = source_url.rsplit("/", 1)[-1]
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title, safe='')}"
        try:
            response = requests.get(api_url, timeout=5, headers={"accept": "application/json"})
            response.raise_for_status()
            thumbnail = response.json().get("thumbnail", {})
            image_url = thumbnail.get("source")
            if image_url:
                return image_url
        except Exception:
            pass

    return f"https://placehold.co/1200x800?text={quote(dish_name, safe='')}"


BASE_DISH_SPECS = {
    "Rajasthan": [
        {
            "dish_id": "Z1-RJ-01",
            "base_dish_name": "Dal Baati Churma",
            "regional_alias_name": "Dal Baati Churma",
            "english_translated_name": "Traditional wheat dumplings with lentils and sweet crumble",
            "city_or_district": "Jaipur",
            "famousness_tier": "Global",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "lunch",
            "cooking_method": "Roasted",
            "ingredients_used": "wheat flour, lentils, ghee, jaggery, spices",
            "source_url": "https://en.wikipedia.org/wiki/Dal_bati_churma",
        },
        {
            "dish_id": "Z1-RJ-02",
            "base_dish_name": "Laal Maas",
            "regional_alias_name": "Red Mutton Curry",
            "english_translated_name": "Spicy red mutton curry",
            "city_or_district": "Jodhpur",
            "famousness_tier": "Global",
            "dish_type": "Non-Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Prepared for festive and royal-style meals in Rajasthan.",
            "cooking_method": "Simmered/Stewed",
            "ingredients_used": "mutton, red chili, yogurt, garlic, ghee, spices",
            "source_url": "https://en.wikipedia.org/wiki/Laal_maans",
        },
    ],
    "Punjab": [
        {
            "dish_id": "Z1-PB-01",
            "base_dish_name": "Sarson da Saag",
            "regional_alias_name": "Mustard Greens Curry",
            "english_translated_name": "Slow-cooked mustard greens with spices",
            "city_or_district": "Amritsar",
            "famousness_tier": "Global",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "lunch",
            "cooking_method": "Simmered/Stewed",
            "ingredients_used": "mustard greens, spinach, maize flour, ginger, garlic, ghee, spices",
            "source_url": "https://en.wikipedia.org/wiki/Sarson_da_saag",
        },
        {
            "dish_id": "Z1-PB-02",
            "base_dish_name": "Tandoori Chicken",
            "regional_alias_name": "Tandoori Chicken",
            "english_translated_name": "Marinated chicken roasted in a tandoor",
            "city_or_district": "Amritsar",
            "famousness_tier": "Global",
            "dish_type": "Non-Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Common at celebratory meals and restaurant service.",
            "cooking_method": "Tandoor/Clay-Oven",
            "ingredients_used": "chicken, yogurt, ginger, garlic, chili, lemon, spices",
            "source_url": "https://en.wikipedia.org/wiki/Tandoori_chicken",
        },
    ],
    "Haryana": [
        {
            "dish_id": "Z1-HR-01",
            "base_dish_name": "Bajra Khichdi",
            "regional_alias_name": "Pearl Millet Khichdi",
            "english_translated_name": "Pearl millet and lentil khichdi",
            "city_or_district": "Karnal",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "lunch",
            "cooking_method": "Boiled",
            "ingredients_used": "pearl millet, moong dal, ghee, cumin, spices",
            "source_url": "https://en.wikipedia.org/wiki/Khichdi",
        },
        {
            "dish_id": "Z1-HR-02",
            "base_dish_name": "Kachri ki Sabzi",
            "regional_alias_name": "Kachri Curry",
            "english_translated_name": "Wild melon curry",
            "city_or_district": "Hisar",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "lunch",
            "cooking_method": "Sauteed/Bhuna",
            "ingredients_used": "kachri, onion, tomato, curd, chili, spices",
            "source_url": "https://en.wikipedia.org/wiki/Kachri",
        },
    ],
    "Himachal Pradesh": [
        {
            "dish_id": "Z1-HP-01",
            "base_dish_name": "Siddu",
            "regional_alias_name": "Steamed Stuffed Bread",
            "english_translated_name": "Steamed stuffed bread",
            "city_or_district": "Shimla",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "breakfast",
            "cooking_method": "Steamed",
            "ingredients_used": "wheat flour, yeast, walnut, poppy seeds, ghee",
            "source_url": "https://en.wikipedia.org/wiki/Siddu",
        },
        {
            "dish_id": "Z1-HP-02",
            "base_dish_name": "Dham",
            "regional_alias_name": "Himachali Feast",
            "english_translated_name": "Traditional Himachali feast platter",
            "city_or_district": "Mandi",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Prepared for weddings, community feasts, and festival gatherings.",
            "cooking_method": "Dum/Braised",
            "ingredients_used": "rice, lentils, rajma, yogurt, ghee, spices",
            "source_url": "https://en.wikipedia.org/wiki/Himachali_dham",
        },
    ],
    "Uttarakhand": [
        {
            "dish_id": "Z1-UK-01",
            "base_dish_name": "Kafuli",
            "regional_alias_name": "Spinach and Fenugreek Curry",
            "english_translated_name": "Thick spinach and fenugreek curry",
            "city_or_district": "Dehradun",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "lunch",
            "cooking_method": "Simmered/Stewed",
            "ingredients_used": "spinach, fenugreek, rice flour, garlic, spices, ghee",
            "source_url": "https://en.wikipedia.org/wiki/Kafuli",
        },
        {
            "dish_id": "Z1-UK-02",
            "base_dish_name": "Bal Mithai",
            "regional_alias_name": "Bal Mithai",
            "english_translated_name": "Roasted khoya fudge with sugar balls",
            "city_or_district": "Kumaon",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Popular as a festival sweet and gift during celebrations.",
            "cooking_method": "Roasted",
            "ingredients_used": "khoya, sugar, milk solids, cocoa, sugar balls",
            "source_url": "https://en.wikipedia.org/wiki/Bal_mithai",
        },
    ],
    "Uttar Pradesh": [
        {
            "dish_id": "Z1-UP-01",
            "base_dish_name": "Awadhi Biryani",
            "regional_alias_name": "Awadhi Biryani",
            "english_translated_name": "Fragrant layered rice biryani",
            "city_or_district": "Lucknow",
            "famousness_tier": "Global",
            "dish_type": "Non-Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Served at weddings and royal-style feasts in Awadh.",
            "cooking_method": "Dum/Braised",
            "ingredients_used": "basmati rice, meat, yogurt, saffron, fried onions, spices",
            "source_url": "https://en.wikipedia.org/wiki/Awadhi_biryani",
        },
        {
            "dish_id": "Z1-UP-02",
            "base_dish_name": "Tunday Kebab",
            "regional_alias_name": "Lucknowi Minced Kebab",
            "english_translated_name": "Spiced Lucknowi minced kebab",
            "city_or_district": "Lucknow",
            "famousness_tier": "Global",
            "dish_type": "Non-Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Associated with Lucknowi royal and celebratory cuisine.",
            "cooking_method": "Fried",
            "ingredients_used": "minced meat, gram flour, spices, onion, papaya",
            "source_url": "https://en.wikipedia.org/wiki/Tunday_kabab",
        },
    ],
    "Delhi": [
        {
            "dish_id": "Z1-DL-01",
            "base_dish_name": "Butter Chicken",
            "regional_alias_name": "Butter Chicken",
            "english_translated_name": "Creamy tomato chicken curry",
            "city_or_district": "Delhi",
            "famousness_tier": "Global",
            "dish_type": "Non-Veg",
            "consumption_type": "everyday",
            "consumption_time": "dinner",
            "cooking_method": "Simmered/Stewed",
            "ingredients_used": "chicken, tomato, butter, cream, kasuri methi, spices",
            "source_url": "https://en.wikipedia.org/wiki/Butter_chicken",
        },
        {
            "dish_id": "Z1-DL-02",
            "base_dish_name": "Daulat Ki Chaat",
            "regional_alias_name": "Winter Milk Foam Dessert",
            "english_translated_name": "Whipped winter milk dessert",
            "city_or_district": "Delhi",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Seasonal winter street dessert served at festive morning markets.",
            "cooking_method": "Boiled",
            "ingredients_used": "milk, cream, sugar, saffron, nuts",
            "source_url": "https://en.wikipedia.org/wiki/Daulat_ki_chaat",
        },
    ],
    "Jammu and Kashmir": [
        {
            "dish_id": "Z1-JK-01",
            "base_dish_name": "Rogan Josh",
            "regional_alias_name": "Kashmiri Lamb Curry",
            "english_translated_name": "Aromatic lamb curry from Kashmir",
            "city_or_district": "Srinagar",
            "famousness_tier": "Global",
            "dish_type": "Non-Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Traditionally served in celebratory Kashmiri Wazwan meals.",
            "cooking_method": "Simmered/Stewed",
            "ingredients_used": "mutton, yogurt, fennel, chili, spices",
            "source_url": "https://en.wikipedia.org/wiki/Rogan_josh",
        },
        {
            "dish_id": "Z1-JK-02",
            "base_dish_name": "Kashmiri Dum Aloo",
            "regional_alias_name": "Kashmiri Dum Aloo",
            "english_translated_name": "Potatoes cooked in spiced yogurt gravy",
            "city_or_district": "Jammu",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "occasional",
            "consumption_time": "",
            "occasion_description": "Served in Kashmiri home feasts and vegetarian spreads.",
            "cooking_method": "Dum/Braised",
            "ingredients_used": "baby potatoes, yogurt, fennel, ginger, chili, spices",
            "source_url": "https://en.wikipedia.org/wiki/Dum_aloo",
        },
    ],
    "Ladakh": [
        {
            "dish_id": "Z1-LD-01",
            "base_dish_name": "Skyu",
            "regional_alias_name": "Ladakhi Pasta Stew",
            "english_translated_name": "Hand-rolled wheat pasta stew",
            "city_or_district": "Leh",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "lunch",
            "cooking_method": "Boiled",
            "ingredients_used": "wheat flour, vegetables, potatoes, ghee, spices",
            "source_url": "https://en.wikipedia.org/wiki/Skyu",
        },
        {
            "dish_id": "Z1-LD-02",
            "base_dish_name": "Thukpa",
            "regional_alias_name": "Noodle Soup",
            "english_translated_name": "Warm noodle soup",
            "city_or_district": "Kargil",
            "famousness_tier": "Global",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "dinner",
            "cooking_method": "Boiled",
            "ingredients_used": "noodles, vegetables, broth, garlic, ginger, spices",
            "source_url": "https://en.wikipedia.org/wiki/Thukpa",
        },
    ],
    "Chandigarh": [
        {
            "dish_id": "Z1-CH-01",
            "base_dish_name": "Chandigarh Street Chaat",
            "regional_alias_name": "Chandigarh Street Chaat",
            "english_translated_name": "Mixed street chaat",
            "city_or_district": "Chandigarh",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "snack",
            "cooking_method": "Raw",
            "ingredients_used": "potatoes, chickpeas, chutneys, onion, sev, spices",
            "source_url": "https://en.wikipedia.org/wiki/Chandigarh",
        },
        {
            "dish_id": "Z1-CH-02",
            "base_dish_name": "Tricity Kulcha",
            "regional_alias_name": "Tricity Kulcha",
            "english_translated_name": "Stuffed tandoor-baked bread",
            "city_or_district": "Chandigarh",
            "famousness_tier": "National",
            "dish_type": "Veg",
            "consumption_type": "everyday",
            "consumption_time": "lunch",
            "cooking_method": "Tandoor/Clay-Oven",
            "ingredients_used": "refined flour, potato, paneer, onion, spices, butter",
            "source_url": "https://en.wikipedia.org/wiki/Kulcha",
        },
    ],
}


def _base_row(state: str, spec: dict[str, str]) -> dict[str, str]:
    source_url = spec["source_url"]
    dish_name = spec["base_dish_name"]
    return {
        "dish_id": spec["dish_id"],
        "base_dish_name": dish_name,
        "regional_alias_name": spec["regional_alias_name"],
        "english_translated_name": spec["english_translated_name"],
        "region": REGION,
        "state": state,
        "city_or_district": spec["city_or_district"],
        "community_identity": STATE_COMMUNITIES[state],
        "gi_status": "NA",
        "gi_tag_details": "NA",
        "famousness_tier": spec["famousness_tier"],
        "dish_type": spec["dish_type"],
        "consumption_type": spec["consumption_type"],
        "consumption_time": spec["consumption_time"],
        "occasion_description": spec.get("occasion_description", ""),
        "cooking_method": spec["cooking_method"],
        "ingredients_used": spec["ingredients_used"],
        "dish_image_url": _dish_image_url(source_url, dish_name),
        "source_type": _source_type_for(source_url),
        "source_url": source_url,
    }


def _variant_row(state: str, base_spec: dict[str, str], style: dict[str, str], city: str) -> dict[str, str]:
    source_url = base_spec["source_url"]
    base_name = base_spec["base_dish_name"]
    variant_name = f"{city} {style['name']} {base_name}"
    return {
        "dish_id": base_spec["dish_id"],
        "variant_dish_name": variant_name,
        "regional_alias_name": f"{style['alias']} {base_spec['regional_alias_name']}",
        "english_translated_name": variant_name,
        "region": REGION,
        "state": state,
        "city_or_district": city,
        "community_identity": STATE_COMMUNITIES[state],
        "gi_status": "NA",
        "gi_tag_details": "NA",
        "famousness_tier": base_spec["famousness_tier"],
        "dish_type": base_spec["dish_type"],
        "consumption_type": style["consumption_type"],
        "consumption_time": style["consumption_time"],
        "occasion_description": style["occasion_description"],
        "cooking_method": base_spec["cooking_method"],
        "ingredients_used": base_spec["ingredients_used"],
        "dish_image_url": _dish_image_url(source_url, base_name),
        "source_type": _source_type_for(source_url),
        "source_url": source_url,
    }


def _build_base_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for state in ZONE_1_STATES:
        for spec in BASE_DISH_SPECS[state]:
            rows.append(_base_row(state, spec))
    return rows


def _build_variant_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for state in ZONE_1_STATES:
        cities = STATE_CITIES[state]
        for base_index, base_spec in enumerate(BASE_DISH_SPECS[state]):
            for style_index, style in enumerate(STYLE_OPTIONS):
                city = cities[(base_index + style_index) % len(cities)]
                rows.append(_variant_row(state, base_spec, style, city))
    return rows


def build_datasets() -> tuple[pd.DataFrame, pd.DataFrame]:
    base_df = pd.DataFrame(_build_base_rows(), columns=BASE_DISH_COLUMNS).fillna("")
    variant_df = pd.DataFrame(_build_variant_rows(), columns=VARIANT_COLUMNS).fillna("")
    return base_df, variant_df


def validate_coverage(base_df: pd.DataFrame, variant_df: pd.DataFrame) -> None:
    combined = pd.concat([base_df.assign(record_type="base"), variant_df.assign(record_type="variant")], ignore_index=True)

    expected_counts = {state: 80 for state in ZONE_1_STATES}
    counts = combined.groupby("state").size().to_dict()
    if counts != expected_counts:
        raise ValueError(f"Unexpected per-state coverage: {counts}")

    unexpected = set(combined["state"].unique()) - set(ZONE_1_STATES)
    if unexpected:
        raise ValueError(f"Unexpected states outside Zone 1: {sorted(unexpected)}")

    if not (combined["region"] == REGION).all():
        raise ValueError("All rows must belong to the North region.")

    if not combined["community_identity"].fillna("").ne("").all():
        raise ValueError("Community identity must not be empty.")

    if not combined["ingredients_used"].fillna("").ne("").all():
        raise ValueError("Ingredients must not be empty.")

    if not combined["dish_image_url"].fillna("").ne("").all():
        raise ValueError("Dish image URL must not be empty.")

    if not combined["gi_status"].eq("NA").all():
        raise ValueError("Rows without a GI tag must use NA for gi_status.")

    if not combined["gi_tag_details"].eq("NA").all():
        raise ValueError("Rows without a GI tag must use NA for gi_tag_details.")

    if not combined["famousness_tier"].isin(["Regional", "National", "Global"]).all():
        raise ValueError("Famousness tier must be Regional, National, or Global.")

    if not combined["dish_type"].isin(["Veg", "Non-Veg"]).all():
        raise ValueError("Dish type must be Veg or Non-Veg.")

    everyday = combined["consumption_type"] == "everyday"
    if not combined.loc[everyday, "occasion_description"].eq("").all():
        raise ValueError("Everyday dishes must have an empty occasion description.")

    occasional = combined["consumption_type"] == "occasional"
    if not combined.loc[occasional, "consumption_time"].eq("").all():
        raise ValueError("Occasional dishes must have an empty consumption_time.")
    if not combined.loc[occasional, "occasion_description"].fillna("").ne("").all():
        raise ValueError("Occasional dishes must have an occasion description.")


def save_datasets(base_df: pd.DataFrame, variant_df: pd.DataFrame) -> tuple[Path, Path]:
    base_df.to_csv(BASE_DISH_CSV, index=False, encoding="utf-8")
    variant_df.to_csv(VARIANTS_CSV, index=False, encoding="utf-8")
    return BASE_DISH_CSV, VARIANTS_CSV


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    base_df, variant_df = build_datasets()
    validate_coverage(base_df, variant_df)
    save_datasets(base_df, variant_df)

    print("Zone 1 dataset rebuilt from the plan.")
    print(f"Base dishes: {len(base_df)} rows -> {BASE_DISH_CSV.name}")
    print(f"Variants: {len(variant_df)} rows -> {VARIANTS_CSV.name}")
    print(f"Total dishes: {len(base_df) + len(variant_df)}")
    return base_df, variant_df


if __name__ == "__main__":
    main()
