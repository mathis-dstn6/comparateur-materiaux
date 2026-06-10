import streamlit as st
import pandas as pd
import numpy as np

# Configuration de la structure de la page web
st.set_page_config(page_title="Éco-Conception Métallurgique", layout="wide")

st.title("🌱 Outil d'Éco-Conception Métallurgique")
st.write("Trouvez le matériau idéal pour votre cahier des charges basé sur vos données réelles.")

# --- 1. CHARGEMENT ET NETTOYAGE DES DONNÉES ---
@st.cache_data
def charger_donnees():
    # Lecture du fichier avec le séparateur point-virgule d'Excel
    df = pd.read_csv('alliages_metalliques_4.csv', sep=';')
    
    # Remplacement préventif des valeurs 0 pour éviter les divisions par zéro
    colonnes_a_nettoyer = [
        'Densite', 'Module_Young_GPa', 'Limite_Elastique_MPa', 
        'Empreinte_CO2', 'Prix_euro_kg', 'Temp_Fusion_C', 
        'Conductivite_Thermique_W_mK', 'Recyclabilite_pct'
    ]
    for col in colonnes_a_nettoyer:
        if col in df.columns:
            df[col] = df[col].replace(0, 1e-6)
    return df

df_initial = charger_donnees()

# Liste ordonnée des colonnes pour l'affichage uniforme dans les tableaux
colonnes_affichage = [
    'Nom', 'Densite', 'Module_Young_GPa', 'Limite_Elastique_MPa', 
    'Temp_Fusion_C', 'Conductivite_Thermique_W_mK', 
    'Empreinte_CO2', 'Recyclabilite_pct', 'Prix_euro_kg'
]

# --- 2. CRÉATION DES DEUX ONGLETS ---
tab1, tab2 = st.tabs(["🔄 Remplacement de Matériau", "📐 Cahier des Charges Strict"])

# --- ONGLET 1 : RECHERCHE PAR SIMILITUDE ---
with tab1:
    st.header("Trouver une alternative plus verte ou moins chère")
    st.write("Sélectionnez le matériau que vous utilisez actuellement pour observer ses propriétés.")
    
    # Menu déroulant de sélection basé sur la colonne Nom
    liste_materiaux = df_initial['Nom'].tolist()
    materiau_ref = st.selectbox("Sélectionnez le matériau à remplacer :", liste_materiaux)
    
    # Extraction des caractéristiques du matériau choisi
    row_ref = df_initial[df_initial['Nom'] == materiau_ref].iloc[0]
    
    # Affichage dynamique des métriques du matériau de référence
    st.subheader("Propriétés du matériau sélectionné")
    
    # Ligne 1 : Propriétés physiques et mécaniques
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Densité", f"{row_ref['Densite']} kg/m³")
    col2.metric("Limite Élastique", f"{row_ref['Limite_Elastique_MPa']} MPa")
    col3.metric("Module de Young", f"{row_ref['Module_Young_GPa']} GPa")
    col4.metric("Empreinte CO₂", f"{row_ref['Empreinte_CO2']} kgCO2/kg")
    
    # Ligne 2 : Propriétés thermiques, écologiques et économiques
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Temp. de Fusion", f"{row_ref['Temp_Fusion_C']} °C")
    col6.metric("Conductivité Thermique", f"{row_ref['Conductivite_Thermique_W_mK']} W/m·K")
    col7.metric("Recyclabilité", f"{row_ref['Recyclabilite_pct']} %")
    col8.metric("Prix moyen", f"{row_ref['Prix_euro_kg']} €/kg")
    
    st.subheader("Visualisation de l'ensemble de votre base de données")
    st.dataframe(df_initial[colonnes_affichage], use_container_width=True)

# --- ONGLET 2 : FILTRAGE STRICT (CAHIER DES CHARGES) ---
with tab2:
    st.header("Filtrer par critères techniques, thermiques et environnementaux")
    st.write("Définissez vos seuils pour isoler les meilleurs candidats pour votre application.")
    
    # Alignement des curseurs de réglage (Sliders) sur 3 colonnes thématiques
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("### ⚙️ Propriétés Mécaniques")
        limite_elastique_min = st.slider(
            "Limite Élastique Minimum (MPa)", 
            int(df_initial['Limite_Elastique_MPa'].min()), 
            int(df_initial['Limite_Elastique_MPa'].max()), 
            int(df_initial['Limite_Elastique_MPa'].min())
        )
        module_young_min = st.slider(
            "Module de Young Minimum (GPa)",
            int(df_initial['Module_Young_GPa'].min()),
            int(df_initial['Module_Young_GPa'].max()),
            int(df_initial['Module_Young_GPa'].min())
        )
        
    with c2:
        st.markdown("### 🌡️ Propriétés Thermiques")
        temp_fusion_min = st.slider(
            "Température de Fusion Minimum (°C)", 
            int(df_initial['Temp_Fusion_C'].min()), 
            int(df_initial['Temp_Fusion_C'].max()), 
            int(df_initial['Temp_Fusion_C'].min())
        )
        conductivite_min = st.slider(
            "Conductivité Thermique Minimum (W/m·K)", 
            int(df_initial['Conductivite_Thermique_W_mK'].min()), 
            int(df_initial['Conductivite_Thermique_W_mK'].max()), 
            int(df_initial['Conductivite_Thermique_W_mK'].min())
        )
        
    with c3:
        st.markdown("### 🌱 Éco-Conception & Coûts")
        empreinte_co2_max = st.slider(
            "Empreinte CO₂ Maximum (kgCO2/kg)", 
            float(df_initial['Empreinte_CO2'].min()), 
            float(df_initial['Empreinte_CO2'].max()), 
            float(df_initial['Empreinte_CO2'].max())
        )
        recyclabilite_min = st.slider(
            "Taux de Recyclabilité Minimum (%)", 
            int(df_initial['Recyclabilite_pct'].min()), 
            int(df_initial['Recyclabilite_pct'].max()), 
            int(df_initial['Recyclabilite_pct'].min())
        )
        prix_max = st.slider(
            "Prix Maximum (€/kg)", 
            float(df_initial['Prix_euro_kg'].min()), 
            float(df_initial['Prix_euro_kg'].max()), 
            float(df_initial['Prix_euro_kg'].max())
        )
        
    # Application simultanée de l'intégralité des filtres du cahier des charges
    df_filtre = df_initial[
        (df_initial['Limite_Elastique_MPa'] >= limite_elastique_min) &
        (df_initial['Module_Young_GPa'] >= module_young_min) &
        (df_initial['Temp_Fusion_C'] >= temp_fusion_min) &
        (df_initial['Conductivite_Thermique_W_mK'] >= conductivite_min) &
        (df_initial['Empreinte_CO2'] <= empreinte_co2_max) &
        (df_initial['Recyclabilite_pct'] >= recyclabilite_min) &
        (df_initial['Prix_euro_kg'] <= prix_max)
    ]
    
    st.subheader(f"📊 {len(df_filtre)} matériau(x) valide(s) trouvé(s)")
    
    if not df_filtre.empty:
        # Affichage du tableau filtré dynamique
        st.dataframe(df_filtre[colonnes_affichage], use_container_width=True)
        
        # Graphique de compromis d'Ashby automatique
        st.write("### 📈 Graphique de compromis : Résistance Mécanique vs Empreinte CO₂")
        st.scatter_chart(
            df_filtre,
            x='Empreinte_CO2',
            y='Limite_Elastique_MPa',
            color='Nom'
        )
    else:
        st.warning("Aucun alliage ne correspond à l'ensemble de vos contraintes strictes. Essayez d'assouplir certains curseurs.")