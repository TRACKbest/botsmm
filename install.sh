#!/data/data/com.termux/files/usr/bin/bash

# Mettre à jour Termux et installer les outils de base
echo "Mise à jour de Termux et installation des outils de base..."
pkg update -y && pkg upgrade -y
pkg install -y python build-essential

# Vérifier si Python est bien installé
if ! command -v python3 &> /dev/null; then
    echo "Erreur : Python n'a pas pu être installé."
    exit 1
fi

# Installer pip (assurez-vous qu'il est à jour)
echo "Installation de pip..."
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip

# Installer les dépendances Python
echo "Installation des dépendances Python (telethon, instagrapi)..."
python3 -m pip install telethon instagrapi

# Vérifier l'installation des dépendances
echo "Vérification des dépendances installées..."
if python3 -c "import telethon; import instagrapi" 2>/dev/null; then
    echo "Toutes les dépendances ont été installées avec succès !"
else
    echo "Erreur lors de l'installation des dépendances. Veuillez vérifier les logs ci-dessus."
    exit 1
fi

echo "Installation terminée ! Vous pouvez maintenant exécuter bot.py avec : python3 volo.py"