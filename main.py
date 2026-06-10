import streamlit as st
import pandas as pd
import numpy as np

# Gestion gracieuse de l'export PDF
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="EcoMetal Selector Pro", page_icon="🌱", layout="wide")

# --- MAPPING DES COLONNES POUR L'AFFICHAGE PRO ---
DISPLAY_MAP = {
    'Nom': 'Nom de l\'Alliage',
    'Famille': 'Famille Métallurgique',
    'Densite': 'Densité (kg/m³)',
    'Module_Young_GPa': 'Module de Young (GPa)',
    'Limite_Elastique_MPa': 'Limite Élastique (MPa)',
    'Temp_Fusion_C': 'Temp. de Fusion (°C)',
    'Conductivite_Thermique_W_mK': 'Conductivité (W/m·K)',
    'Empreinte_CO2': 'Empreinte CO₂ (kg/kg)',
    'Recyclabilite_pct': 'Recyclabilité (%)',
    'Prix_euro_kg': 'Prix moyen (€/kg)',
    'Score_Eco': 'Score Éco-Conception (/100)'
}

# --- CHARGEMENT ET PRÉPARATION DES DONNÉES ---
@st.cache_data
def charger_donnees():
    df = pd.read_csv('alliages_metalliques_4.csv', sep=';')
    
    if 'Famille' not in df.columns:
        df['Famille'] = 'Non spécifié'
        
    colonnes_a_nettoyer = [
        'Densite', 'Module_Young_GPa', 'Limite_Elastique_MPa', 
        'Empreinte_CO2', 'Prix_euro_kg', 'Temp_Fusion_C', 
        'Conductivite_Thermique_W_mK', 'Recyclabilite_pct'
    ]
    for col in colonnes_a_nettoyer:
        if col in df.columns:
            df[col] = df[col].replace(0, 1e-6)
            
    # Calcul des indices d'Ashby
    df['Indice_Traction'] = df['Limite_Elastique_MPa'] / df['Densite']
    df['Indice_Flexion'] = np.sqrt(df['Limite_Elastique_MPa']) / df['Densite']
    
    # Calcul du KPI : Score Eco-Conception (sur 100)
    # Formule : (Recyclabilité / 100) * (5 / Empreinte CO2) * 100 (Plafonné à 100)
    def calc_eco_score(row):
        score = (row['Recyclabilite_pct'] / 100) * (5 / row['Empreinte_CO2']) * 100
        return max(0, min(100, int(score)))
        
    df['Score_Eco'] = df.apply(calc_eco_score, axis=1)
    return df

df_initial = charger_donnees()
colonnes_brutes_affichage = list(DISPLAY_MAP.keys())

