"""
Demo data definitions — pure data, no database access.

Loaded by scripts/generate_test_data.py, which turns it into rows.

Conventions:
- A time is (days_from_today, hour, minute) in local time (DEFAULT_TZ); negative
  days are in the past. Everything is relative to the moment of seeding so the
  demo always has upcoming products and alarms.
- Records refer to each other by "key" (accounts, teams, products, customers,
  companies) or by email (users).
- All people, companies, phone numbers and bank details are fictional. Phone
  numbers come from the ranges PTS reserves for fiction, emails use the
  reserved .example TLD, so nothing here can reach a real person.
"""

PASSWORD = "1234"

# Users created by the previous generator; removed on --reset.
LEGACY_EMAILS = ["m1admin@x", "m2admin@x", "sales@x", "support@x", "finance@x", "viewer@x"]

ROLE_ADMIN = 0b0001
CALLER_ROLES = {"customers": ROLE_ADMIN, "products": ROLE_ADMIN}
FINANCE_ROLES = {"customers": ROLE_ADMIN, "companies": ROLE_ADMIN, "invoices": ROLE_ADMIN}

# ProductCustomer.status
INTERESTED, NOT_INTERESTED, COMING = 1, 2, 3
# Call.status
ANSWER, NO_ANSWER, OUTSIDE = 1, 2, 3
# Invoice extra.status
PROCESSING, OK, CANCELLED = "1", "2", "3"


# ---------------------------------------------------------------------------
# CMS config used by the demo tenants.
#
# The ids are chosen to match what the templates and columns expect:
# - product type item ids are numeric strings ("4".."7"): they are stored in the
#   integer column ProductCustomer.type_status, after the fixed statuses 1-3
# - organisation and personality ids are integers (looked up as ints)
# ---------------------------------------------------------------------------
DEMO_CMS = {
    "categories": {
        "active": {
            "name": "AKTIV",
            "items": {
                "active-key": "Nyckelkund",
                "active-loyal": "Trogen",
                "active-frequent": "Kommer ofta",
                "active-rare": "Kommer sällan",
            },
        },
        "prospect": {
            "name": "PROSPEKT",
            "items": {
                "prospect-new": "Ny kontakt",
                "prospect-callback": "Vill bli uppringd",
                "prospect-talked": "Har pratat med",
            },
        },
        "inactive": {
            "name": "INAKTIV",
            "items": {
                "inactive-no-interest": "Inte intresserad",
                "inactive-no-answer": "Svarar inte",
                "inactive-moved": "Flyttat",
                "inactive-unsubscribed": "Avböjt utskick",
            },
        },
        "segment": {
            "name": "SEGMENT",
            "items": {
                "seg-private": "Privatperson",
                "seg-business": "Företagskund",
                "seg-student": "Student",
                "seg-senior": "Senior",
            },
        },
    },
    "product_extras": {
        "external": {"label": "Extern arrangör", "type": "bool", "filter": True},
        "online": {"label": "Digitalt", "type": "bool", "filter": True},
    },
    "products": {
        "event": {
            "name": "Event",
            "items": {"4": "Betald", "5": "Betalar på plats", "6": "Deltog", "7": "Deltog ej"},
            "extra": {
                "location": {"label": "Plats", "type": "text", "filter": True, "list": True},
                "capacity": {"label": "Antal platser", "type": "number"},
            },
        },
        "subscription": {
            "name": "Prenumeration",
            "items": {"4": "Betald", "5": "Ej betald", "6": "Utgått"},
            "extra": {},
        },
        "membership": {
            "name": "Medlemskap",
            "items": {"4": "Betald", "5": "Ej betald"},
            "extra": {},
        },
        "course": {
            "name": "Kurs",
            "items": {"4": "Betald", "5": "Faktura skickad", "6": "Genomförd"},
            "extra": {
                "location": {"label": "Plats", "type": "text", "filter": True, "list": True},
                "teacher": {"label": "Kursledare", "type": "text"},
            },
        },
    },
    "customer_extras": {
        "newsletter": {"label": "Nyhetsbrev", "type": "bool", "filter": True},
        "gdpr_consent": {"label": "GDPR-samtycke", "type": "bool", "filter": True},
    },
    "organisations": [
        {"id": 1, "name": "Näringslivsklubben"},
        {"id": 2, "name": "Kulturföreningen"},
        {"id": 3, "name": "Alumninätverket"},
        {"id": 4, "name": "Studentkåren"},
        {"id": 5, "name": "Företagarföreningen"},
    ],
    "filters": [
        {"id": "is_filter_1", "name": "Mingel & fester"},
        {"id": "is_filter_2", "name": "AW"},
        {"id": "is_filter_3", "name": "Föreläsningar"},
        {"id": "is_filter_4", "name": "Workshops"},
        {"id": "is_filter_5", "name": "Konferenser"},
        {"id": "is_filter_6", "name": "Medlemskap"},
        {"id": "is_filter_7", "name": "Prenumeration"},
    ],
    "personalities": [
        {"id": 1, "name": "Ny"},
        {"id": 2, "name": "Gul"},
        {"id": 3, "name": "Blå"},
        {"id": 4, "name": "Röd"},
        {"id": 5, "name": "Grön"},
    ],
}


def _user_extra(first, last, address, email, phone, bank, bic, clearing, account):
    return {
        "first_name": first,
        "last_name": last,
        "address": address,
        "email": email,
        "cc_email": "",
        "phone": phone,
        "bank_name": bank,
        "swift_bic": bic,
        "account_holder": f"{first} {last}",
        "account_number": account,
        "clearing_number": clearing,
    }


def _address(line1, line2, postal_code, city, country="Sverige"):
    return {
        "address_line1": line1,
        "address_line2": line2,
        "postal_code": postal_code,
        "postal_address": city,
        "country": country,
    }


