import getpass
import json
import os
import uuid
from statistics import mean

# --- Fonctions utilitaires ---

def valider_mot_de_passe(first, second):
    return first == second

def valider_note_range(note):
    try:
        note_float = float(note)
        return 0 <= note_float <= 20
    except ValueError:
        return False

# --- Classes Logique & Données ---

class LoaderSave:
    def __init__(self, chemin=None):
        base_path = os.path.expanduser("~/DATABASE.json")
        self.chemin = os.path.expanduser(chemin) if chemin else base_path
        
    def loader_donnee(self):
        try:
            if os.path.exists(self.chemin):
                with open(self.chemin, "r", encoding="utf-8") as donnee:
                    contenu_brut = donnee.read().strip()
                    return json.loads(contenu_brut) if contenu_brut else {}
            return {}
        except Exception:
            return {}

    def save_donnee(self, a_ajouter):
        try:
            os.makedirs(os.path.dirname(self.chemin), exist_ok=True)
            with open(self.chemin, "w", encoding="utf-8") as charger:
                json.dump(a_ajouter, charger, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False

class BASEDEDONEE:
    """Logique pure : aucune interaction UI (print/input)"""
    def __init__(self):
        self.gestionnaire = LoaderSave() 
        self.bd = self.gestionnaire.loader_donnee()

    def _recharger_bd(self):
        self.bd = self.gestionnaire.loader_donnee()

    def _sauvegarder_bd(self):
        return self.gestionnaire.save_donnee(self.bd)

    def verify(self, ID):
        self._recharger_bd()
        return str(ID) in self.bd

    def get_eleve(self, ID):
        self._recharger_bd()
        return self.bd.get(str(ID))

    def ajouter_a_la_base(self, nom, prenom, age, sexe, classe, mot_de_passe, ID):
        self._recharger_bd()
        self.bd[str(ID)] = {
            "Nom": nom, "Prenom": prenom, "Age": age, "Sexe": sexe,
            "Classe": classe, "Mot de passe": mot_de_passe,
            "Notes": {},
        }
        return self._sauvegarder_bd()

    def ajouter_note(self, ID, matiere, note, type_note="Interro"):
        self._recharger_bd()
        ID_str = str(ID)
        if ID_str not in self.bd: return False

        notes_eleve = self.bd[ID_str]["Notes"]
        if matiere not in notes_eleve:
            notes_eleve[matiere] = {"Interro": [], "Devoir": [], "MI": None, "MD": None, "MM": None}

        notes_eleve[matiere][type_note].append(note)
        
        # Correction : On ne calcule la moyenne que si la liste n'est pas vide
        liste_notes = notes_eleve[matiere][type_note]
        if liste_notes:
            cle_moyenne = "MI" if type_note == "Interro" else "MD"
            notes_eleve[matiere][cle_moyenne] = mean(liste_notes)

        return self._sauvegarder_bd()

    def calculer_moyenne_generale(self, ID, matiere):
            """
            Calcule la moyenne de l'élève pour une matière donnée.
            Retourne :
                - float : La moyenne calculée (MM).
                - False : Si aucune note (MI ou MD) n'est disponible.
                - None  : Si l'ID ou la matière n'existe pas.
            """
            self._recharger_bd()
            ID_str = str(ID)
            
            # Vérification d'existence
            if ID_str not in self.bd or matiere not in self.bd[ID_str]["Notes"]:
                return None

            notes = self.bd[ID_str]["Notes"][matiere]
            mi = notes.get("MI")
            md = notes.get("MD")

            # Logique de calcul flexible :
            # 1. Si les deux moyennes existent
            if mi is not None and md is not None:
                moyenne = (mi + md) / 2
            # 2. Si seule l'interro existe
            elif mi is not None:
                moyenne = mi
            # 3. Si seul le devoir existe
            elif md is not None:
                moyenne = md
            # 4. Aucune note disponible
            else:
                return None

            # Mise à jour et sauvegarde
            notes["MM"] = moyenne
            self._sauvegarder_bd()
            return moyenne

    def supprimer_compte(self, ID):
        self._recharger_bd()
        if str(ID) in self.bd:
            del self.bd[str(ID)]
            return self._sauvegarder_bd()
        return False

# --- Classe Interface Utilisateur (UI) ---

class Gestion:
    def __init__(self):
        self.bd = BASEDEDONEE() 
        self.menu_principal()

    def menu_principal(self):
        while True:
            print("\n--- GESTION SCOLAIRE ---")
            print("1. Inscrire un élève\n2. Connexion\n3. Quitter")
            choix = input("~ Choix : ")

            if choix == "1":
                self.action_inscription()
            elif choix == "2":
                self.action_connexion()
            elif choix == "3":
                break

    def action_inscription(self):
        nom, prenom, age, sexe, classe, mdp = self.information_inscription()
        id_genere = str(uuid.uuid4())
        if self.bd.ajouter_a_la_base(nom, prenom, age, sexe, classe, mdp, id_genere):
            print(f"\n✅ Inscription réussie ! ID à conserver : {id_genere}")

    def action_connexion(self):
        id_user = input("ID : ")
        mdp_saisi = getpass.getpass("Mot de passe : ")
        eleve = self.bd.get_eleve(id_user)
        
        if eleve and valider_mot_de_passe(mdp_saisi, eleve["Mot de passe"]):
            self.menu_eleve(id_user)
        else:
            print("❌ Identifiants invalides.")

    def menu_eleve(self, id_user):
        while True:
            print(f"\n=== SESSION : {id_user} ===")
            print("1. Voir notes\n2. Ajouter Interro\n3. Ajouter Devoir\n4. Calculer Moyenne\n5. Déconnexion\n6. Supprimer compte")
            action = input("~ Action : ")

            if action == "1":
                self.UI_afficher_notes(id_user)
            elif action in ["2", "3"]:
                self.UI_ajouter_note(id_user, "Interro" if action == "2" else "Devoir")
            elif action == "4":
                self.UI_calculer_moyenne(id_user)
            elif action == "5":
                break
            elif action == "6":
                if input("Confirmer suppression ? (y/n) : ").lower() == 'y':
                    if self.bd.supprimer_compte(id_user):
                        print("Compte supprimé.")
                        break

    def UI_afficher_notes(self, id_user):
            eleve = self.bd.get_eleve(id_user)
            
            # Sécurité : vérifier si l'élève existe bien dans la base
            if not eleve:
                print("❌ Erreur : Impossible de trouver les données de l'élève.")
                return

            matiere_filtre = input("Matière (ou Entrée pour tout) : ").strip().upper()
            
            print(f"\n{'='*40}")
            print(f"RELEVÉ DE NOTES : {eleve['Prenom']} {eleve['Nom']}")
            print(f"{'='*40}")

            notes_dict = eleve.get("Notes", {}) # Sécurité sur la clé Notes

            if not notes_dict:
                print("Aucune note enregistrée pour le moment.")
                return

            trouve = False
            for mat, data in notes_dict.items():
                # Gestion du filtre
                if matiere_filtre and mat != matiere_filtre:
                    continue
                
                trouve = True
                mi = f"{data['MI']:.2f}" if data.get('MI') is not None else "N/A"
                md = f"{data['MD']:.2f}" if data.get('MD') is not None else "N/A"
                
                print(f"📚 {mat}")
                print(f"   - Interros : {data['Interro']} (Moyenne : {mi}/20)")
                print(f"   - Devoirs  : {data['Devoir']} (Moyenne : {md}/20)")
                
                if data.get('MM'):
                    print(f"   👉 MOYENNE GÉNÉRALE : {data['MM']:.2f}/20")
                print("-" * 20)

            if matiere_filtre and not trouve:
                print(f"Aucune donnée trouvée pour la matière : {matiere_filtre}")

    def UI_ajouter_note(self, id_user, type_n):
        mat = input("Matière : ").upper()
        note = input("Note (0-20) : ")
        if valider_note_range(note):
            if self.bd.ajouter_note(id_user, mat, float(note), type_n):
                print(f"✅ {type_n} ajoutée.")
        else:
            print("❌ Valeur incorrecte.")

    def UI_calculer_moyenne(self, id_user):
            mat = input("Matière : ").strip().upper()
            resultat = self.bd.calculer_moyenne_generale(id_user, mat)
            
            if isinstance(resultat, float):
                print(f"✅ Moyenne de {mat} calculée : {resultat:.2f}/20")
            elif resultat is False:
                print(f"⚠️ Impossible de calculer : aucune note enregistrée en {mat}.")
            else:
                print(f"❌ Erreur : La matière '{mat}' n'existe pas dans votre dossier.")

    def information_inscription(self):
        nom = input("Nom: "); prenom = input("Prenom: "); age = input("Age: ")
        sexe = input("Sexe (M/F): "); classe = input("Classe: ")
        while True:
            mdp1 = getpass.getpass("Mot de passe: ")
            if valider_mot_de_passe(mdp1, getpass.getpass("Confirmer: ")):
                return nom, prenom, age, sexe, classe, mdp1
            print("❌ Erreur mot de passe.")

