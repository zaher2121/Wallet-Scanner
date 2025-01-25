import random
from web3 import Web3
from bip44 import Wallet
from mnemonic import Mnemonic
import concurrent.futures
import os

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. التأكد من وجود الملف وتحميله
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
file_path = '/content/english.txt'

if not os.path.exists(file_path):
    raise FileNotFoundError(f"الملف {file_path} غير موجود! الرجاء رفعه أولاً.")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. قراءة الملف بالترميز الصحيح
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
try:
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        word_list = [word.strip() for word in f.readlines()]
    print(f"✅ تم تحميل {len(word_list)} كلمة بنجاح!")
except Exception as e:
    print(f"❌ خطأ في قراءة الملف: {e}")
    raise

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. التحقق من توافق القائمة مع BIP39
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
mnemo = Mnemonic("english")
valid_words = set(mnemo.wordlist)
if not all(word in valid_words for word in word_list):
    invalid_words = [word for word in word_list if word not in valid_words]
    print(f"❌ يوجد {len(invalid_words)} كلمات غير صالحة في القائمة!")
    raise ValueError("القائمة غير متوافقة مع معيار BIP39!")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. إعدادات الشبكات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NETWORKS = {
    'ethereum': {'url': 'https://cloudflare-eth.com', 'symbol': 'ETH'},
    'bsc': {'url': 'https://bsc-dataseed.binance.org', 'symbol': 'BNB'},
    'polygon': {'url': 'https://polygon-rpc.com', 'symbol': 'MATIC'}
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. الدوال الأساسية (مُحسَّنة)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_valid_mnemonic(word_list):
    while True:
        words = random.sample(word_list, 12)
        phrase = " ".join(words)
        if mnemo.check(phrase):
            return phrase

def check_network_balance(network, address):
    try:
        w3 = Web3(Web3.HTTPProvider(network['url'], request_kwargs={'timeout': 3}))
        balance = w3.eth.get_balance(address)
        return balance / 1e18, network['symbol']
    except:
        return 0, None

def scan_wallets(word_list):
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        while True:
            phrase = generate_valid_mnemonic(word_list)
            seed = mnemo.to_seed(phrase)
            wallet = Wallet(seed)
            address = wallet.derive_account("eth")['address']
            
            futures = {executor.submit(check_network_balance, network, address): network for network in NETWORKS.values()}
            
            for future in concurrent.futures.as_completed(futures):
                balance, symbol = future.result()
                if balance > 0:
                    network_name = [k for k, v in NETWORKS.items() if v['symbol'] == symbol][0]
                    print("\n══════════════════════════════════════")
                    print(f"🔥 تم العثور على محفظة برصيد! 🔥")
                    print(f"📝 العبارة السرية: {phrase}")
                    print(f"🌐 الشبكة: {network_name.upper()}")
                    print(f"📍 العنوان: {address}")
                    print(f"💰 الرصيد: {balance:.4f} {symbol}")
                    print("══════════════════════════════════════\n")
                    return True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. بدء الفحص
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("بدء الفحص... (قد يستغرق وقتاً غير واقعي! ⏳)")
scan_wallets(word_list)