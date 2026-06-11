import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.graph_objects as go

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
    df = pd.read_csv('alliages_metalliques_4_1.csv', sep=';')
    
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
            
    df['Indice_Traction'] = df['Limite_Elastique_MPa'] / df['Densite']
    df['Indice_Flexion'] = np.sqrt(df['Limite_Elastique_MPa']) / df['Densite']
    
    def calc_eco_score(row):
        score = (row['Recyclabilite_pct'] / 100) * (5 / row['Empreinte_CO2']) * 100
        return max(0, min(100, int(score)))
        
    df['Score_Eco'] = df.apply(calc_eco_score, axis=1)
    return df

df_initial = charger_donnees()
colonnes_brutes_affichage = list(DISPLAY_MAP.keys())

# --- GÉNÉRATEUR PDF 1 : SUBSTITUTION ---
def generer_pdf(ref, alt, gain_co2, gain_prix):
    pdf = FPDF()
    pdf.add_page()
    NOIR, GRIS = (30, 30, 30), (100, 100, 100)
    
    pdf.set_fill_color(46, 125, 50)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, "RAPPORT D'AUDIT : SUBSTITUTION ECO-RESPONSABLE", ln=True, align="C", fill=True)
    pdf.ln(5)
    
    pdf.set_text_color(*GRIS)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 6, f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} par EcoMetal Selector Pro", ln=True, align="R")
    pdf.ln(8)
    
    pdf.set_text_color(*NOIR)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "  1. ANALYSE DU MATERIAU ACTUEL", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.ln(3)
    pdf.cell(0, 6, f"   * Nom de l'alliage : {ref['Nom']} ({ref['Famille']})", ln=True)
    pdf.cell(0, 6, f"   * Score Eco : {ref['Score_Eco']} / 100 | CO2 : {ref['Empreinte_CO2']} kg/kg | Prix : {ref['Prix_euro_kg']} EUR/kg", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(200, 240, 200)
    pdf.cell(0, 10, "  2. ALTERNATIVE RECOMMANDEE", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.ln(3)
    pdf.cell(0, 6, f"   * Nom de l'alliage : {alt['Nom']} ({alt['Famille']})", ln=True)
    pdf.cell(0, 6, f"   * Score Eco : {alt['Score_Eco']} / 100 | CO2 : {alt['Empreinte_CO2']} kg/kg | Prix : {alt['Prix_euro_kg']} EUR/kg", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(255, 240, 200)
    pdf.cell(0, 10, "  3. BILAN DETAILLE DES GAINS", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.ln(3)
    pdf.cell(0, 8, f"   -> Environnement : {ref['Empreinte_CO2'] - alt['Empreinte_CO2']:.2f} kg CO2/kg economises", ln=True)
    pdf.cell(0, 8, f"   -> Economie : {ref['Prix_euro_kg'] - alt['Prix_euro_kg']:.2f} EUR/kg economises", ln=True)
    pdf.cell(0, 8, f"   -> Score RSE : +{alt['Score_Eco'] - ref['Score_Eco']} points", ln=True)
    
    return bytes(pdf.output(dest='S').encode('latin-1', 'replace'))

# --- GÉNÉRATEUR PDF 2 : CAHIER DES CHARGES ---
def generer_pdf_etude(df_top, criteres):
    pdf = FPDF()
    pdf.add_page()
    NOIR, GRIS = (30, 30, 30), (100, 100, 100)
    
    pdf.set_fill_color(25, 118, 210) # Bleu Ingénieur
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, "ETUDE DE FAISABILITE : CAHIER DES CHARGES MATERIAUX", ln=True, align="C", fill=True)
    pdf.ln(5)
    
    pdf.set_text_color(*GRIS)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 6, f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} par EcoMetal Selector Pro", ln=True, align="R")
    pdf.ln(8)
    
    pdf.set_text_color(*NOIR)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "  1. RAPPEL DES CONTRAINTES DU PROJET", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.ln(3)
    for cle, valeur in criteres.items():
        pdf.cell(0, 6, f"   * {cle} : {valeur}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(0, 10, "  2. LE TOP 5 DES MEILLEURS CANDIDATS", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.ln(3)
    
    for i, (_, row) in enumerate(df_top.head(5).iterrows(), 1):
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, f"  #{i} - {row['Nom']} ({row['Famille']})", ln=True)
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 5, f"        Re: {row['Limite_Elastique_MPa']} MPa | CO2: {row['Empreinte_CO2']} kg | Prix: {row['Prix_euro_kg']} EUR | Score: {row['Score_Eco']}/100", ln=True)
        pdf.ln(2)
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_fill_color(255, 240, 200)
    pdf.cell(0, 10, "  3. RECOMPENSES & SPECIFICITES", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.ln(3)
    
    best_co2 = df_top.loc[df_top['Empreinte_CO2'].idxmin()]
    best_prix = df_top.loc[df_top['Prix_euro_kg'].idxmin()]
    best_re = df_top.loc[df_top['Limite_Elastique_MPa'].idxmax()]
    
    pdf.cell(0, 7, f"   -> Le plus ecologique : {best_co2['Nom']} ({best_co2['Empreinte_CO2']} kg CO2/kg)", ln=True)
    pdf.cell(0, 7, f"   -> Le plus economique : {best_prix['Nom']} ({best_prix['Prix_euro_kg']} EUR/kg)", ln=True)
    pdf.cell(0, 7, f"   -> Le plus resistant : {best_re['Nom']} ({best_re['Limite_Elastique_MPa']} MPa)", ln=True)
    
    return bytes(pdf.output(dest='S').encode('latin-1', 'replace'))

# --- INTERFACE UTILISATEUR PRINCIPALE ---
st.title("🌱 EcoMetal Selector Pro")

with st.expander("👋 Comment utiliser cette plateforme ?"):
    st.markdown("""
    * **Étape 1 :** Utilisez le menu latéral pour filtrer les familles.
    * **Étape 2 :** Onglet *Substitution* pour trouver un jumeau numérique responsable.
    * **Étape 3 :** Onglet *Base de données* pour faire une étude de faisabilité complète à partir de zéro.
    """)

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942232.png", width=80) 
    st.header("⚙️ Configuration Globale")
    familles_disponibles = ['Toutes'] + sorted(df_initial['Famille'].unique().tolist())
    famille_choisie = st.selectbox("Filtrer par famille métallurgique :", familles_disponibles)
    
    st.write("---")
    st.markdown("### 🎯 Paramètres d'optimisation")
    objectif = st.radio("Objectif principal de la substitution :", ["Réduire l'empreinte CO₂", "Réduire le prix (€/kg)"])

df_recherche = df_initial[df_initial['Famille'] == famille_choisie] if famille_choisie != 'Toutes' else df_initial

# --- CRÉATION DES ONGLETS ---
tab1, tab2 = st.tabs(["🔄 Substitution Intelligente", "📐 Étude & Cahier des Charges"])

# --- ONGLET 1 : RECHERCHE PAR SIMILITUDE ---
with tab1:
    st.header("Analyse de substitution et Jumeau Numérique")
    
    col_sel, col_tol = st.columns([1, 2])
    with col_sel:
        liste_materiaux = df_recherche['Nom'].tolist()
        materiau_ref = st.selectbox("Sélectionnez le matériau de référence :", liste_materiaux)
        row_ref = df_initial[df_initial['Nom'] == materiau_ref].iloc[0]
        
    with col_tol:
        st.write("**Tolérances Mécaniques & Thermiques :**")
        c_check1, c_check2, c_check3 = st.columns(3)
        with c_check1:
            keep_mecha = st.checkbox("Conserver Résistance", value=True)
            tol_mecha = st.slider("Tolérance Re (%)", 0, 50, 20, disabled=not keep_mecha)
        with c_check2:
            keep_thermal = st.checkbox("Conserver Tenue Thermique", value=False)
            tol_thermal = st.slider("Tolérance Fusion (%)", 0, 50, 20, disabled=not keep_thermal)
        with c_check3:
            keep_stiff = st.checkbox("Conserver Rigidité", value=False)
            tol_stiff = st.slider("Tolérance Young (%)", 0, 50, 20, disabled=not keep_stiff)

    df_alt = df_initial[df_initial['Nom'] != materiau_ref].copy()
    if keep_mecha: df_alt = df_alt[df_alt['Limite_Elastique_MPa'] >= row_ref['Limite_Elastique_MPa'] * (1 - (tol_mecha / 100))]
    if keep_thermal: df_alt = df_alt[df_alt['Temp_Fusion_C'] >= row_ref['Temp_Fusion_C'] * (1 - (tol_thermal / 100))]
    if keep_stiff: df_alt = df_alt[df_alt['Module_Young_GPa'] >= row_ref['Module_Young_GPa'] * (1 - (tol_stiff / 100))]
        
    if objectif == "Réduire l'empreinte CO₂":
        df_alt = df_alt[df_alt['Empreinte_CO2'] < row_ref['Empreinte_CO2']].sort_values(by='Empreinte_CO2', ascending=True)
    else:
        df_alt = df_alt[df_alt['Prix_euro_kg'] < row_ref['Prix_euro_kg']].sort_values(by='Prix_euro_kg', ascending=True)

    if not df_alt.empty:
        meilleur_choix = df_alt.iloc[0]
        st.success(f"### 🎉 Alternative recommandée : **{meilleur_choix['Nom']}**")
        
        # --- L'ATOUT VISUEL : GRAPHIQUE RADAR ---
        st.markdown("### 🕸️ Comparaison des profils de performance")
        categories = ['Résistance (Re)', 'Rigidité (Young)', 'Éco-Score', 'Légèreté (Inv. Densité)', 'Économie (Inv. Prix)']
        
        # Normalisation pour que la référence soit toujours un pentagone parfait à 100%
        # Pour Légèreté et Économie, "plus petit" est "mieux", donc on inverse le ratio.
        vals_ref = [100, 100, 100, 100, 100]
        vals_alt = [
            (meilleur_choix['Limite_Elastique_MPa'] / row_ref['Limite_Elastique_MPa']) * 100,
            (meilleur_choix['Module_Young_GPa'] / row_ref['Module_Young_GPa']) * 100,
            (meilleur_choix['Score_Eco'] / row_ref['Score_Eco']) * 100 if row_ref['Score_Eco'] > 0 else 100,
            (row_ref['Densite'] / meilleur_choix['Densite']) * 100,       # Moins dense = Mieux
            (row_ref['Prix_euro_kg'] / meilleur_choix['Prix_euro_kg']) * 100 # Moins cher = Mieux
        ]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=vals_ref, theta=categories, fill='toself', name=row_ref['Nom'], line_color='gray'))
        fig.add_trace(go.Scatterpolar(r=vals_alt, theta=categories, fill='toself', name=meilleur_choix['Nom'], line_color='green'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, max(max(vals_alt), 120)])), showlegend=True, height=400, margin=dict(t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # --- Bouton PDF ---
        if HAS_FPDF:
            gain_co2 = ((row_ref['Empreinte_CO2'] - meilleur_choix['Empreinte_CO2']) / row_ref['Empreinte_CO2']) * 100
            gain_prix = ((row_ref['Prix_euro_kg'] - meilleur_choix['Prix_euro_kg']) / row_ref['Prix_euro_kg']) * 100
            pdf_bytes = generer_pdf(row_ref, meilleur_choix, gain_co2, gain_prix)
            st.download_button("📄 Télécharger le Rapport d'Audit (PDF)", data=pdf_bytes, file_name=f"Rapport_Substitution.pdf", mime="application/pdf", type="primary")
            
    else:
        st.info("Aucune alternative trouvée. Essayez d'élargir les tolérances.")

# --- ONGLET 2 : FILTRAGE STRICT & ASHBY ---
with tab2:
    st.header("Étude de Faisabilité & Cahier des Charges")
    
    type_indice = st.selectbox("Indice de performance (Méthode d'Ashby) :", ["Aucun - Tri standard", "Traction pure (Max Re / ρ)", "Flexion pure (Max √Re / ρ)"])
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### ⚙️ Mécanique")
        limite_elastique_min = st.slider("Limite Élastique Min (MPa)", int(df_initial['Limite_Elastique_MPa'].min()), int(df_initial['Limite_Elastique_MPa'].max()), int(df_initial['Limite_Elastique_MPa'].min()))
        module_young_min = st.slider("Module de Young Min (GPa)", int(df_initial['Module_Young_GPa'].min()), int(df_initial['Module_Young_GPa'].max()), int(df_initial['Module_Young_GPa'].min()))
    with c2:
        st.markdown("### 🌡️ Thermique")
        temp_fusion_min = st.slider("Temp. de Fusion Min (°C)", int(df_initial['Temp_Fusion_C'].min()), int(df_initial['Temp_Fusion_C'].max()), int(df_initial['Temp_Fusion_C'].min()))
    with c3:
        st.markdown("### 🌱 Éco & Coûts")
        empreinte_co2_max = st.slider("Empreinte CO₂ Max (kg/kg)", float(df_initial['Empreinte_CO2'].min()), float(df_initial['Empreinte_CO2'].max()), float(df_initial['Empreinte_CO2'].max()))
        prix_max = st.slider("Prix Max (€/kg)", float(df_initial['Prix_euro_kg'].min()), float(df_initial['Prix_euro_kg'].max()), float(df_initial['Prix_euro_kg'].max()))
        
    df_filtre = df_initial[
        (df_initial['Limite_Elastique_MPa'] >= limite_elastique_min) &
        (df_initial['Module_Young_GPa'] >= module_young_min) &
        (df_initial['Temp_Fusion_C'] >= temp_fusion_min) &
        (df_initial['Empreinte_CO2'] <= empreinte_co2_max) &
        (df_initial['Prix_euro_kg'] <= prix_max)
    ].copy()
    
    if type_indice == "Traction pure (Max Re / ρ)": df_filtre = df_filtre.sort_values(by='Indice_Traction', ascending=False)
    elif type_indice == "Flexion pure (Max √Re / ρ)": df_filtre = df_filtre.sort_values(by='Indice_Flexion', ascending=False)

    st.subheader(f"📊 {len(df_filtre)} matériau(x) valide(s)")
    
    if not df_filtre.empty:
        # --- BOUTON PDF POUR L'ONGLET 2 ---
        if HAS_FPDF:
            criteres_actuels = {
                "Re minimum": f"{limite_elastique_min} MPa",
                "Young minimum": f"{module_young_min} GPa",
                "CO2 maximum": f"{empreinte_co2_max} kg/kg",
                "Prix maximum": f"{prix_max} EUR/kg"
            }
            pdf_etude = generer_pdf_etude(df_filtre, criteres_actuels)
            st.download_button("📄 Télécharger l'Étude de Faisabilité (PDF)", data=pdf_etude, file_name="Etude_Faisabilite_Materiaux.pdf", mime="application/pdf", type="primary")

        st.dataframe(df_filtre[colonnes_brutes_affichage].rename(columns=DISPLAY_MAP).head(20), use_container_width=True)