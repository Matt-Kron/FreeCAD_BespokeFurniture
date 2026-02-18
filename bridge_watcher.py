import os, time, json, subprocess

TRIGGER_FILE = "/home/matthou/snap/freecad/common/bridge_trigger.json"
BRIDGE_SCRIPT = "/home/matthou/snap/freecad/common/bridge_calc.py"

print(f"👀 Surveillant actif... (En attente sur : {TRIGGER_FILE})")

subprocess.Popen('soffice --accept="socket,host=localhost,port=2002;urp;"', shell=True)

while True:
    if os.path.exists(TRIGGER_FILE):
        # On attend que le fichier ne soit plus vide (écriture terminée)
        attempts = 0
        while os.path.getsize(TRIGGER_FILE) == 0 and attempts < 10:
            time.sleep(0.1)
            attempts += 1

        print("📥 Données détectées !")

        # On lance le pont en passant le CHEMIN du fichier, pas le contenu directement
        # pour éviter les erreurs de guillemets dans le terminal
        result = subprocess.run(["python3", BRIDGE_SCRIPT, TRIGGER_FILE],
                                capture_output=True, text=True)

        if result.stdout: print(f"STDOUT: {result.stdout}")
        if result.stderr: print(f"❌ STDERR: {result.stderr}")

        if os.path.exists(TRIGGER_FILE):
            os.remove(TRIGGER_FILE)
        print("✨ Prêt.\n")

    time.sleep(0.3)