# --- GÉNÉRATEUR DE RAPPORT PDF ---
def generer_pdf(ref, alt, gain_co2, gain_prix):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rapport d'Eco-Conception : Substitution de Materiau", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"1. Materiau d'origine : {ref['Nom']}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"   - Empreinte carbone : {ref['Empreinte_CO2']} kg CO2/kg", ln=True)
    pdf.cell(0, 8, f"   - Prix moyen : {ref['Prix_euro_kg']} EUR/kg", ln=True)
    pdf.cell(0, 8, f"   - Limite Elastique : {ref['Limite_Elastique_MPa']} MPa", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"2. Alternative recommandee : {alt['Nom']}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"   - Nouvelle empreinte : {alt['Empreinte_CO2']} kg CO2/kg", ln=True)
    pdf.cell(0, 8, f"   - Nouveau prix : {alt['Prix_euro_kg']} EUR/kg", ln=True)
    pdf.cell(0, 8, f"   - Limite Elastique : {alt['Limite_Elastique_MPa']} MPa", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. Bilan et Gains estimes :", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"   -> Reduction de l'empreinte CO2 : {gain_co2:.1f} %", ln=True)
    pdf.cell(0, 8, f"   -> Reduction du cout matiere : {gain_prix:.1f} %", ln=True)
    
    # Encodage standard pour éviter les erreurs d'accents dans fpdf
    return bytes(pdf.output(dest='S').encode('latin-1', 'replace'))

# --- INTERFACE UTILISATEUR PRINCIPALE ---
st.title("🌱 EcoMetal Selector Pro")

# Expander d'Onboarding
with st.expander("👋 Comment utiliser cette plateforme ? (Guide Rapide)"):
    st.markdown("""
    **Bienvenue sur l'outil d'aide à la décision pour l'éco-conception.**
    * **Étape 1 :** Utilisez le menu latéral pour filtrer les familles de matériaux.
    * **Étape 2 :** Dans l'onglet *Substitution*, sélectionnez votre matériau actuel pour trouver un jumeau numérique plus responsable.
    * **Étape 3 :** Ajustez les tolérances techniques (mécaniques, thermiques).
    * **Étape 4 :** Téléchargez le rapport PDF pour justifier votre choix auprès de votre hiérarchie ou de vos clients.
    """)

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942232.png", width=80) # Icône générique
    st.header("⚙️ Configuration Globale")
    
    familles_disponibles = ['Toutes'] + sorted(df_initial['Famille'].unique().tolist())
    famille_choisie = st.selectbox("Filtrer par famille métallurgique :", familles_disponibles)
    
    st.write("---")
    st.markdown("### 🎯 Paramètres d'optimisation")
    objectif = st.radio(
        "Objectif principal de la substitution :",
        ["Réduire l'empreinte CO₂", "Réduire le prix (€/kg)"]
    )

if famille_choisie != 'Toutes':
    df_recherche = df_initial[df_initial['Famille'] == famille_choisie]
else:
    df_recherche = df_initial

# --- CRÉATION DES ONGLETS ---
tab1, tab2 = st.tabs(["🔄 Substitution Intelligente", "📐 Base de Données & Ashby"])

# --- ONGLET 1 : RECHERCHE PAR SIMILITUDE ---
with tab1:
    st.header("Analyse de substitution et Jumeau Numérique")
    
    liste_materiaux = df_recherche['Nom'].tolist()
    materiau_ref = st.selectbox("Sélectionnez le matériau de référence (votre nomenclature actuelle) :", liste_materiaux)
    row_ref = df_initial[df_initial['Nom'] == materiau_ref].iloc[0]
    
    st.markdown(f"#### 📊 Profil du matériau : **{materiau_ref}**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score Éco-Conception", f"{row_ref['Score_Eco']} /100", help="Basé sur l'empreinte carbone et la recyclabilité.")
    c2.metric("Limite Élastique", f"{row_ref['Limite_Elastique_MPa']} MPa")
    c3.metric("Empreinte CO₂", f"{row_ref['Empreinte_CO2']} kg/kg")
    c4.metric("Prix", f"{row_ref['Prix_euro_kg']} €/kg")
    
    st.write("---")
    st.markdown("### 🛠️ Tolérances du Cahier des Charges")
    
    c_check1, c_check2, c_check3 = st.columns(3)
    with c_check1:
        keep_mecha = st.checkbox("Conserver la résistance mécanique", value=True)
        tol_mecha = st.slider("Tolérance Limite Élastique (%)", 0, 50, 20, disabled=not keep_mecha)
    with c_check2:
        keep_thermal = st.checkbox("Conserver la tenue thermique", value=False)
        tol_thermal = st.slider("Tolérance Température de Fusion (%)", 0, 50, 20, disabled=not keep_thermal)
    with c_check3:
        keep_stiff = st.checkbox("Conserver la rigidité", value=False)
        tol_stiff = st.slider("Tolérance Module de Young (%)", 0, 50, 20, disabled=not keep_stiff)

    # Algorithme de recherche
    df_alt = df_initial[df_initial['Nom'] != materiau_ref].copy()
    if keep_mecha:
        df_alt = df_alt[df_alt['Limite_Elastique_MPa'] >= row_ref['Limite_Elastique_MPa'] * (1 - (tol_mecha / 100))]
    if keep_thermal:
        df_alt = df_alt[df_alt['Temp_Fusion_C'] >= row_ref['Temp_Fusion_C'] * (1 - (tol_thermal / 100))]
    if keep_stiff:
        df_alt = df_alt[df_alt['Module_Young_GPa'] >= row_ref['Module_Young_GPa'] * (1 - (tol_stiff / 100))]
        
    if objectif == "Réduire l'empreinte CO₂":
        df_alt = df_alt[df_alt['Empreinte_CO2'] < row_ref['Empreinte_CO2']].sort_values(by='Empreinte_CO2', ascending=True)
    else:
        df_alt = df_alt[df_alt['Prix_euro_kg'] < row_ref['Prix_euro_kg']].sort_values(by='Prix_euro_kg', ascending=True)

    if not df_alt.empty:
        meilleur_choix = df_alt.iloc[0]
        st.success(f"### 🎉 Alternative recommandée : **{meilleur_choix['Nom']}**")
        
        # Calcul des gains
        gain_co2 = ((row_ref['Empreinte_CO2'] - meilleur_choix['Empreinte_CO2']) / row_ref['Empreinte_CO2']) * 100
        gain_prix = ((row_ref['Prix_euro_kg'] - meilleur_choix['Prix_euro_kg']) / row_ref['Prix_euro_kg']) * 100
        
        col_gain1, col_gain2, col_gain3 = st.columns(3)
        col_gain1.metric("Nouvelle Empreinte CO₂", f"{meilleur_choix['Empreinte_CO2']} kg/kg", f"-{gain_co2:.1f}% CO₂", delta_color="inverse")
        col_gain2.metric("Nouveau Prix", f"{meilleur_choix['Prix_euro_kg']} €/kg", f"{'-' if gain_prix > 0 else '+'}{abs(gain_prix):.1f}% coût", delta_color="inverse")
        col_gain3.metric("Nouveau Score Éco", f"{meilleur_choix['Score_Eco']} /100", f"{meilleur_choix['Score_Eco'] - row_ref['Score_Eco']} pts")
        
        # Bouton d'export PDF
        if HAS_FPDF:
            pdf_bytes = generer_pdf(row_ref, meilleur_choix, gain_co2, gain_prix)
            st.download_button(
                label="📄 Télécharger le Rapport d'Audit (PDF)",
                data=pdf_bytes,
                file_name=f"Rapport_Substitution_{materiau_ref.replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("⚠️ Module PDF non installé. Exécutez 'uv pip install fpdf' pour activer l'export.")
            
        st.write("**Aperçu des autres alternatives viables :**")
        # Affichage avec renommage propre
        df_alt_display = df_alt[colonnes_brutes_affichage].rename(columns=DISPLAY_MAP)
        st.dataframe(df_alt_display, use_container_width=True)
    else:
        st.info("Aucun autre alliage ne permet d'améliorer ce critère avec ces tolérances. Essayez d'élargir les pourcentages.")

# --- ONGLET 2 : FILTRAGE STRICT & ASHBY ---
with tab2:
    st.header("Exploration de la base de données")
    
    st.markdown("### 📈 Optimisation Structurelle (Méthode d'Ashby)")
    type_indice = st.selectbox(
        "Sélectionnez un indice de performance pour l'allègement :",
        ["Aucun - Tri standard", "Composant en Traction pure (Maximiser Re / ρ)", "Composant en Flexion pure (Maximiser √Re / ρ)"]
    )
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### ⚙️ Mécanique")
        limite_elastique_min = st.slider("Limite Élastique Min (MPa)", int(df_initial['Limite_Elastique_MPa'].min()), int(df_initial['Limite_Elastique_MPa'].max()), int(df_initial['Limite_Elastique_MPa'].min()))
        module_young_min = st.slider("Module de Young Min (GPa)", int(df_initial['Module_Young_GPa'].min()), int(df_initial['Module_Young_GPa'].max()), int(df_initial['Module_Young_GPa'].min()))
    with c2:
        st.markdown("### 🌡️ Thermique")
        temp_fusion_min = st.slider("Temp. de Fusion Min (°C)", int(df_initial['Temp_Fusion_C'].min()), int(df_initial['Temp_Fusion_C'].max()), int(df_initial['Temp_Fusion_C'].min()))
        conductivite_min = st.slider("Conductivité Min (W/m·K)", int(df_initial['Conductivite_Thermique_W_mK'].min()), int(df_initial['Conductivite_Thermique_W_mK'].max()), int(df_initial['Conductivite_Thermique_W_mK'].min()))
    with c3:
        st.markdown("### 🌱 Éco & Coûts")
        empreinte_co2_max = st.slider("Empreinte CO₂ Max (kg/kg)", float(df_initial['Empreinte_CO2'].min()), float(df_initial['Empreinte_CO2'].max()), float(df_initial['Empreinte_CO2'].max()))
        score_eco_min = st.slider("Score Éco-Conception Min (/100)", 0, 100, 0)
        prix_max = st.slider("Prix Max (€/kg)", float(df_initial['Prix_euro_kg'].min()), float(df_initial['Prix_euro_kg'].max()), float(df_initial['Prix_euro_kg'].max()))
        
    df_filtre = df_initial[
        (df_initial['Limite_Elastique_MPa'] >= limite_elastique_min) &
        (df_initial['Module_Young_GPa'] >= module_young_min) &
        (df_initial['Temp_Fusion_C'] >= temp_fusion_min) &
        (df_initial['Conductivite_Thermique_W_mK'] >= conductivite_min) &
        (df_initial['Empreinte_CO2'] <= empreinte_co2_max) &
        (df_initial['Score_Eco'] >= score_eco_min) &
        (df_initial['Prix_euro_kg'] <= prix_max)
    ].copy()
    
    if type_indice == "Composant en Traction pure (Maximiser Re / ρ)":
        df_filtre = df_filtre.sort_values(by='Indice_Traction', ascending=False)
    elif type_indice == "Composant en Flexion pure (Maximiser √Re / ρ)":
        df_filtre = df_filtre.sort_values(by='Indice_Flexion', ascending=False)

    st.subheader(f"📊 {len(df_filtre)} matériau(x) valide(s)")
    
    if not df_filtre.empty:
        # Affichage du tableau formaté
        df_filtre_display = df_filtre[colonnes_brutes_affichage].rename(columns=DISPLAY_MAP)
        st.dataframe(df_filtre_display, use_container_width=True)
        
        # Export CSV Propre
        csv_data = df_filtre_display.to_csv(index=False, sep=';').encode('utf-8')
        st.download_button(
            label="📥 Exporter les résultats (CSV)",
            data=csv_data,
            file_name="Audit_Eco_Conception.csv",
            mime="text/csv"
        )
        
        st.write("### 📈 Matrice d'aide à la décision : Résistance vs CO₂")
        st.scatter_chart(df_filtre, x='Empreinte_CO2', y='Limite_Elastique_MPa', color='Famille')
    else:
        st.warning("Aucun alliage ne correspond. Essayez d'assouplir certains curseurs.")