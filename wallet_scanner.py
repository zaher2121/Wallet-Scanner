import random
import time
import logging
from web3 import Web3
from bip44 import Wallet
from mnemonic import Mnemonic
import concurrent.futures
import os

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. إعدادات السجلات والملفات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
logging.basicConfig(
    filename='scan.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

FILE_PATH = 'english.txt'
mnemo = Mnemonic("english")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. تحميل وتفقد ملف الكلمات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def load_wordlist():
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            word_list = [word.strip() for word in f if word.strip()]
            
        if len(word_list) != 2048:
            raise ValueError("يجب أن يحتوي الملف على 2048 كلمة بالضبط!")
            
        if not all(word in mnemo.wordlist for word in word_list):
            invalid = [word for word in word_list if word not in mnemo.wordlist]
            raise ValueError(f"كلمات غير صالحة: {invalid[:3]}...")
            
        print(f"✅ تم تحميل {len(word_list)} كلمة بنجاح")
        return word_list
        
    except Exception as e:
        logging.error(f"خطأ في تحميل الملف: {str(e)}")
        raise

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. إعدادات الشبكات
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NETWORKS = {
    'ethereum': {
        'url': 'https://rpc.ankr.com/eth',
        'symbol': 'ETH',
        'scan': 'https://etherscan.io/address/'
    },
    'bsc': {
        'url': 'https://bsc-dataseed4.defibit.io',
        'symbol': 'BNB',
        'scan': 'https://bscscan.com/address/'
    }
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. الدوال الأساسية
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_mnemonic(word_list):
    for _ in range(10):
        words = random.sample(word_list, 12)
        phrase = " ".join(words)
        if mnemo.check(phrase):
            return phrase
    raise RuntimeError("فشل في إنشاء عبارة سرية صالحة")

def check_balance(network, address):
    try:
        w3 = Web3(Web3.HTTPProvider(network['url'], request_kwargs={'timeout': 5}))
        balance = w3.eth.get_balance(address)
        return balance / 1e18, network['symbol']
    except Exception as e:
        logging.warning(f"خطأ في الشبكة {network['symbol']}: {str(e)}")
        return 0, None

def scan_wallets(word_list):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        attempt = 0
        while True:
            try:
                attempt += 1
                phrase = generate_mnemonic(word_list)
                seed = mnemo.to_seed(phrase)
                wallet = Wallet(seed)
                address = wallet.derive_account("eth")['address']
                
                if attempt % 50 == 0:
                    status = f"المحاولة: {attempt} | العنوان: {address[:6]}...{address[-4:]}"
                    print(status)
                    logging.info(status)
                
                futures = {
                    executor.submit(check_balance, network, address): network 
                    for network in NETWORKS.values()
                }
                
                for future in concurrent.futures.as_completed(futures):
                    balance, symbol = future.result()
                    if balance > 0:
                        network_name = next(k for k, v in NETWORKS.items() if v['symbol'] == symbol)
                        report = (
                            f"\n🔥 تم العثور على رصيد! 🔥\n"
                            f"📝 العبارة: {phrase}\n"
                            f"🌐 الشبكة: {network_name}\n"
                            f"📍 العنوان: {address}\n"
                            f"💰 الرصيد: {balance:.6f} {symbol}\n"
                            f"🔗 الرابط: {NETWORKS[network_name]['scan']}{address}"
                        )
                        print(report)
                        logging.critical(report)
                        return True
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\nتم إيقاف العملية بواسطة المستخدم")
                exit()
            except Exception as e:
                logging.error(f"خطأ غير متوقع: {str(e)}")
                time.sleep(1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. بدء التشغيل
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    print("""
    ░█████╗░██╗░░██╗███████╗██████╗░██╗░░██╗
    ██╔══██╗██║░░██║██╔════╝██╔══██╗╚██╗██╔╝
    ██║░░╚═╝███████║█████╗░░██████╔╝░╚███╔╝░
    ██║░░██╗██╔══██║██╔══╝░░██╔═══╝░░██╔██╗░
    ╚█████╔╝██║░░██║███████╗██║░░██╗██╔╝╚██╗
    ░╚════╝░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝
    """)
    try:
        words = load_wordlist()
        scan_wallets(words)
    except Exception as e:
        print(f"❌ خطأ فادح: {str(e)}")
        logging.critical(f"إيقاف البرنامج بسبب: {str(e)}")
