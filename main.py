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
    df = pd.read_csv('alliages_metalliques_4.csv', sep=';')
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

colonnes_affichage = [
    'Nom', 'Densite', 'Module_Young_GPa', 'Limite_Elastique_MPa', 
    'Temp_Fusion_C', 'Conductivite_Thermique_W_mK', 
    'Empreinte_CO2', 'Recyclabilite_pct', 'Prix_euro_kg'
]

# --- 2. CRÉATION DES DEUX ONGLETS ---
tab1, tab2 = st.tabs(["🔄 Remplacement de Matériau", "📐 Cahier des Charges Strict"])

# --- ONGLET 1 : RECHERCHE PAR SIMILITUDE + SUGGESTION ---
with tab1:
    st.header("Trouver une alternative plus verte ou moins chère")
    
    # Séparation en deux colonnes : Sélection à gauche, Paramètres de suggestion à droite
    col_sel, col_param = st.columns([1, 1])
    
    with col_sel:
        liste_materiaux = df_initial['Nom'].tolist()
        materiau_ref = st.selectbox("Sélectionnez le matériau actuel à remplacer :", liste_materiaux)
        row_ref = df_initial[df_initial['Nom'] == materiau_ref].iloc[0]
        
    with col_param:
        objectif = st.radio(
            "Quel est votre objectif prioritaire pour l'alternative ?",
            ["Réduire l'empreinte CO₂", "Réduire le prix (€/kg)"]
        )
    
    # Affichage des métriques du matériau de référence
    st.markdown(f"#### 📊 Propriétés actuelles de l'alliage : **{materiau_ref}**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Limite Élastique", f"{row_ref['Limite_Elastique_MPa']} MPa")
    c2.metric("Temp. de Fusion", f"{row_ref['Temp_Fusion_C']} °C")
    c3.metric("Empreinte CO₂", f"{row_ref['Empreinte_CO2']} kg/kg")
    c4.metric("Prix", f"{row_ref['Prix_euro_kg']} €/kg")
    
    st.write("---")
    
    # MOTEUR DE SUGGESTION INTERACTIF
    
    st.subheader("💡 Assistant de Substitution Intelligent")
    st.write("Cochez les paramètres techniques que le remplaçant doit impérativement conserver de manière similaire (à ± 20%) :")
    
    c_check1, c_check2, c_check3 = st.columns(3)
    with c_check1:
        keep_mecha = st.checkbox("Conserver la résistance mécanique (Limite élastique)", value=True)
    with c_check2:
        keep_thermal = st.checkbox("Conserver la tenue thermique (Température de fusion)")
    with c_check3:
        keep_stiff = st.checkbox("Conserver la rigidité (Module de Young)")

    # Algorithme de filtrage des alternatives
    df_alt = df_initial[df_initial['Nom'] != materiau_ref].copy()
    tolerance = 0.20
    
    if keep_mecha:
        df_alt = df_alt[df_alt['Limite_Elastique_MPa'] >= row_ref['Limite_Elastique_MPa'] * (1 - tolerance)]
    if keep_thermal:
        df_alt = df_alt[df_alt['Temp_Fusion_C'] >= row_ref['Temp_Fusion_C'] * (1 - tolerance)]
    if keep_stiff:
        df_alt = df_alt[df_alt['Module_Young_GPa'] >= row_ref['Module_Young_GPa'] * (1 - tolerance)]
        
    # Tri et sélection selon l'objectif de gain
    if objectif == "Réduire l'empreinte CO₂":
        df_alt = df_alt[df_alt['Empreinte_CO2'] < row_ref['Empreinte_CO2']]
        df_alt = df_alt.sort_values(by='Empreinte_CO2', ascending=True)
    else:
        df_alt = df_alt[df_alt['Prix_euro_kg'] < row_ref['Prix_euro_kg']]
        df_alt = df_alt.sort_values(by='Prix_euro_kg', ascending=True)

    # Affichage du résultat de la suggestion
    if not df_alt.empty:
        meilleur_choix = df_alt.iloc[0]
        st.success(f"### 🎉 Alternative idéale trouvée : **{meilleur_choix['Nom']}**")
        
        # Comparaison visuelle des gains
        col_gain1, col_gain2 = st.columns(2)
        if objectif == "Réduire l'empreinte CO₂":
            gain_co2 = ((row_ref['Empreinte_CO2'] - meilleur_choix['Empreinte_CO2']) / row_ref['Empreinte_CO2']) * 100
            col_gain1.metric("Nouvelle Empreinte CO₂", f"{meilleur_choix['Empreinte_CO2']} kg/kg", f"-{gain_co2:.1f}% CO₂", delta_color="inverse")
            col_gain2.metric("Prix associé", f"{meilleur_choix['Prix_euro_kg']} €/kg")
        else:
            gain_prix = ((row_ref['Prix_euro_kg'] - meilleur_choix['Prix_euro_kg']) / row_ref['Prix_euro_kg']) * 100
            col_gain1.metric("Nouveau Prix", f"{meilleur_choix['Prix_euro_kg']} €/kg", f"-{gain_prix:.1f}% cher", delta_color="inverse")
            col_gain2.metric("Empreinte CO₂ associée", f"{meilleur_choix['Empreinte_CO2']} kg/kg")
            
        st.write("**Autres alternatives viables trouvées pour ces critères :**")
        st.dataframe(df_alt[colonnes_affichage], use_container_width=True)
    else:
        st.info("Aucun autre alliage de la base de données ne permet d'améliorer ce critère tout en respectant vos contraintes techniques. Essayez de décocher une contrainte.")

    st.write("---")
    st.subheader("📋 Base complète pour référence")
    st.dataframe(df_initial[colonnes_affichage], use_container_width=True)

