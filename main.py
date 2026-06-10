import streamlit as st
import pandas as pd

st.title("🌱 Outil d'Éco-Conception Métallurgique")
st.write("Trouvez le matériau idéal pour votre cahier des charges.")

# --- CHARGEMENT ET NETTOYAGE DES DONNÉES ---
@st.cache_data
def charger_donnees():
    # Remplacement des valeurs 0 pour éviter les divisions par zéro
    df = pd.read_csv('alliages_metalliques_3.csv', sep=';') 
    df['Empreinte_Carbone_kgCO2_kg'] = df['Empreinte_Carbone_kgCO2_kg'].replace(0, 1e-6)
    df['Densite_g_cm3'] = df['Densite_g_cm3'].replace(0, 1e-6)
    df['Prix_euro_kg'] = df['Prix_euro_kg'].replace(0, 1e-6)
    return df

df_initial = charger_donnees()

# --- CRÉATION DES DEUX ONGLETS ---
tab1, tab2 = st.tabs(["🔄 Remplacement de Matériau", "📐 Cahier des Charges Strict"])

# ==============================================================================
# ONGLET 1 : RECHERCHE PAR SIMILITUDE / SUBSTITUTION
# ==============================================================================
with tab1:
    st.header("Trouver une alternative plus verte ou moins chère")
    
    # 1. Sélection du matériau à remplacer
    materiau_ref = st.selectbox("Sélectionnez le matériau actuellement utilisé :", df_initial['Nom_Alliage'].unique())
    
    # 2. Récupération de la ligne du matériau de référence
    row_ref = df_initial[df_initial['Nom_Alliage'] == materiau_ref].iloc[0]
    
    st.info(f"**Propriétés de référence ({materiau_ref}) :** \n"
            f"🔹 Résistance : {row_ref['Limite_Elastique_MPa']} MPa | "
            f"🔹 Densité : {row_ref['Densite_g_cm3']} g/cm³  \n"
            f"💰 Prix : {row_ref['Prix_euro_kg']} €/kg | "
            f"🌍 Carbone : {row_ref['Empreinte_Carbone_kgCO2_kg']} kgCO2/kg")

    # 3. Réglage de la tolérance mécanique (ex: accepter des matériaux à +/- 15% de performance)
    tolerance = st.slider("Tolérance sur les propriétés mécaniques (%)", 5, 30, 15) / 100.0

    # 4. Calcul des bornes acceptables
    limite_inf_meca = row_ref['Limite_Elastique_MPa'] * (1 - tolerance)
    limite_sup_densite = row_ref['Densite_g_cm3'] * (1 + tolerance)

    # 5. Extraction et filtrage
    # On cherche des performances mécaniques équivalentes ou meilleures
    alternatives = df_initial[
        (df_initial['Limite_Elastique_MPa'] >= limite_inf_meca) & 
        (df_initial['Densite_g_cm3'] <= limite_sup_densite) &
        (df_initial['Nom_Alliage'] != materiau_ref) # On s'exclut soi-même des résultats
    ].copy()

    # Optionnel : Filtrer uniquement ce qui est strictement MIEUX en prix ou carbone
    seulement_mieux = st.checkbox("Afficher uniquement les matériaux STRICTEMENT moins chers ET plus écologiques", value=True)
    if seulement_mieux:
        alternatives = alternatives[
            (alternatives['Prix_euro_kg'] < row_ref['Prix_euro_kg']) & 
            (alternatives['Empreinte_Carbone_kgCO2_kg'] < row_ref['Empreinte_Carbone_kgCO2_kg'])
        ]

    # 6. Affichage du résultat
    st.subheader(f"🔄 {len(alternatives)} alternatives trouvées")
    if not alternatives.empty:
        st.dataframe(alternatives[['Nom_Alliage', 'Limite_Elastique_MPa', 'Densite_g_cm3', 'Prix_euro_kg', 'Empreinte_Carbone_kgCO2_kg']])
    else:
        st.warning("Aucune alternative stricte trouvée avec cette tolérance. Essayez d'augmenter la tolérance mécanique.")


# ==============================================================================
# ONGLET 2 : RECHERCHE PAR CAHIER DES CHARGES (CONTRAINTES)
# ==============================================================================
with tab2:
    st.header("Filtrer par contraintes absolues")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ Propriétés Mécaniques")
        meca_min = st.number_input("Limite Élastique minimum (MPa)", value=int(df_initial['Limite_Elastique_MPa'].min()))
        densite_max = st.number_input("Densité maximum (g/cm³)", value=float(df_initial['Densite_g_cm3'].max()))
        
    with col2:
        st.subheader("💰 & 🌱 Impact & Coût")
        prix_max = st.number_input("Prix maximum (€/kg)", value=float(df_initial['Prix_euro_kg'].max()))
        carbone_max = st.number_input("Empreinte Carbone max (kgCO2/kg)", value=float(df_initial['Empreinte_Carbone_kgCO2_kg'].max()))

    # Filtrage strict basé sur les entrées utilisateurs
    df_filtre = df_initial[
        (df_initial['Limite_Elastique_MPa'] >= meca_min) &
        (df_initial['Densite_g_cm3'] <= densite_max) &
        (df_initial['Prix_euro_kg'] <= prix_max) &
        (df_initial['Empreinte_Carbone_kgCO2_kg'] <= carbone_max)
    ]

    # Affichage du résultat trié par le prix le plus bas (par exemple)
    st.subheader(f"📐 {len(df_filtre)} matériaux respectent votre cahier des charges")
    if not df_filtre.empty:
        st.dataframe(df_filtre.sort_values(by='Prix_euro_kg'))
    else:
        st.error("Aucun matériau ne respecte toutes ces contraintes en même temps. Ajustez vos critères.")