# ---------------------------------------------------------------------------
# Tenant 1 — Nordljus Media AB (the tenant behind the landing page login)
# ---------------------------------------------------------------------------
NORDLJUS = {
    "slug": "default",
    "name": "Nordljus Media AB",

    "accounts": [
        {"key": "media", "name": "Nordljus Media AB", "extra": {
            "vat_number": "SE559812345601",
            **_address("Sveavägen 98", "Plan 4", "113 50", "Stockholm"),
            "bank_name": "Handelsbanken", "iban": "SE35 6000 0000 0005 4910 0031", "bic": "HANDSESS",
            "bankgiro": "5051-6822", "plusgiro": "47 11 02-5",
            "comment": "Moderbolag. Används för all extern fakturering.",
        }},
        {"key": "event", "name": "Nordljus Event", "extra": {
            "vat_number": "SE559812345601",
            **_address("Sveavägen 98", "Plan 2", "113 50", "Stockholm"),
            "bank_name": "Handelsbanken", "iban": "SE72 6000 0000 0005 4910 0147", "bic": "HANDSESS",
            "bankgiro": "5051-6830", "plusgiro": "",
            "comment": "Biljettintäkter från mingel, föreläsningar och konferenser.",
        }},
        {"key": "forlag", "name": "Nordljus Förlag", "extra": {
            "vat_number": "SE559733218801",
            **_address("Kungsgatan 41", "", "411 15", "Göteborg"),
            "bank_name": "Swedbank", "iban": "SE45 8000 0810 5998 4627 3310", "bic": "SWEDSESS",
            "bankgiro": "720-4418", "plusgiro": "",
            "comment": "Magasinet och prenumerationer. Moms 6 % på tryckt utgåva.",
        }},
        {"key": "stiftelse", "name": "Nordljus Stipendiestiftelse", "extra": {
            "vat_number": "",
            **_address("Sveavägen 98", "c/o Nordljus Media AB", "113 50", "Stockholm"),
            "bank_name": "SEB", "iban": "SE12 5000 0000 0583 9825 7466", "bic": "ESSESESS",
            "bankgiro": "900-7741", "plusgiro": "90 07 74-1",
            "comment": "Gåvor och stipendier. Ej momspliktig verksamhet.",
        }},
    ],

    "teams": [
        {"key": "kundtjanst", "name": "Kundtjänst", "account": "event", "extra": {
            **_address("Sveavägen 98", "Plan 2", "113 50", "Stockholm"),
            "vat_number": "SE559812345601",
            "bank_name": "Handelsbanken", "iban": "SE72 6000 0000 0005 4910 0147", "bic": "HANDSESS",
            "bankgiro": "5051-6830", "plusgiro": "",
            "note": "Betalningsvillkor 30 dagar netto.",
        }},
        {"key": "ekonomi", "name": "Ekonomi", "account": "media", "extra": {
            **_address("Sveavägen 98", "Plan 4", "113 50", "Stockholm"),
            "vat_number": "SE559812345601",
            "bank_name": "Handelsbanken", "iban": "SE35 6000 0000 0005 4910 0031", "bic": "HANDSESS",
            "bankgiro": "5051-6822", "plusgiro": "47 11 02-5",
            "note": "Betalningsvillkor 30 dagar netto. Dröjsmålsränta enligt räntelagen.",
        }},
    ],

    "users": [
        {"email": "anna.lindqvist@nordljus.example", "admin": 1, "team": "kundtjanst", "roles": CALLER_ROLES,
         "extra": _user_extra("Anna", "Lindqvist", "Rörstrandsgatan 14, 113 40 Stockholm",
                              "anna.lindqvist@nordljus.example", "+46701740611",
                              "Swedbank", "SWEDSESS", "8327-9", "934 551 207-4")},
        {"email": "sales@nordljus.example", "admin": 0, "team": "kundtjanst", "roles": CALLER_ROLES,
         "extra": _user_extra("Sara", "Nyström", "Hornsgatan 72, 118 21 Stockholm",
                              "sales@nordljus.example", "+46701740612",
                              "Nordea", "NDEASESS", "3300", "880412-4521")},
        {"email": "jonas.berg@nordljus.example", "admin": 0, "team": "kundtjanst", "roles": CALLER_ROLES,
         "extra": _user_extra("Jonas", "Berg", "Västmannagatan 31, 113 25 Stockholm",
                              "jonas.berg@nordljus.example", "+46701740613",
                              "SEB", "ESSESESS", "5201", "22 384 71")},
        {"email": "karin.ekstrom@nordljus.example", "admin": 1, "team": "ekonomi", "roles": FINANCE_ROLES,
         "extra": _user_extra("Karin", "Ekström", "Bergsunds strand 9, 117 38 Stockholm",
                              "karin.ekstrom@nordljus.example", "+46701740614",
                              "Handelsbanken", "HANDSESS", "6102", "418 772 306")},
        {"email": "finance@nordljus.example", "admin": 0, "team": "ekonomi", "roles": FINANCE_ROLES,
         "extra": _user_extra("Oskar", "Dahl", "Gullmarsvägen 22, 121 40 Johanneshov",
                              "finance@nordljus.example", "+46701740615",
                              "Swedbank", "SWEDSESS", "8105-9", "724 118 630-2")},
        {"email": "maria.sandberg@nordljus.example", "admin": 0, "team": "ekonomi", "roles": FINANCE_ROLES,
         "extra": _user_extra("Maria", "Sandberg", "Lötsjövägen 5, 174 43 Sundbyberg",
                              "maria.sandberg@nordljus.example", "+46701740616",
                              "Länsförsäkringar Bank", "ELLFSESS", "9023", "33 507 194")},
    ],

    "products": [
        {"key": "hostmingel", "type_id": "event", "name": "Höstmingel på Münchenbryggeriet", "price": 395,
         "description": "Årets stora nätverkskväll för medlemmar och prenumeranter. Mat, bar och "
                        "samtal på scen med redaktionen. Anmälan senast en vecka innan.",
         "start": (30, 18, 0), "end": (30, 23, 0), "filters": [1, 2], "visible_all": True,
         "extra": {"location": "Stockholm", "capacity": "180"}},
        {"key": "ai_forelasning", "type_id": "event", "name": "Föreläsning: AI i redaktionen", "price": 250,
         "description": "Frukostföreläsning om hur redaktioner använder AI-verktyg i research och "
                        "faktakoll. Sänds även digitalt för den som inte kan vara på plats.",
         "start": (52, 8, 0), "end": (52, 10, 0), "filters": [3], "visible_all": True,
         "extra": {"location": "Göteborg", "capacity": "80", "online": "true"}},
        {"key": "mediedagar", "type_id": "event", "name": "Nordiska Mediedagarna", "price": 4900,
         "description": "Två dagars konferens med talare från hela Norden. Priset avser "
                        "konferenspass inklusive lunch och middag dag ett.",
         "start": (150, 9, 0), "end": (151, 16, 30), "filters": [5], "visible_all": False,
         "extra": {"location": "Malmö", "capacity": "450", "external": "true"}},
        {"key": "magasin", "type_id": "subscription", "name": "Nordljus Magasin – helår", "price": 895,
         "description": "Tio nummer per år, tryckt och digitalt. Förnyas automatiskt och kan sägas "
                        "upp när som helst.",
         "start": (-200, 0, 0), "end": (165, 23, 59), "filters": [7], "visible_all": True,
         "extra": {}},
        {"key": "medlemskap", "type_id": "membership", "name": "Årsmedlemskap", "price": 450,
         "description": "Medlemskap i Nordljus läsarklubb: förtur och rabatt på evenemang samt "
                        "medlemsbrev varje månad.",
         "start": (-100, 0, 0), "end": (265, 23, 59), "filters": [6], "visible_all": True,
         "extra": {}},
        {"key": "skrivarkurs", "type_id": "course", "name": "Skrivarkurs: Berätta med data", "price": 6900,
         "description": "Fyra kurstillfällen om datajournalistik för skribenter. Max 16 deltagare. "
                        "Kurslitteratur ingår.",
         "start": (95, 13, 0), "end": (116, 16, 0), "filters": [4], "visible_all": False,
         "extra": {"location": "Stockholm", "teacher": "Helena Brandt"}},
    ],

    "customers": [
        {"key": "erik", "user_id": "NL-10231", "first_name": "Erik", "last_name": "Lundgren",
         "email": "erik.lundgren@lundgrenkonsult.example", "phone": "+46701740621",
         "description_phone": "Mobil, säkrast efter kl. 15", "location": "Stockholm", "contributes": 4,
         "team": "kundtjanst", "assigned": "sales@nordljus.example",
         "comment": "Prenumerant sedan flera år. Tar gärna med kollegor på mingel – fråga om gruppbokning.",
         "sub_caller": "Sara", "organisations": ["1", "5"], "categories": ["active-key", "seg-business"],
         "personality_type": 4, "filters": [1, 2, 5, 7], "tags": ["VIP", "gruppbokning"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "maja", "user_id": "NL-10244", "first_name": "Maja", "last_name": "Öberg",
         "email": "maja.oberg@post.example", "phone": "+46701740622",
         "description_phone": "Mobil", "location": "Uppsala", "contributes": 6,
         "team": "kundtjanst", "assigned": "sales@nordljus.example",
         "comment": "Doktorand i medievetenskap. Intresserad av föreläsningar, helst digitalt.",
         "sub_caller": "Sara", "organisations": ["3", "4"], "categories": ["active-frequent", "seg-student"],
         "personality_type": 3, "filters": [3, 4, 7], "tags": ["student", "digitalt"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "larsgoran", "user_id": "NL-10102", "first_name": "Lars-Göran", "last_name": "Hedlund",
         "email": "lg.hedlund@post.example", "phone": "+46701740623",
         "description_phone": "Hemtelefon, ring förmiddag", "location": "Västerås", "contributes": 5,
         "team": "kundtjanst", "assigned": "sales@nordljus.example",
         "comment": "Pensionerad chefredaktör. Ger regelbundet till stipendiestiftelsen. Vill ha papperstidning.",
         "sub_caller": "Sara", "organisations": ["2"], "categories": ["active-loyal", "seg-senior"],
         "personality_type": 5, "filters": [3, 5, 6, 7], "tags": ["givare", "VIP"],
         "extra": {"gdpr_consent": "true"}},
        {"key": "fatima", "user_id": "NL-10377", "first_name": "Fatima", "last_name": "Al-Hassan",
         "email": "fatima.alhassan@solnakommunikation.example", "phone": "+46701740624",
         "description_phone": "Arbete", "location": "Solna", "contributes": 3,
         "team": "kundtjanst", "assigned": "sales@nordljus.example",
         "comment": "Kommunikationschef. Vill ha faktura till företaget, inte kortbetalning.",
         "sub_caller": "Sara", "organisations": ["1"], "categories": ["active-frequent", "seg-business"],
         "personality_type": 2, "filters": [1, 3, 4, 5], "tags": ["faktura"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "johanna", "user_id": "NL-10412", "first_name": "Johanna", "last_name": "Wikström",
         "email": "johanna.wikstrom@post.example", "phone": "+46701740625",
         "description_phone": "Mobil", "location": "Göteborg", "contributes": 1,
         "team": "kundtjanst", "assigned": "sales@nordljus.example",
         "comment": "Kom in via nyhetsbrevet. Har inte köpt något än men bad oss höra av oss om Göteborgsevent.",
         "sub_caller": "Sara", "organisations": [], "categories": ["prospect-callback", "seg-private"],
         "personality_type": 1, "filters": [2, 3], "tags": ["nyhetsbrev"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "anders", "user_id": "NL-10058", "first_name": "Anders", "last_name": "Sjöberg",
         "email": "anders.sjoberg@sjobergstryckeri.example", "phone": "+46701740626",
         "description_phone": "Växel, be om Anders", "location": "Örebro", "contributes": 2,
         "team": "kundtjanst", "assigned": "sales@nordljus.example",
         "comment": "Svår att nå dagtid. Avböjde medlemskap i våras men stöttar stiftelsen ibland.",
         "sub_caller": "Sara", "organisations": ["5"], "categories": ["active-rare", "seg-business"],
         "personality_type": 4, "filters": [5, 6], "tags": ["givare"],
         "extra": {"gdpr_consent": "true"}},
        {"key": "elin", "user_id": "NL-10489", "first_name": "Elin", "last_name": "Forsberg",
         "email": "elin.forsberg@post.example", "phone": "+46701740627",
         "description_phone": "Mobil", "location": "Malmö", "contributes": 6,
         "team": "kundtjanst", "assigned": "jonas.berg@nordljus.example",
         "comment": "Frilansjournalist. Anmäld till skrivarkursen, väntar på besked om stipendium.",
         "sub_caller": "Jonas", "organisations": ["2", "3"], "categories": ["active-frequent", "seg-private"],
         "personality_type": 2, "filters": [3, 4, 5, 7], "tags": ["frilans", "stipendium"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "henrik", "user_id": "NL-10301", "first_name": "Henrik", "last_name": "Åkesson",
         "email": "henrik.akesson@post.example", "phone": "+46701740628",
         "description_phone": "Mobil", "location": "Lund", "contributes": 1,
         "team": "kundtjanst", "assigned": "jonas.berg@nordljus.example",
         "comment": "Sade upp prenumerationen i fjol. Bad uttryckligen att inte bli kontaktad om förnyelse.",
         "sub_caller": "Jonas", "organisations": [], "categories": ["inactive-no-interest", "inactive-unsubscribed"],
         "personality_type": 3, "filters": [], "tags": ["uppsagd"],
         "extra": {}},
        {"key": "sofia", "user_id": "NL-10533", "first_name": "Sofia", "last_name": "Bergqvist",
         "email": "sofia.bergqvist@post.example", "phone": "+46701740629",
         "description_phone": "Mobil", "location": "Umeå", "contributes": None,
         "team": None, "assigned": None,
         "comment": "Ny kontakt från bokmässan. Inte tilldelad någon ringare ännu.",
         "sub_caller": "", "organisations": ["2"], "categories": ["prospect-new", "seg-private"],
         "personality_type": 1, "filters": [3, 7], "tags": ["bokmässan"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "viktor", "user_id": "NL-10534", "first_name": "Viktor", "last_name": "Nordin",
         "email": "viktor.nordin@nordinmedia.example", "phone": "+46701740630",
         "description_phone": "Arbete", "location": "Linköping", "contributes": None,
         "team": None, "assigned": None,
         "comment": "Fyllde i intresseanmälan för Nordiska Mediedagarna på webben. Inte tilldelad ännu.",
         "sub_caller": "", "organisations": ["1"], "categories": ["prospect-new", "seg-business"],
         "personality_type": 1, "filters": [5], "tags": ["webbformulär"],
         "extra": {"gdpr_consent": "true"}},
    ],

    # (customer, product, status, type_status, order placed days-from-today)
    "selections": [
        ("erik", "hostmingel", COMING, 4, -6),
        ("erik", "mediedagar", INTERESTED, None, None),
        ("erik", "magasin", COMING, 4, -190),
        ("maja", "ai_forelasning", COMING, 5, -3),
        ("maja", "magasin", COMING, 4, -120),
        ("maja", "skrivarkurs", INTERESTED, None, None),
        ("larsgoran", "magasin", COMING, 4, -200),
        ("larsgoran", "medlemskap", COMING, 4, -95),
        ("larsgoran", "mediedagar", COMING, 5, -12),
        ("fatima", "hostmingel", COMING, 5, -2),
        ("fatima", "skrivarkurs", COMING, 5, -9),
        ("fatima", "mediedagar", INTERESTED, None, None),
        ("johanna", "ai_forelasning", INTERESTED, None, None),
        ("johanna", "medlemskap", NOT_INTERESTED, None, None),
        ("anders", "medlemskap", NOT_INTERESTED, None, None),
        ("anders", "mediedagar", INTERESTED, None, None),
        ("elin", "skrivarkurs", COMING, 5, -14),
        ("elin", "magasin", COMING, 5, -30),
        ("henrik", "magasin", NOT_INTERESTED, None, None),
        ("henrik", "hostmingel", NOT_INTERESTED, None, None),
    ],

    # (customer, team, when, status, note)
    "calls": [
        ("erik", "kundtjanst", (-41, 14, 10), ANSWER,
         "Förnyade helårsprenumerationen. Vill ha fakturan på mejl i fortsättningen."),
        ("erik", "kundtjanst", (-6, 15, 35), ANSWER,
         "Bokade två platser till höstminglet, betalade med kort. Funderar på Mediedagarna – ring igen efter budgetmötet."),
        ("maja", "kundtjanst", (-18, 10, 5), NO_ANSWER, "Inget svar, lämnade röstmeddelande om AI-föreläsningen."),
        ("maja", "kundtjanst", (-3, 16, 20), ANSWER,
         "Anmäld till AI-föreläsningen, betalar på plats. Frågade om studentrabatt på skrivarkursen."),
        ("larsgoran", "kundtjanst", (-12, 9, 40), ANSWER,
         "Anmäld till Nordiska Mediedagarna. Behöver hjälp med hotell, skickar förslag per brev."),
        ("larsgoran", "kundtjanst", (-1, 10, 15), OUTSIDE,
         "Ringde själv in och frågade om tågtider till Malmö. Mycket nöjd med senaste numret."),
        ("fatima", "kundtjanst", (-9, 13, 0), ANSWER,
         "Bokade skrivarkursen åt en medarbetare. Faktura till Solna Kommunikation, märk med kostnadsställe 410."),
        ("fatima", "kundtjanst", (-2, 11, 30), ANSWER,
         "Kommer på höstminglet, betalar på plats. Vill ha offert på 10 konferenspass till Mediedagarna."),
        ("johanna", "kundtjanst", (-5, 17, 45), ANSWER,
         "Intresserad av AI-föreläsningen men vill kolla kalendern. Tackade nej till medlemskap just nu."),
        ("anders", "kundtjanst", (-25, 11, 0), NO_ANSWER, "Växeln svarade, Anders i möte hela dagen."),
        ("anders", "kundtjanst", (-10, 15, 10), NO_ANSWER, "Inget svar. Tredje försöket den här månaden."),
        ("anders", "kundtjanst", (0, 9, 20), ANSWER,
         "Fick tag på honom till slut. Inget medlemskap, men vill ha program för Mediedagarna när det är klart."),
        ("elin", "kundtjanst", (-14, 14, 30), ANSWER,
         "Anmäld till skrivarkursen, faktura skickad. Söker stipendium för kursavgiften."),
        ("henrik", "kundtjanst", (-60, 13, 15), ANSWER,
         "Vill inte förnya och inte bli kontaktad igen. Markerad som avböjt utskick."),
    ],

    # (customer, product, team, when, reminder minutes before, note)
    "alarms": [
        ("erik", "mediedagar", "kundtjanst", (2, 10, 0), 30,
         "Ring Erik efter budgetmötet – vill han boka Mediedagarna? Nämn gruppris vid 3+ pass."),
        ("fatima", "mediedagar", "kundtjanst", (4, 13, 30), 60,
         "Följ upp offerten på 10 konferenspass. Kontaktperson på ekonomi: Karin."),
        ("johanna", "ai_forelasning", "kundtjanst", (9, 16, 0), 30,
         "Johanna skulle kolla kalendern. Sista anmälningsdag närmar sig."),
        ("maja", "skrivarkurs", "kundtjanst", (16, 11, 0), 30,
         "Återkom om studentrabatt på skrivarkursen (20 % godkänt av Anna)."),
        ("anders", "mediedagar", "kundtjanst", (35, 9, 30), 120,
         "Skicka programmet för Mediedagarna och ring dagen efter."),
        ("larsgoran", "medlemskap", "kundtjanst", (120, 10, 0), 1440,
         "Påminn om förnyelse av årsmedlemskapet i god tid."),
    ],

    "companies": [
        {"key": "bergstrom", "team": "ekonomi", "first_name": "Per", "last_name": "Bergström",
         "email": "per.bergstrom@bergstromsbygg.example", "phone": "+46846500411",
         "comment": "Annonserar i varje nummer. Vill ha samlingsfaktura per kvartal.",
         "extra": {"company_name": "Bergströms Bygg & Fastighet AB", "org_nr": "5568123456",
                   **_address("Industrivägen 12", "", "171 48", "Solna"),
                   "cc_email": "ekonomi@bergstromsbygg.example"}},
        {"key": "solna", "team": "ekonomi", "first_name": "Fatima", "last_name": "Al-Hassan",
         "email": "fatima.alhassan@solnakommunikation.example", "phone": "+46846500427",
         "comment": "Märk alltid fakturor med kostnadsställe 410.",
         "extra": {"company_name": "Solna Kommunikation AB", "org_nr": "5590457712",
                   **_address("Råsundavägen 4", "Box 1207", "169 56", "Solna"),
                   "cc_email": "faktura@solnakommunikation.example"}},
        {"key": "vastkust", "team": "ekonomi", "first_name": "Gunilla", "last_name": "Holmberg",
         "email": "gunilla.holmberg@vastkusttryck.example", "phone": "+46313900618",
         "comment": "Tryckeri och samarbetspartner för magasinet. 45 dagars betalningsvillkor enligt avtal.",
         "extra": {"company_name": "Västkust Tryck & Media AB", "org_nr": "5566340981",
                   **_address("Hamngatan 27", "", "411 14", "Göteborg"),
                   "cc_email": ""}},
        {"key": "oresund", "team": "ekonomi", "first_name": "Mads", "last_name": "Kjeldsen",
         "email": "mads.kjeldsen@oresundevents.example", "phone": "+4533456701",
         "comment": "Dansk medarrangör av Nordiska Mediedagarna. Faktureras i EUR utan moms (omvänd skattskyldighet).",
         "extra": {"company_name": "Øresund Events ApS", "org_nr": "DK38914522",
                   **_address("Amager Strandvej 60", "2. sal", "2300", "København S", "Danmark"),
                   "cc_email": "bogholderi@oresundevents.example"}},
        {"key": "norrlands", "team": "ekonomi", "first_name": "Ingrid", "last_name": "Söderlund",
         "email": "ingrid.soderlund@norrlandsbanken.example", "phone": "+4690465008",
         "comment": "Huvudsponsor för stipendiestiftelsen.",
         "extra": {"company_name": "Norrlands Sparbank", "org_nr": "5980117734",
                   **_address("Storgatan 50", "", "903 26", "Umeå"),
                   "cc_email": ""}},
    ],

    # date / due are days from today; rows are (description, price, qty)
    "invoices": [
        {"company": "bergstrom", "team": "ekonomi", "date": -64, "due": -34, "status": OK,
         "vat": "25", "currency": "SEK", "note": "Annonsering kvartal 2. Tack för ett gott samarbete!",
         "rows": [("Helsidesannons Nordljus Magasin nr 4–6", "18500", "3"),
                  ("Banner i medlemsbrevet, april–juni", "4200", "3")]},
        {"company": "vastkust", "team": "ekonomi", "date": -38, "due": 7, "status": OK,
         "vat": "25", "currency": "SEK", "note": "Enligt samarbetsavtal 2024-11. Betalningsvillkor 45 dagar.",
         "rows": [("Utställarplats Nordiska Mediedagarna, 12 kvm", "32000", "1"),
                  ("Konferenspass personal", "4900", "4")]},
        {"company": "oresund", "team": "ekonomi", "date": -21, "due": 9, "status": OK,
         "vat": "0", "currency": "EUR", "note": "Reverse charge, article 196 Council Directive 2006/112/EC.",
         "rows": [("Co-production fee, Nordiska Mediedagarna", "8500", "1"),
                  ("Speaker travel, shared cost", "640", "2")]},
        {"company": "solna", "team": "ekonomi", "date": -9, "due": 21, "status": CANCELLED,
         "vat": "25", "currency": "SEK", "note": "Makulerad – fel kostnadsställe. Ersätts av ny faktura.",
         "rows": [("Skrivarkurs: Berätta med data, 1 deltagare", "6900", "1")]},
        {"company": "solna", "team": "ekonomi", "date": -8, "due": 22, "status": OK,
         "vat": "25", "currency": "SEK", "note": "Kostnadsställe 410. Ersätter makulerad faktura.",
         "rows": [("Skrivarkurs: Berätta med data, 1 deltagare", "6900", "1"),
                  ("Kurslitteratur", "385", "1")]},
        {"company": "norrlands", "team": "ekonomi", "date": -2, "due": 28, "status": PROCESSING,
         "vat": "25", "currency": "SEK", "note": "Sponsorpaket enligt offert. Inväntar inköpsordernummer.",
         "rows": [("Huvudsponsor höstmingel, logotyp på scen och i program", "45000", "1"),
                  ("Biljetter höstmingel", "395", "20")]},
        {"company": "bergstrom", "team": "ekonomi", "date": 0, "due": 30, "status": PROCESSING,
         "vat": "25", "currency": "SEK", "note": "Annonsering kvartal 3.",
         "rows": [("Helsidesannons Nordljus Magasin nr 7–9", "18500", "3")]},
    ],
}


# ---------------------------------------------------------------------------
# Tenant 2 — Fjällvind Event AB (smaller; shows tenant isolation and the
# tenant picker, since two of the Nordljus users also work here)
# ---------------------------------------------------------------------------
FJALLVIND = {
    "slug": "fjallvind",
    "name": "Fjällvind Event AB",

    "accounts": [
        {"key": "ab", "name": "Fjällvind Event AB", "extra": {
            "vat_number": "SE559244871201",
            **_address("Årevägen 138", "", "837 52", "Åre"),
            "bank_name": "Swedbank", "iban": "SE91 8000 0832 7900 4418 2205", "bic": "SWEDSESS",
            "bankgiro": "5820-3317", "plusgiro": "",
            "comment": "Huvudkonto för bokningar och fakturering.",
        }},
        {"key": "guide", "name": "Fjällvind Guidebyrå", "extra": {
            "vat_number": "SE559244871201",
            **_address("Årevägen 138", "", "837 52", "Åre"),
            "bank_name": "Swedbank", "iban": "SE18 8000 0832 7900 4418 2311", "bic": "SWEDSESS",
            "bankgiro": "5820-3325", "plusgiro": "",
            "comment": "Guidade turer och kurser. Moms 6 % på guidning.",
        }},
        {"key": "uthyrning", "name": "Fjällvind Uthyrning", "extra": {
            "vat_number": "SE559244871201",
            **_address("Stationsvägen 9", "", "837 52", "Åre"),
            "bank_name": "Handelsbanken", "iban": "SE64 6000 0000 0007 2815 5093", "bic": "HANDSESS",
            "bankgiro": "713-9042", "plusgiro": "",
            "comment": "Uthyrning av utrustning. Deposition bokförs separat.",
        }},
        {"key": "klubb", "name": "Fjällvind Klubben", "extra": {
            "vat_number": "",
            **_address("Årevägen 138", "", "837 52", "Åre"),
            "bank_name": "Swedbank", "iban": "SE40 8000 0832 7900 4418 2477", "bic": "SWEDSESS",
            "bankgiro": "5820-3333", "plusgiro": "",
            "comment": "Medlemsavgifter för kundklubben.",
        }},
    ],

    "teams": [
        {"key": "bokning", "name": "Bokning", "account": "ab", "extra": {
            **_address("Årevägen 138", "", "837 52", "Åre"),
            "vat_number": "SE559244871201",
            "bank_name": "Swedbank", "iban": "SE91 8000 0832 7900 4418 2205", "bic": "SWEDSESS",
            "bankgiro": "5820-3317", "plusgiro": "",
            "note": "Betalningsvillkor 20 dagar netto.",
        }},
        {"key": "ekonomi", "name": "Ekonomi", "account": "ab", "extra": {
            **_address("Årevägen 138", "", "837 52", "Åre"),
            "vat_number": "SE559244871201",
            "bank_name": "Swedbank", "iban": "SE91 8000 0832 7900 4418 2205", "bic": "SWEDSESS",
            "bankgiro": "5820-3317", "plusgiro": "",
            "note": "Betalningsvillkor 20 dagar netto.",
        }},
    ],

    # Same people as in Nordljus — they are linked to both tenants.
    "users": [
        {"email": "anna.lindqvist@nordljus.example", "admin": 1, "team": "bokning", "roles": CALLER_ROLES,
         "extra": _user_extra("Anna", "Lindqvist", "Rörstrandsgatan 14, 113 40 Stockholm",
                              "anna.lindqvist@nordljus.example", "+46701740611",
                              "Swedbank", "SWEDSESS", "8327-9", "934 551 207-4")},
        {"email": "karin.ekstrom@nordljus.example", "admin": 1, "team": "ekonomi", "roles": FINANCE_ROLES,
         "extra": _user_extra("Karin", "Ekström", "Bergsunds strand 9, 117 38 Stockholm",
                              "karin.ekstrom@nordljus.example", "+46701740614",
                              "Handelsbanken", "HANDSESS", "6102", "418 772 306")},
    ],

    "products": [
        {"key": "topptur", "type_id": "event", "name": "Toppturshelg i Åre", "price": 5400,
         "description": "Tre dagar med bergsguide, två nätter på fjällstation och all säkerhetsutrustning.",
         "start": (45, 8, 0), "end": (47, 17, 0), "filters": [1], "visible_all": True,
         "extra": {"location": "Åre", "capacity": "12"}},
        {"key": "after_ski", "type_id": "event", "name": "Kundkväll: Säsongspremiär", "price": 0,
         "description": "Säsongsstart för klubbmedlemmar med bildvisning, AW och prova-på av årets utrustning.",
         "start": (24, 17, 30), "end": (24, 21, 0), "filters": [2], "visible_all": True,
         "extra": {"location": "Östersund", "capacity": "60"}},
        {"key": "klubb", "type_id": "membership", "name": "Fjällvind Klubben", "price": 350,
         "description": "Årsmedlemskap: 10 % på alla turer och förtur vid bokning.",
         "start": (-150, 0, 0), "end": (215, 23, 59), "filters": [6], "visible_all": True,
         "extra": {}},
        {"key": "lavinkurs", "type_id": "course", "name": "Lavinkurs steg 1", "price": 3900,
         "description": "Tvådagarskurs i lavinkunskap och kamraträddning. Sändare, sond och spade ingår.",
         "start": (60, 9, 0), "end": (61, 16, 0), "filters": [4], "visible_all": True,
         "extra": {"location": "Storulvån", "teacher": "Tobias Edlund"}},
    ],

    "customers": [
        {"key": "linnea", "user_id": "FV-2041", "first_name": "Linnea", "last_name": "Strand",
         "email": "linnea.strand@post.example", "phone": "+46701740641",
         "description_phone": "Mobil", "location": "Östersund", "contributes": 4,
         "team": "bokning", "assigned": "anna.lindqvist@nordljus.example",
         "comment": "Åker med oss varje vinter. Vegetarian – meddela fjällstationen.",
         "sub_caller": "Anna", "organisations": [], "categories": ["active-loyal", "seg-private"],
         "personality_type": 5, "filters": [1, 4, 6], "tags": ["stamkund"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "oscar", "user_id": "FV-2087", "first_name": "Oscar", "last_name": "Lindahl",
         "email": "oscar.lindahl@lindahlrevision.example", "phone": "+46701740642",
         "description_phone": "Arbete", "location": "Sundsvall", "contributes": 3,
         "team": "bokning", "assigned": "anna.lindqvist@nordljus.example",
         "comment": "Bokar konferensresor åt byrån. Vill alltid ha faktura.",
         "sub_caller": "Anna", "organisations": ["5"], "categories": ["active-key", "seg-business"],
         "personality_type": 4, "filters": [1, 2], "tags": ["företag", "faktura"],
         "extra": {"gdpr_consent": "true"}},
        {"key": "amanda", "user_id": "FV-2112", "first_name": "Amanda", "last_name": "Persson",
         "email": "amanda.persson@post.example", "phone": "+46701740643",
         "description_phone": "Mobil", "location": "Stockholm", "contributes": 1,
         "team": "bokning", "assigned": "anna.lindqvist@nordljus.example",
         "comment": "Nybörjare på topptur, vill gå lavinkursen först.",
         "sub_caller": "Anna", "organisations": ["4"], "categories": ["prospect-talked", "seg-student"],
         "personality_type": 1, "filters": [4], "tags": ["nybörjare"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "gustav", "user_id": "FV-1978", "first_name": "Gustav", "last_name": "Eklund",
         "email": "gustav.eklund@post.example", "phone": "+46701740644",
         "description_phone": "Mobil, kvällstid", "location": "Trondheim", "contributes": 6,
         "team": "bokning", "assigned": "anna.lindqvist@nordljus.example",
         "comment": "Bor i Norge, kommer över gränsen för helgturer.",
         "sub_caller": "Anna", "organisations": [], "categories": ["active-rare", "seg-private"],
         "personality_type": 3, "filters": [1, 6], "tags": ["norge"],
         "extra": {"newsletter": "true", "gdpr_consent": "true"}},
        {"key": "ida", "user_id": "FV-2130", "first_name": "Ida", "last_name": "Hansson",
         "email": "ida.hansson@post.example", "phone": "+46701740645",
         "description_phone": "Mobil", "location": "Gävle", "contributes": None,
         "team": None, "assigned": None,
         "comment": "Intresseanmälan från mässan. Inte tilldelad ännu.",
         "sub_caller": "", "organisations": [], "categories": ["prospect-new", "seg-private"],
         "personality_type": 1, "filters": [2], "tags": ["mässa"],
         "extra": {"gdpr_consent": "true"}},
    ],

    "selections": [
        ("linnea", "topptur", COMING, 4, -20),
        ("linnea", "klubb", COMING, 4, -140),
        ("oscar", "topptur", COMING, 5, -8),
        ("oscar", "after_ski", INTERESTED, None, None),
        ("amanda", "lavinkurs", COMING, 5, -4),
        ("amanda", "topptur", INTERESTED, None, None),
        ("gustav", "klubb", COMING, 5, -30),
        ("gustav", "after_ski", NOT_INTERESTED, None, None),
    ],

    "calls": [
        ("linnea", "bokning", (-20, 12, 15), ANSWER, "Bokade toppturshelgen, betalade direkt. Vegetarisk kost."),
        ("oscar", "bokning", (-8, 9, 30), ANSWER, "Fyra platser till toppturshelgen för byrån. Faktura till Lindahl Revision."),
        ("amanda", "bokning", (-4, 18, 5), ANSWER, "Anmäld till lavinkursen. Vill låna utrustning, hänvisad till uthyrningen."),
        ("gustav", "bokning", (-11, 19, 20), NO_ANSWER, "Inget svar. Provar igen på kvällstid."),
        ("gustav", "bokning", (-2, 19, 45), OUTSIDE, "Ringde tillbaka. Förnyar klubbmedlemskapet, kan inte komma på säsongspremiären."),
    ],

    "alarms": [
        ("oscar", "after_ski", "bokning", (3, 10, 0), 30, "Fråga om byrån vill komma på säsongspremiären."),
        ("amanda", "topptur", "bokning", (12, 15, 0), 30, "Följ upp efter lavinkursen – redo för topptur?"),
        ("gustav", "klubb", "bokning", (20, 18, 30), 60, "Påminn om obetald klubbavgift."),
        ("linnea", "lavinkurs", "bokning", (28, 11, 0), 30, "Tipsa om lavinkursen, hon har frågat om repetition."),
    ],

    "companies": [
        {"key": "lindahl", "team": "ekonomi", "first_name": "Oscar", "last_name": "Lindahl",
         "email": "oscar.lindahl@lindahlrevision.example", "phone": "+4660465012",
         "comment": "Årlig konferensresa i mars.",
         "extra": {"company_name": "Lindahl Revision AB", "org_nr": "5567018842",
                   **_address("Storgatan 18", "", "852 30", "Sundsvall"),
                   "cc_email": "ekonomi@lindahlrevision.example"}},
        {"key": "jamtkraft", "team": "ekonomi", "first_name": "Helena", "last_name": "Sundin",
         "email": "helena.sundin@jamtenergi.example", "phone": "+4663465031",
         "comment": "Personalaktiviteter två gånger per år.",
         "extra": {"company_name": "Jämtlands Energi & Värme AB", "org_nr": "5561927365",
                   **_address("Kyrkgatan 21", "Box 394", "831 25", "Östersund"),
                   "cc_email": ""}},
        {"key": "fjallstation", "team": "ekonomi", "first_name": "Rolf", "last_name": "Backman",
         "email": "rolf.backman@storulvan.example", "phone": "+46647465070",
         "comment": "Samarbetspartner för logi. Vi fakturerar provision kvartalsvis.",
         "extra": {"company_name": "Storulvåns Fjällstation", "org_nr": "8024015509",
                   **_address("Storulvån 150", "", "837 99", "Duved"),
                   "cc_email": ""}},
        {"key": "trondheim", "team": "ekonomi", "first_name": "Kari", "last_name": "Nilsen",
         "email": "kari.nilsen@trondelagtur.example", "phone": "+4773465090",
         "comment": "Norsk researrangör. Faktureras i EUR.",
         "extra": {"company_name": "Trøndelag Tur og Fjell AS", "org_nr": "NO918274650MVA",
                   **_address("Kjøpmannsgata 34", "", "7011", "Trondheim", "Norge"),
                   "cc_email": "regnskap@trondelagtur.example"}},
    ],

    "invoices": [
        {"company": "jamtkraft", "team": "ekonomi", "date": -45, "due": -25, "status": OK,
         "vat": "25", "currency": "SEK", "note": "Personaldag i september.",
         "rows": [("Guidad vandring Åreskutan, heldag", "1450", "24"), ("Lunchpaket", "165", "24")]},
        {"company": "fjallstation", "team": "ekonomi", "date": -30, "due": -10, "status": OK,
         "vat": "25", "currency": "SEK", "note": "Provision kvartal 3 enligt avtal.",
         "rows": [("Förmedlingsprovision logi, 8 %", "21840", "1")]},
        {"company": "trondheim", "team": "ekonomi", "date": -12, "due": 8, "status": CANCELLED,
         "vat": "0", "currency": "EUR", "note": "Cancelled – tour postponed to next season.",
         "rows": [("Ski touring weekend, group of 8", "520", "8")]},
        {"company": "lindahl", "team": "ekonomi", "date": -8, "due": 12, "status": OK,
         "vat": "25", "currency": "SEK", "note": "Toppturshelg i Åre, fyra deltagare.",
         "rows": [("Toppturshelg i Åre", "5400", "4"), ("Hyra lavinutrustning", "450", "4")]},
        {"company": "lindahl", "team": "ekonomi", "date": 0, "due": 20, "status": PROCESSING,
         "vat": "25", "currency": "SEK", "note": "Tillägg: transfer från Åre Östersund Airport.",
         "rows": [("Transfer tur och retur", "2800", "1")]},
    ],
}


TENANTS = [NORDLJUS, FJALLVIND]


def demo_emails() -> list[str]:
    seen = []
    for tenant in TENANTS:
        for user in tenant["users"]:
            if user["email"] not in seen:
                seen.append(user["email"])
    return seen
