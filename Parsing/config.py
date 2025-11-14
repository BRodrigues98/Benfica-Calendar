import pytz
TZ = pytz.timezone("Europe/Lisbon")

# Config the ICS URL(s)
# TODO: Put this in a .env or config
ECAL_URLS = [
    "https://ics.ecal.com/ecal-sub/6915f30f396fa00008c2a014/SL%20Benfica.ics"
]

BENFICA_NAME = "SL Benfica"

# keywords for segmentation
SPORT_KEYWORDS = [
    "Hóquei em Patins",
    "Andebol",
    "Futsal",
    "Basquetebol",
    "Voleibol",
    "Futebol",
    "Hóquei",
]

FOOTBALL_SQUAD_KEYWORDS = [
    "Equipa B",
    "Juniores",
    "Sub-19",
    "Sub-23",
    "Sub-17",
    "Sub-15",
    "Juvenis",
    "Iniciados",
]

FOOTBALL_COMP_KEYWORDS = [
    "liga portugal",
    "taça de portugal",
    "liga dos campeões",
    "liga dos campeoes",
    "liga revelação",
    "liga revelacao",
    "liga dos campeões feminina",
    "liga dos campeoes feminina",
    "liga dos campeões feminina uefa",
    "supertaça",
    "supertaca",
    "campeonato nacional feminino ii divisão",
    "campeonato nacional feminino ii divisao",
]

BROADCAST_KEYWORDS = [
    "📺",
    "BTV",
    "DAZN",
    "Sport TV",
    "Eleven",
    "Canal 11",
    "RTP",
    "SIC",
    "TVI",
    "Benfica TV",
]