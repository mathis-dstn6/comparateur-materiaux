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
st.set_page_config(page_title="MatSwap", page_icon="🔄", layout="wide")

# --- TITRE SAAS PREMIUM (CSS) ---
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght=700;800&display=swap');
        .main-title-container {
            font-family: 'Poppins', sans-serif;
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 0px;
            padding-bottom: 0px;
            line-height: 1.2;
        }
        .text-gradient {
            background: -webkit-linear-gradient(45deg, #2563EB, #14B8A6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle {
            font-family: 'Inter', sans-serif;
            color: #64748B;
            font-size: 1.1rem;
            margin-bottom: 30px;
            margin-top: 5px;
        }
    </style>
    <div class='main-title-container'>🔄 <span class='text-gradient'>MatSwap</span></div>
    <div class='subtitle'>L'intelligence artificielle au service de la substitution des matériaux.</div>
""", unsafe_allow_html=True)

# --- MAPPING ET TOOLTIPS ---
DISPLAY_MAP = {
    'Nom': 'Nom de l\'Alliage', 'Famille': 'Famille Métallurgique', 'Densite': 'Densité (kg/m³)',
    'Module_Young_GPa': 'Module de Young (GPa)', 'Limite_Elastique_MPa': 'Limite Élastique (MPa)',
    'Durete_HRC': 'Dureté Rockwell (HRC)',
    'Temp_Fusion_C': 'Temp. de Fusion (°C)', 'Conductivite_Thermique_W_mK': 'Conductivité (W/m·K)',
    'Empreinte_CO2': 'Empreinte CO₂ (kg/kg)', 'Recyclabilite_pct': 'Recyclabilité (%)',
    'Prix_euro_kg': 'Prix moyen (€/kg)', 'Score_Eco': 'Score Éco-Conception (/100)'
}

HELP_RE = "Limite Élastique (Re) : Contrainte maximale avant déformation irréversible."
HELP_YOUNG = "Module de Young (E) : Mesure la rigidité. Plus il est élevé, moins la pièce fléchira."
HELP_DURETE = "Dureté Rockwell (C) : Résistance à la pénétration. Crucial pour l'usure et le frottement."
HELP_CO2 = "Kilos de CO₂ émis pour produire 1 kg de cet alliage."
HELP_PRIX = "Prix estimatif sur le marché industriel européen."
HELP_SCORE = "Note sur 100 valorisant les matériaux bas carbone et hautement recyclables."

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def charger_donnees():
    df = pd.read_csv('alliages_metalliques_4_2.csv', sep=';')
    if 'Famille' not in df.columns: df['Famille'] = 'Non spécifié'
    
    if 'Durete_HRC' not in df.columns:
        df['Durete_HRC'] = 0.0
        
    colonnes_tri = ['Densite', 'Module_Young_GPa', 'Limite_Elastique_MPa', 'Durete_HRC', 'Empreinte_CO2', 'Prix_euro_kg', 'Temp_Fusion_C', 'Conductivite_Thermique_W_mK', 'Recyclabilite_pct']
    for col in colonnes_tri:
        if col in df.columns: df[col] = df[col].replace(0, 1e-6)
            
    df['Indice_Traction'] = df['Limite_Elastique_MPa'] / df['Densite']
    df['Indice_Flexion'] = np.sqrt(df['Limite_Elastique_MPa']) / df['Densite']
    
    def calc_eco_score(row):
        return max(0, min(100, int((row['Recyclabilite_pct'] / 100) * (5 / row['Empreinte_CO2']) * 100)))
        
    df['Score_Eco'] = df.apply(calc_eco_score, axis=1)
    return df

df_initial = charger_donnees()
colonnes_brutes_affichage = list(DISPLAY_MAP.keys())

# --- CONFIGURATION DES LIMITES GLOBALES POUR LE RADAR (0 à 100) ---
GLOBAL_MINS = df_initial[['Limite_Elastique_MPa', 'Module_Young_GPa', 'Score_Eco', 'Densite', 'Prix_euro_kg']].min()
GLOBAL_MAXS = df_initial[['Limite_Elastique_MPa', 'Module_Young_GPa', 'Score_Eco', 'Densite', 'Prix_euro_kg']].max()

def obtenir_profil_radar(row):
    def norm_plus(val, col):
        span = GLOBAL_MAXS[col] - GLOBAL_MINS[col]
        return 10 + 90 * (val - GLOBAL_MINS[col]) / span if span > 0 else 50
    def norm_moins(val, col):
        span = GLOBAL_MAXS[col] - GLOBAL_MINS[col]
        return 10 + 90 * (GLOBAL_MAXS[col] - val) / span if span > 0 else 50

    return [
        norm_plus(row['Limite_Elastique_MPa'], 'Limite_Elastique_MPa'),
        norm_plus(row['Module_Young_GPa'], 'Module_Young_GPa'),
        norm_plus(row['Score_Eco'], 'Score_Eco'),
        norm_moins(row['Densite'], 'Densite'),      
        norm_moins(row['Prix_euro_kg'], 'Prix_euro_kg')  
    ]

# --- GÉNÉRATEUR PDF 1 : SUBSTITUTION ---
def generer_pdf(ref, alt, simuler_piece, poids_ref, poids_alt, co2_ref, co2_alt, prix_ref, prix_alt, fig_radar, fig_ashby):
    pdf = FPDF()
    pdf.add_page()
    NOIR, GRIS = (30, 30, 30), (100, 100, 100)
    
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, "RAPPORT D'AUDIT : SUBSTITUTION MATSWAP", ln=True, align="C", fill=True)
    pdf.ln(5)
    
    pdf.set_text_color(*GRIS)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 6, f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} via MatSwap", ln=True, align="R")
    pdf.ln(5)
    
    pdf.set_text_color(*NOIR)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, f"  1. MATERIAU DE REFERENCE : {ref['Nom']} ({ref['Famille']})", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.ln(2)
    pdf.cell(0, 5, f"   - Mecanique : Re = {ref['Limite_Elastique_MPa']} MPa | E = {ref['Module_Young_GPa']} GPa | Durete = {ref['Durete_HRC']} HRC", ln=True)
    pdf.cell(0, 5, f"   - Base 1 kg : CO2 = {ref['Empreinte_CO2']} kg/kg | Prix = {ref['Prix_euro_kg']} EUR/kg | Densite = {ref['Densite']} kg/m3", ln=True)
    pdf.ln(4)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(219, 234, 254)
    pdf.cell(0, 8, f"  2. ALTERNATIVE RECOMMANDEE : {alt['Nom']} ({alt['Famille']})", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.ln(2)
    pdf.cell(0, 5, f"   - Mecanique : Re = {alt['Limite_Elastique_MPa']} MPa | E = {alt['Module_Young_GPa']} GPa | Durete = {alt['Durete_HRC']} HRC", ln=True)
    pdf.cell(0, 5, f"   - Base 1 kg : CO2 = {alt['Empreinte_CO2']} kg/kg | Prix = {alt['Prix_euro_kg']} EUR/kg | Densite = {alt['Densite']} kg/m3", ln=True)
    pdf.ln(4)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(241, 245, 249)
    if simuler_piece:
        pdf.cell(0, 8, f"  3. BILAN SUR PIECE REELLE (Volume constant)", ln=True, fill=True)
    else:
        pdf.cell(0, 8, f"  3. BILAN GENERIQUE (Pour 1 kg de matiere)", ln=True, fill=True)
        
    pdf.set_font("Arial", '', 10)
    pdf.ln(2)
    
    if simuler_piece:
        diff_poids = poids_ref - poids_alt
        pdf.cell(0, 6, f"   -> Poids de la piece : Passe de {poids_ref:.2f} kg a {poids_alt:.2f} kg ({'-' if diff_poids>0 else '+'}{abs(diff_poids):.2f} kg per piece)", ln=True)
    
    diff_co2 = co2_ref - co2_alt
    diff_prix = prix_ref - prix_alt
    unite = "piece" if simuler_piece else "kg"
    
    pdf.cell(0, 6, f"   -> Bilan Carbone : {'Economie' if diff_co2>0 else 'Surcout'} de {abs(diff_co2):.2f} kg CO2 / {unite}", ln=True)
    pdf.cell(0, 6, f"   -> Bilan Financier : {'Economie' if diff_prix>0 else 'Surcout'} de {abs(diff_prix):.2f} EUR / {unite}", ln=True)
    pdf.cell(0, 6, f"   -> Score Eco-Conception : +{alt['Score_Eco'] - ref['Score_Eco']} points", ln=True)
    pdf.ln(6)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, "  4. ANALYSES GRAPHIQUES RAPPORTÉES", ln=True, fill=True)
    pdf.ln(4)
    
    try:
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_radar:
            f_radar.write(fig_radar.to_image(format="png", width=550, height=450))
            path_radar = f_radar.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_ashby:
            f_ashby.write(fig_ashby.to_image(format="png", width=550, height=450))
            path_ashby = f_ashby.name
        
        y_actuel = pdf.get_y()
        pdf.image(path_radar, x=10, y=y_actuel, w=92)
        pdf.image(path_ashby, x=108, y=y_actuel, w=92)
        pdf.ln(78)
        os.unlink(path_radar)
        os.unlink(path_ashby)
    except Exception as e:
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 6, "   (Graphes indisponibles sans kaleido)", ln=True)
        pdf.ln(4)
    
    pdf.ln(4)
    pdf.set_text_color(*GRIS)
    pdf.set_font("Arial", 'I', 9)
    pdf.multi_cell(0, 4, "Ce document certifie la pertinence de la substitution. Analyse effectuee en temps reel via le moteur MatSwap.", align="J")
    
    return bytes(pdf.output(dest='S').encode('latin-1', 'replace'))

# --- GÉNÉRATEUR PDF 2 : CAHIER DES CHARGES ---
def generer_pdf_etude(df_top, criteres, type_indice, fig_radar, fig_ashby):
    pdf = FPDF()
    pdf.add_page()
    NOIR, GRIS = (30, 30, 30), (100, 100, 100)
    
    pdf.set_fill_color(37, 99, 235)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 15, "ETUDE DE FAISABILITE MATSWAP", ln=True, align="C", fill=True)
    pdf.ln(5)
    
    pdf.set_text_color(*GRIS)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 6, f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} via MatSwap", ln=True, align="R")
    pdf.ln(5)
    
    pdf.set_text_color(*NOIR)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, "  1. RAPPEL DU CAHIER DES CHARGES", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.ln(2)
    for cle, valeur in criteres.items(): pdf.cell(0, 5, f"   * {cle} : {valeur}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(219, 234, 254)
    pdf.cell(0, 8, "  2. TOP 5 DES MEILLEURS CANDIDATS DETECTES", ln=True, fill=True)
    pdf.ln(3)
    
    for i, (_, row) in enumerate(df_top.head(5).iterrows(), 1):
        pdf.set_text_color(37, 99, 235)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, f"  #{i} - {row['Nom']} ({row['Famille']})", ln=True)
        pdf.set_text_color(*NOIR)
        pdf.set_font("Arial", '', 9)
        pdf.cell(0, 4, f"        Mecanique : Re = {row['Limite_Elastique_MPa']} MPa | E = {row['Module_Young_GPa']} GPa | Durete = {row['Durete_HRC']} HRC", ln=True)
        pdf.cell(0, 4, f"        RSE & Cout : CO2 = {row['Empreinte_CO2']} kg | Prix = {row['Prix_euro_kg']} EUR | Score = {row['Score_Eco']}/100", ln=True)
        pdf.ln(3)
        
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 8, "  3. CARTOGRAPHIE ET VISUALISATION DU CAHIER DES CHARGES", ln=True, fill=True)
    pdf.ln(4)
    
    try:
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_radar:
            f_radar.write(fig_radar.to_image(format="png", width=550, height=450))
            path_radar = f_radar.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f_ashby:
            f_ashby.write(fig_ashby.to_image(format="png", width=550, height=450))
            path_ashby = f_ashby.name
        
        y_actuel = pdf.get_y()
        pdf.image(path_radar, x=10, y=y_actuel, w=92)
        pdf.image(path_ashby, x=108, y=y_actuel, w=92)
        pdf.ln(78)
        os.unlink(path_radar)
        os.unlink(path_ashby)
    except Exception as e:
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 6, "   (Installez 'kaleido' pour inclure les graphiques dans ce PDF)", ln=True)
        pdf.ln(4)
        
    return bytes(pdf.output(dest='S').encode('latin-1', 'replace'))

# --- INTERFACE UTILISATEUR ---
with st.expander("👋 Guide Rapide de MatSwap"):
    st.markdown("""
    * **Étape 1 :** Utilisez le menu latéral pour cibler une famille de matériaux.
    * **Étape 2 :** Choisissez votre Objectif principal dans la configuration : réduire l'empreinte CO₂, réduire le prix, ou trouver le compromis idéal grâce à une Pondération mixte personnalisée (%).
    * **Étape 3 :** Onglet *Substitution* pour comparer instantanément les **3 meilleures alternatives** calculées selon vos critères.
    * **💡 Astuce Pro :** Activez la simulation sur pièce réelle pour calculer l'allègement exact (en kg) de votre pièce mécanique !
    * **Étape 4 :** Onglet *Étude* pour définir un cahier des charges strict et exporter les candidats.
    """)

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942232.png", width=80) 
    st.header("⚙️ Configuration")
    famille_choisie = st.selectbox("Filtrer par famille :", ['Toutes'] + sorted(df_initial['Famille'].unique().tolist()))
    
    st.markdown("### 🎯 Stratégie d'Optimisation")
    objectif = st.radio(
        "Objectif principal :", 
        ["Réduire l'empreinte CO₂", "Réduire le prix (€/kg)", "Optimisation mixte (Pondérée)"]
    )
    
    poids_co2 = 50
    poids_prix = 50
    if objectif == "Optimisation mixte (Pondérée)":
        st.write("---")
        st.markdown("**⚖️ Ajustement des poids :**")
        poids_co2 = st.slider("Importance Écologique (%)", 0, 100, 50, step=5)
        poids_prix = 100 - poids_co2
        st.caption(f"➔ Importance Économique : **{poids_prix}%**")

df_recherche = df_initial[df_initial['Famille'] == famille_choisie] if famille_choisie != 'Toutes' else df_initial
tab1, tab2 = st.tabs(["🔄 Substitution (Top 3 Scénarios)", "📐 Étude & Cahier des Charges"])

# --- ONGLET 1 : SUBSTITUTION ---
with tab1:
    col_sel, col_tol = st.columns([1, 2])
    with col_sel:
        liste_materiaux = sorted(df_recherche['Nom'].tolist())
        materiau_ref = st.selectbox("Sélectionnez le matériau de référence (tapez pour chercher) :", liste_materiaux)
        row_ref = df_initial[df_initial['Nom'] == materiau_ref].iloc[0]
        
    with col_tol:
        st.write("**Tolérances Mécaniques & Thermiques :**")
        c1, c2, c3 = st.columns(3)
        with c1: keep_mecha = st.checkbox("Conserver Résistance", True); tol_mecha = st.slider("Tolérance Re (%)", 0, 50, 20, disabled=not keep_mecha, help=HELP_RE)
        with c2: keep_thermal = st.checkbox("Conserver Tenue Therm.", False); tol_thermal = st.slider("Tolérance Fusion (%)", 0, 50, 20, disabled=not keep_thermal)
        with c3: keep_stiff = st.checkbox("Conserver Rigidité", False); tol_stiff = st.slider("Tolérance Young (%)", 0, 50, 20, disabled=not keep_stiff, help=HELP_YOUNG)

    st.write("---")
    
    st.markdown("### 📦 Simulation sur Pièce Réelle (Optionnelle)")
    simuler_piece = st.toggle("Activer le calcul d'impact pour une pièce spécifique", value=False)
    poids_actuel = st.number_input("Poids de votre pièce actuelle en kg :", min_value=0.01, value=5.00, step=0.1) if simuler_piece else 1.0

    st.markdown(f"#### 📊 Profil actuel : **{materiau_ref}**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Score Éco", f"{row_ref['Score_Eco']} /100", help=HELP_SCORE)
    c2.metric("Dureté Rockwell", f"{row_ref['Durete_HRC']} HRC", help=HELP_DURETE)
    c3.metric(f"CO₂ ({'Total' if simuler_piece else 'au kg'})", f"{row_ref['Empreinte_CO2'] * poids_actuel:.1f} kg", help=HELP_CO2)
    c4.metric(f"Prix ({'Total' if simuler_piece else 'au kg'})", f"{row_ref['Prix_euro_kg'] * poids_actuel:.1f} €", help=HELP_PRIX)
    
    st.write("---")

    df_alt = df_initial[df_initial['Nom'] != materiau_ref].copy()
    if keep_mecha: df_alt = df_alt[df_alt['Limite_Elastique_MPa'] >= row_ref['Limite_Elastique_MPa'] * (1 - (tol_mecha / 100))]
    if keep_thermal: df_alt = df_alt[df_alt['Temp_Fusion_C'] >= row_ref['Temp_Fusion_C'] * (1 - (tol_thermal / 100))]
    if keep_stiff: df_alt = df_alt[df_alt['Module_Young_GPa'] >= row_ref['Module_Young_GPa'] * (1 - (tol_stiff / 100))]
        
    if objectif == "Réduire l'empreinte CO₂": 
        df_alt = df_alt.sort_values(by='Empreinte_CO2')
    elif objectif == "Réduire le prix (€/kg)": 
        df_alt = df_alt.sort_values(by='Prix_euro_kg')
    else:
        min_co2, max_co2 = df_alt['Empreinte_CO2'].min(), df_alt['Empreinte_CO2'].max()
        min_prix, max_prix = df_alt['Prix_euro_kg'].min(), df_alt['Prix_euro_kg'].max()
        span_co2 = max_co2 - min_co2 if max_co2 != min_co2 else 1
        span_prix = max_prix - min_prix if max_prix != min_prix else 1
        
        df_alt['Score_Mixte'] = (
            (poids_co2 / 100) * ((df_alt['Empreinte_CO2'] - min_co2) / span_co2) +
            (poids_prix / 100) * ((df_alt['Prix_euro_kg'] - min_prix) / span_prix)
        )
        df_alt = df_alt.sort_values(by='Score_Mixte')

    if not df_alt.empty:
        top_alternatives = df_alt.head(3)
        st.success(f"### 🎉 Les {len(top_alternatives)} meilleures alternatives recommandées")
        
        colonnes_alt = st.columns(len(top_alternatives))
        for idx, col in enumerate(colonnes_alt):
            alt = top_alternatives.iloc[idx]
            with col:
                st.markdown(f"#### #{idx+1} {alt['Nom']}")
                st.caption(f"Dureté : {alt['Durete_HRC']} HRC")
                
                poids_alt = poids_actuel * (alt['Densite'] / row_ref['Densite']) if simuler_piece else 1.0
                co2_alt_tot = alt['Empreinte_CO2'] * poids_alt
                prix_alt_tot = alt['Prix_euro_kg'] * poids_alt
                
                gain_co2 = ((row_ref['Empreinte_CO2'] * poids_actuel) - co2_alt_tot) / (row_ref['Empreinte_CO2'] * poids_actuel) * 100
                gain_prix = ((row_ref['Prix_euro_kg'] * poids_actuel) - prix_alt_tot) / (row_ref['Prix_euro_kg'] * poids_actuel) * 100
                
                if simuler_piece:
                    st.metric("Poids Pièce", f"{poids_alt:.1f} kg", f"{-(poids_actuel - poids_alt):.1f} kg", delta_color="inverse")
                st.metric(f"CO₂ {'Totale' if simuler_piece else ''}", f"{co2_alt_tot:.1f} kg", f"-{gain_co2:.1f}%", delta_color="inverse")
                st.metric(f"Prix {'Total' if simuler_piece else ''}", f"{prix_alt_tot:.1f} €", f"{'-' if gain_prix>0 else '+'}{abs(gain_prix):.1f}%", delta_color="inverse")
        
        st.write("---")
        
        st.markdown("### 📊 Analyses Graphiques Avancées")
        col_radar, col_ashby = st.columns(2)
        
        with col_radar:
            st.markdown("#### 🕸️ Profil de Performance (Échelle Absolue 0-100)")
            categories = ['Résistance (Re)', 'Rigidité (E)', 'Éco-Score', 'Légèreté (Inv. ρ)', 'Économie (Inv. €)']
            
            fig = go.Figure()
            vals_ref = obtenir_profil_radar(row_ref)
            fig.add_trace(go.Scatterpolar(
                r=vals_ref, theta=categories, fill='toself', 
                name=f"Réf: {row_ref['Nom']}", 
                line=dict(color='#64748B', width=4)
            ))
            
            colors = ['#2563EB', '#10B981', '#8B5CF6']
            for idx, alt in top_alternatives.iterrows():
                pos = list(top_alternatives.index).index(idx)
                vals_alt = obtenir_profil_radar(alt)
                
                fig.add_trace(go.Scatterpolar(
                    r=vals_alt, theta=categories, fill='toself', 
                    name=f"#{pos+1} {alt['Nom']}", 
                    line=dict(color=colors[pos], width=3)
                ))
                
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=450, margin=dict(t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

        with col_ashby:
            st.markdown("#### 📈 Cartographie d'Ashby (vs Résistance Re)")
            axe_x_choix = st.selectbox(
                "Sélectionner la variable de l'Axe X :", 
                ["Densite", "Prix_euro_kg", "Empreinte_CO2"], 
                format_func=lambda x: DISPLAY_MAP[x]
            )
            
            fig_ashby = go.Figure()
            for famille, group in df_initial.groupby('Famille'):
                fig_ashby.add_trace(go.Scatter(
                    x=group[axe_x_choix], y=group['Limite_Elastique_MPa'],
                    mode='markers', name=famille, marker=dict(size=7, opacity=0.35), text=group['Nom'],
                    hovertemplate="<b>%{text}</b><br>" + DISPLAY_MAP[axe_x_choix] + " : %{x}<br>Re : %{y} MPa<extra></extra>"
                ))
            
            fig_ashby.add_trace(go.Scatter(
                x=[row_ref[axe_x_choix]], y=[row_ref['Limite_Elastique_MPa']],
                mode='markers', name=f"Réf: {row_ref['Nom']}",
                marker=dict(color='#475569', size=15, symbol='diamond', line=dict(color='white', width=2)), text=[row_ref['Nom']],
                hovertemplate="<b>%{text} (RÉFÉRENCE)</b><br>" + DISPLAY_MAP[axe_x_choix] + " : %{x}<br>Re : %{y} MPa<extra></extra>"
            ))
            
            for idx, alt in top_alternatives.iterrows():
                pos = list(top_alternatives.index).index(idx)
                fig_ashby.add_trace(go.Scatter(
                    x=[alt[axe_x_choix]], y=[alt['Limite_Elastique_MPa']],
                    mode='markers', name=f"#{pos+1} {alt['Nom']}",
                    marker=dict(color=colors[pos], size=13, symbol='circle', line=dict(color='white', width=2)), text=[alt['Nom']],
                    hovertemplate="<b>%{text} (Alternative #"+str(pos+1)+")</b><br>" + DISPLAY_MAP[axe_x_choix] + " : %{x}<br>Re : %{y} MPa<extra></extra>"
                ))
                
            fig_ashby.update_layout(
                xaxis_title=DISPLAY_MAP[axe_x_choix], yaxis_title="Limite Élastique Re (MPa)", showlegend=True, height=400,
                margin=dict(t=10, b=10), plot_bgcolor='rgba(241,245,249,0.5)', paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_ashby, use_container_width=True)

        st.write("---")
        meilleur_choix = top_alternatives.iloc[0]
        if HAS_FPDF:
            poids_alt_best = poids_actuel * (meilleur_choix['Densite'] / row_ref['Densite']) if simuler_piece else 1.0
            co2_ref_tot = row_ref['Empreinte_CO2'] * poids_actuel
            co2_alt_tot = meilleur_choix['Empreinte_CO2'] * poids_alt_best
            prix_ref_tot = row_ref['Prix_euro_kg'] * poids_actuel
            prix_alt_tot = meilleur_choix['Prix_euro_kg'] * poids_alt_best
            
            pdf_bytes = generer_pdf(
                row_ref, meilleur_choix, simuler_piece, poids_actuel, poids_alt_best, 
                co2_ref_tot, co2_alt_tot, prix_ref_tot, prix_alt_tot, fig, fig_ashby
            )
            st.download_button("📄 Exporter le Rapport d'Audit Enrichi (PDF)", data=pdf_bytes, file_name=f"Rapport_MatSwap.pdf", mime="application/pdf", type="primary")
            
    else:
        st.info("Aucune alternative trouvée. Essayez d'élargir les tolérances.")

# --- ONGLET 2 : FILTRAGE STRICT & CAHIER DES CHARGES ---
with tab2:
    st.header("Étude de Faisabilité & Cahier des Charges")
    type_indice = st.selectbox("Indice d'Ashby :", ["Aucun - Tri standard", "Traction pure (Max Re / ρ)", "Flexion pure (Max √Re / ρ)"])
    
    st.write("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        limite_elastique_min = st.slider("Limite Élastique Min (MPa)", int(df_initial['Limite_Elastique_MPa'].min()), int(df_initial['Limite_Elastique_MPa'].max()), int(df_initial['Limite_Elastique_MPa'].min()), help=HELP_RE)
        module_young_min = st.slider("Module de Young Min (GPa)", int(df_initial['Module_Young_GPa'].min()), int(df_initial['Module_Young_GPa'].max()), int(df_initial['Module_Young_GPa'].min()), help=HELP_YOUNG)
    with c2:
        durete_min = st.slider("Dureté Minimale souhaitée (HRC)", 0, 70, 0, help=HELP_DURETE)
        temp_fusion_min = st.slider("Temp. de Fusion Min (°C)", int(df_initial['Temp_Fusion_C'].min()), int(df_initial['Temp_Fusion_C'].max()), int(df_initial['Temp_Fusion_C'].min()))
        conductivite_min = st.slider("Conductivité Min (W/m·K)", int(df_initial['Conductivite_Thermique_W_mK'].min()), int(df_initial['Conductivite_Thermique_W_mK'].max()), int(df_initial['Conductivite_Thermique_W_mK'].min()))
    with c3:
        empreinte_co2_max = st.slider("Empreinte CO₂ Max (kg/kg)", float(df_initial['Empreinte_CO2'].min()), float(df_initial['Empreinte_CO2'].max()), float(df_initial['Empreinte_CO2'].max()), help=HELP_CO2)
        prix_max = st.slider("Prix Max (€/kg)", float(df_initial['Prix_euro_kg'].min()), float(df_initial['Prix_euro_kg'].max()), float(df_initial['Prix_euro_kg'].max()), help=HELP_PRIX)
        
    df_filtre = df_initial[
        (df_initial['Limite_Elastique_MPa'] >= limite_elastique_min) &
        (df_initial['Module_Young_GPa'] >= module_young_min) &
        (df_initial['Durete_HRC'] >= durete_min) &
        (df_initial['Temp_Fusion_C'] >= temp_fusion_min) &
        (df_initial['Conductivite_Thermique_W_mK'] >= conductivite_min) &
        (df_initial['Empreinte_CO2'] <= empreinte_co2_max) &
        (df_initial['Prix_euro_kg'] <= prix_max)
    ].copy()
    
    if type_indice == "Traction pure (Max Re / ρ)": df_filtre = df_filtre.sort_values(by='Indice_Traction', ascending=False)
    elif type_indice == "Flexion pure (Max √Re / ρ)": df_filtre = df_filtre.sort_values(by='Indice_Flexion', ascending=False)

    st.subheader(f"📊 {len(df_filtre)} matériau(x) valide(s)")
    
    if not df_filtre.empty:
        top_etude = df_filtre.head(3)
        
        st.markdown("### 📊 Analyses Graphiques du Cahier des Charges")
        col_radar_e, col_ashby_e = st.columns(2)
        
        with col_radar_e:
            st.markdown("#### 🕸️ Profil des 3 Meilleurs Candidats Répondants (0-100)")
            fig_radar_e = go.Figure()
            colors_e = ['#2563EB', '#10B981', '#8B5CF6']
            categories = ['Résistance (Re)', 'Rigidité (E)', 'Éco-Score', 'Légèreté (Inv. ρ)', 'Économie (Inv. €)']
            
            for idx, alt in top_etude.iterrows():
                pos = list(top_etude.index).index(idx)
                vals_alt = obtenir_profil_radar(alt)
                fig_radar_e.add_trace(go.Scatterpolar(
                    r=vals_alt, theta=categories, fill='toself',
                    name=f"#{pos+1} {alt['Nom']}", line=dict(color=colors_e[pos], width=3)
                ))
            fig_radar_e.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=450, margin=dict(t=20, b=20))
            st.plotly_chart(fig_radar_e, use_container_width=True)
            
        with col_ashby_e:
            st.markdown("#### 📈 Positionnement d'Ashby (Filtrage en bloc)")
            axe_x_e = st.selectbox(
                "Variable de l'Axe X (Étude) :", ["Densite", "Prix_euro_kg", "Empreinte_CO2"],
                format_func=lambda x: DISPLAY_MAP[x], key="axe_x_etude"
            )
            
            fig_ashby_e = go.Figure()
            for famille, group in df_initial.groupby('Famille'):
                fig_ashby_e.add_trace(go.Scatter(
                    x=group[axe_x_e], y=group['Limite_Elastique_MPa'],
                    mode='markers', name=famille, marker=dict(size=6, opacity=0.10), text=group['Nom'], showlegend=False
                ))
            fig_ashby_e.add_trace(go.Scatter(
                x=df_filtre[axe_x_e], y=df_filtre['Limite_Elastique_MPa'],
                mode='markers', name="Solutions Valides", marker=dict(color='#14B8A6', size=8, opacity=0.5),
                text=df_filtre['Nom'], hovertemplate="<b>%{text}</b><br>Valide selon critères<extra></extra>"
            ))
            for idx, alt in top_etude.iterrows():
                pos = list(top_etude.index).index(idx)
                fig_ashby_e.add_trace(go.Scatter(
                    x=[alt[axe_x_e]], y=[alt['Limite_Elastique_MPa']],
                    mode='markers', name=f"Podium #{pos+1} {alt['Nom']}",
                    marker=dict(color=colors_e[pos], size=13, symbol='circle', line=dict(color='white', width=2)), text=[alt['Nom']],
                    hovertemplate="<b>%{text} (Top #"+str(pos+1)+")</b><br>Re : %{y} MPa<extra></extra>"
                ))
            fig_ashby_e.update_layout(
                xaxis_title=DISPLAY_MAP[axe_x_e], yaxis_title="Limite Élastique Re (MPa)", showlegend=True, height=400,
                margin=dict(t=10, b=10), plot_bgcolor='rgba(241,245,249,0.5)', paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_ashby_e, use_container_width=True)

        st.write("---")

        # --- SECTIONS DES EXPORTS (COTE À CÔTE) ---
        c_btn1, c_btn2 = st.columns(2)
        
        with c_btn1:
            if HAS_FPDF:
                criteres_actuels = {
                    "Re min": f"{limite_elastique_min} MPa", 
                    "Young min": f"{module_young_min} GPa", 
                    "Durete min": f"{durete_min} HRC", 
                    "Temp. Fusion min": f"{temp_fusion_min} °C",
                    "Conductivite min": f"{conductivite_min} W/m.K",
                    "CO2 max": f"{empreinte_co2_max} kg/kg",
                    "Prix max": f"{prix_max} EUR/kg"
                }
                pdf_etude = generer_pdf_etude(df_filtre, criteres_actuels, type_indice, fig_radar_e, fig_ashby_e)
                st.download_button("📄 Télécharger l'Étude de Faisabilité (PDF)", data=pdf_etude, file_name="Etude_Faisabilite.pdf", mime="application/pdf", type="primary", use_container_width=True)

        with c_btn2:
            # --- CONVERSION DU TABLEAU EN CSV NETTOYÉ ET TRADUIT ---
            df_export = df_filtre[colonnes_brutes_affichage].rename(columns=DISPLAY_MAP)
            csv_bytes = df_export.to_csv(index=False, sep=';', encoding='utf-8-sig')
            
            st.download_button(
                label="📊 Exporter les Données Brutes (Excel / CSV)",
                data=csv_bytes,
                file_name="Cahier_des_Charges_MatSwap.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.dataframe(df_filtre[colonnes_brutes_affichage].rename(columns=DISPLAY_MAP).head(20), use_container_width=True)