# --- ONGLET 2 : FILTRAGE STRICT (CAHIER DES CHARGES) ---
with tab2:
    st.header("Filtrer par critères techniques, thermiques et environnementaux")
    st.write("Définissez vos seuils pour isoler les meilleurs candidats pour votre application.")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### ⚙️ Propriétés Mécaniques")
        limite_elastique_min = st.slider("Limite Élastique Minimum (MPa)", int(df_initial['Limite_Elastique_MPa'].min()), int(df_initial['Limite_Elastique_MPa'].max()), int(df_initial['Limite_Elastique_MPa'].min()))
        module_young_min = st.slider("Module de Young Minimum (GPa)", int(df_initial['Module_Young_GPa'].min()), int(df_initial['Module_Young_GPa'].max()), int(df_initial['Module_Young_GPa'].min()))
    with c2:
        st.markdown("### 🌡️ Propriétés Thermiques")
        temp_fusion_min = st.slider("Température de Fusion Minimum (°C)", int(df_initial['Temp_Fusion_C'].min()), int(df_initial['Temp_Fusion_C'].max()), int(df_initial['Temp_Fusion_C'].min()))
        conductivite_min = st.slider("Conductivité Thermique Minimum (W/m·K)", int(df_initial['Conductivite_Thermique_W_mK'].min()), int(df_initial['Conductivite_Thermique_W_mK'].max()), int(df_initial['Conductivite_Thermique_W_mK'].min()))
    with c3:
        st.markdown("### 🌱 Éco-Conception & Coûts")
        empreinte_co2_max = st.slider("Empreinte CO₂ Maximum (kgCO2/kg)", float(df_initial['Empreinte_CO2'].min()), float(df_initial['Empreinte_CO2'].max()), float(df_initial['Empreinte_CO2'].max()))
        recyclabilite_min = st.slider("Taux de Recyclabilité Minimum (%)", int(df_initial['Recyclabilite_pct'].min()), int(df_initial['Recyclabilite_pct'].max()), int(df_initial['Recyclabilite_pct'].min()))
        prix_max = st.slider("Prix Maximum (€/kg)", float(df_initial['Prix_euro_kg'].min()), float(df_initial['Prix_euro_kg'].max()), float(df_initial['Prix_euro_kg'].max()))
        
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
        st.dataframe(df_filtre[colonnes_affichage], use_container_width=True)
        st.write("### 📈 Graphique de compromis : Résistance Mécanique vs Empreinte CO₂")
        st.scatter_chart(df_filtre, x='Empreinte_CO2', y='Limite_Elastique_MPa', color='Nom')
    else:
        st.warning("Aucun alliage ne correspond à l'ensemble de vos contraintes strictes. Essayez d'assouplir certains curseurs.")