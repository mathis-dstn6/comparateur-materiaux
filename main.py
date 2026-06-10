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
    df = pd.read_csv('alliages_metalliques_3.csv', sep=';')
    
    # Remplacement préventif des valeurs 0 pour éviter les divisions par zéro
    df['Densite'] = df['Densite'].replace(0, 1e-6)
    df['Empreinte_CO2'] = df['Empreinte_CO2'].replace(0, 1e-6)
    df['Prix_euro_kg'] = df['Prix_euro_kg'].replace(0, 1e-6)
    return df

df_initial = charger_donnees()

# --- 2. CRÉATION DES DEUX ONGLETS ---
tab1, tab2 = st.tabs(["🔄 Remplacement de Matériau", "📐 Cahier des Charges Strict"])

# --- ONGLET 1 : RECHERCHE PAR SIMILITUDE ---
with tab1:
    st.header("Trouver une alternative plus verte ou moins chère")
    st.write("Sélectionnez le matériau que vous utilisez actuellement pour observer ses propriétés.")
    
    # Menu déroulant de sélection
    liste_materiaux = df_initial['Nom'].tolist()
    materiau_ref = st.selectbox("Sélectionnez le matériau à remplacer :", liste_materiaux)
    
    # Extraction des caractéristiques du matériau choisi
    row_ref = df_initial[df_initial['Nom'] == materiau_ref].iloc[0]
    
    # Affichage dynamique des métriques du matériau de référence
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Densité", f"{row_ref['Densite']} kg/m³")
    col2.metric("Limite Élastique", f"{row_ref['Limite_Elastique_MPa']} MPa")
    col3.metric("Empreinte CO₂", f"{row_ref['Empreinte_CO2']} kgCO2/kg")
    col4.metric("Prix moyen", f"{row_ref['Prix_euro_kg']} €/kg")
    
    st.subheader("Visualisation de l'ensemble de votre base de données")
    colonnes_affichage = ['Nom', 'Densite', 'Module_Young_GPa', 'Limite_Elastique_MPa', 'Empreinte_CO2', 'Prix_euro_kg']
    st.dataframe(df_initial[colonnes_affichage], use_container_width=True)

# --- ONGLET 2 : FILTRAGE STRICT (CAHIER DES CHARGES) ---
with tab2:
    st.header("Filtrer par critères techniques et environnementaux")
    st.write("Définissez des seuils maximums et minimums pour isoler les meilleurs candidats.")
    
    # Alignement des curseurs de réglage (Sliders) sur 2 colonnes
    c1, c2 = st.columns(2)
    with c1:
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
        empreinte_co2_max = st.slider(
            "Empreinte CO₂ Maximum (kgCO2/kg)", 
            float(df_initial['Empreinte_CO2'].min()), 
            float(df_initial['Empreinte_CO2'].max()), 
            float(df_initial['Empreinte_CO2'].max())
        )
        prix_max = st.slider(
            "Prix Maximum (€/kg)", 
            float(df_initial['Prix_euro_kg'].min()), 
            float(df_initial['Prix_euro_kg'].max()), 
            float(df_initial['Prix_euro_kg'].max())
        )
        
    # Application simultanée de tous les filtres mécaniques et écologiques
    df_filtre = df_initial[
        (df_initial['Limite_Elastique_MPa'] >= limite_elastique_min) &
        (df_initial['Module_Young_GPa'] >= module_young_min) &
        (df_initial['Empreinte_CO2'] <= empreinte_co2_max) &
        (df_initial['Prix_euro_kg'] <= prix_max)
    ]
    
    st.subheader(f"📊 {len(df_filtre)} matériau(x) valide(s) trouvé(s)")
    
    if not df_filtre.empty:
        # Affichage du tableau filtré
        st.dataframe(df_filtre[colonnes_affichage], use_container_width=True)
        
        # Graphique de performance d'Ashby automatisé
        st.write("### 📈 Graphique de compromis : Résistance Mécanique vs Empreinte CO₂")
        st.scatter_chart(
            df_filtre,
            x='Empreinte_CO2',
            y='Limite_Elastique_MPa',
            color='Nom'
        )
    else:
        st.warning("Aucun matériau ne correspond à l'ensemble de ces critères. Essayez d'assouplir vos contraintes.")